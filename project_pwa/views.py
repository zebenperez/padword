from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from guest.models import Guest
from padword.decorators import group_required
from web.models import Project

from .models import ProjectPWA


DEFAULT_CONFIG = {
    'header_bg': '#111827',
    'header_border': '#1e40af',
    'menu_color': '#ffffff',
    'header_size': 24,
    'room_color': '#111827',
    'room_size': 28,
    'button_border': '#d1d5db',
    'button_bg': '#ffffff',
    'lock_text': '#111827',
    'lock_size': 18,
    'footer_border': '#e5e7eb',
    'footer_color': '#6b7280',
    'footer_size': 14,
    'footer_bg': '#ffffff',
    'login_logo_size': 65,
}


def _get_pwa(project_uuid, pwa_uuid):
    return get_object_or_404(
        ProjectPWA,
        uuid=pwa_uuid,
        project_uuid=project_uuid,
    )


def _get_config(pwa):
    saved_config = pwa.config or {}
    config = {**DEFAULT_CONFIG, **saved_config}
    # Keep drafts saved before ``footer_color`` was introduced working.
    if 'footer_color' not in saved_config and 'footer_text' in saved_config:
        config['footer_color'] = saved_config['footer_text']
    return config


def _get_content(pwa):
    return {
        'room_title': '',
        'footer_text': '',
        'login_title': 'Bienvenid@ a {}'.format(pwa.name),
        'login_subtitle': 'Introduce tus datos de acceso.',
        **(pwa.content or {}),
    }


def _save_wizard_data(request, pwa):
    config = _get_config(pwa)
    for key in DEFAULT_CONFIG:
        value = request.POST.get(key)
        if value is not None:
            if key.endswith('_size'):
                try:
                    config[key] = int(value)
                except (TypeError, ValueError):
                    continue
            else:
                config[key] = value

    if 'name' in request.POST:
        pwa.name = request.POST.get('name', pwa.name).strip() or pwa.name
    pwa.config = config
    content = pwa.content.copy() if pwa.content else {}
    for key in ('room_title', 'footer_text', 'login_title', 'login_subtitle'):
        if key in request.POST:
            content[key] = request.POST[key]
    pwa.content = content
    if request.FILES.get('logo'):
        pwa.logo = request.FILES['logo']
    if request.FILES.get('background'):
        pwa.background = request.FILES['background']
    if request.FILES.get('app_background'):
        pwa.app_background = request.FILES['app_background']
    pwa.save()


def _guest_session_key(pwa):
    return 'project_pwa_guest_{}'.format(pwa.uuid)


def _language_session_key(pwa):
    return 'project_pwa_language_{}'.format(pwa.uuid)


def _logged_out_session_key(pwa):
    """Keep a legacy guest login from silently reopening this PWA."""
    return 'project_pwa_logged_out_{}'.format(pwa.uuid)


def _get_languages(pwa):
    project = Project.objects.filter(uuid=pwa.project_uuid).first()
    languages = [language.lower() for language in project.get_languages] if project else []
    return languages or ['es', 'en', 'de']


def _get_language(request, pwa, guest=None):
    languages = _get_languages(pwa)
    language = request.session.get(_language_session_key(pwa))
    if language not in languages and guest and guest.language:
        language = guest.language.lower()
    return language if language in languages else languages[0]


def _guest_is_valid_for_pwa(guest, pwa):
    try:
        return (
            guest is not None
            and guest.project_id == pwa.project_uuid
            and guest.deleted == 0
            and guest.have_valid_booking()
        )
    except Exception:
        return False


def _grant_guest_pwa_access(request, pwa, guest, language=None):
    """Store a validated guest in the PWA session."""
    request.session.cycle_key()
    request.session[_guest_session_key(pwa)] = guest.UUID
    request.session.pop(_logged_out_session_key(pwa), None)
    if language in _get_languages(pwa):
        request.session[_language_session_key(pwa)] = language
        guest.language = language
        guest.save(update_fields=['language'])


def _current_guest(request, pwa):
    guest_uuid = request.session.get(_guest_session_key(pwa))
    if guest_uuid:
        guest = Guest.objects.filter(UUID=guest_uuid, project_id=pwa.project_uuid).first()
        if _guest_is_valid_for_pwa(guest, pwa):
            return guest
        request.session.pop(_guest_session_key(pwa), None)

    # A PWA logout must win over the legacy-access fallback below.  Otherwise
    # visiting the public URL immediately logs the same guest back in.
    if request.session.get(_logged_out_session_key(pwa)):
        return None

    # A guest already authenticated through the legacy access flow can enter
    # the new PWA without having to provide the PIN a second time.
    if request.user.is_authenticated:
        from bookings.models import GuestUser

        guest_user = GuestUser.objects.filter(
            username=request.user.username,
            project_uuid=pwa.project_uuid,
        ).order_by('-id').first()
        if guest_user:
            guest = Guest.objects.filter(UUID=guest_user.guest_uuid, project_id=pwa.project_uuid).first()
            if _guest_is_valid_for_pwa(guest, pwa):
                request.session[_guest_session_key(pwa)] = guest.UUID
                return guest
    return None


def _published_pwa(pwa_uuid):
    return get_object_or_404(ProjectPWA, uuid=pwa_uuid, status=ProjectPWA.Status.PUBLISHED)


def _guest_pwa_data(guest):
    try:
        room = guest.room_obj
        room_name = room.alias if room and room.alias else guest.room
        locks = [
            {'id': lock.id, 'name': lock.alias or lock.room}
            for lock in guest.get_locks
        ]
        return {'room_name': room_name, 'locks': locks}
    except Exception:
        return {'room_name': guest.room, 'locks': []}


@group_required('admins')
def list(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    return render(request, 'project_pwa/list.html', {
        'project': project,
        'pwas': ProjectPWA.objects.filter(project_uuid=project.uuid),
    })


@group_required('admins')
def create(request, project_uuid):
    project = get_object_or_404(Project, uuid=project_uuid)
    pwa = ProjectPWA.objects.create(project_uuid=project.uuid, name=project.name, config=DEFAULT_CONFIG)
    return redirect('project-pwa-edit', project_uuid=project.uuid, pwa_uuid=pwa.uuid)


@group_required('admins')
def edit(request, project_uuid, pwa_uuid):
    pwa = _get_pwa(project_uuid, pwa_uuid)
    step = request.GET.get('step', request.POST.get('step', 'login'))
    if step not in ('login', 'app'):
        step = 'login'
    if request.method == 'POST':
        _save_wizard_data(request, pwa)
        messages.success(request, 'PWA saved.')
        return redirect('{}?step={}'.format(
            reverse('project-pwa-edit', kwargs={'project_uuid': project_uuid, 'pwa_uuid': pwa.uuid}),
            step,
        ))
    return render(request, 'project_pwa/wizard.html', {
        'pwa': pwa,
        'config': _get_config(pwa),
        'content': _get_content(pwa),
        'step': step,
    })


@require_POST
@group_required('admins')
def publish(request, project_uuid, pwa_uuid):
    pwa = _get_pwa(project_uuid, pwa_uuid)
    _save_wizard_data(request, pwa)
    pwa.status = ProjectPWA.Status.PUBLISHED
    pwa.published_at = timezone.now()
    pwa.save(update_fields=['status', 'published_at', 'updated_at'])
    messages.success(request, 'PWA published.')
    step = request.POST.get('step', 'login')
    return redirect('{}?step={}'.format(
        reverse('project-pwa-edit', kwargs={'project_uuid': project_uuid, 'pwa_uuid': pwa.uuid}),
        step if step in ('login', 'app') else 'login',
    ))


@require_POST
@group_required('admins')
def unpublish(request, project_uuid, pwa_uuid):
    pwa = _get_pwa(project_uuid, pwa_uuid)
    pwa.status = ProjectPWA.Status.DRAFT
    pwa.published_at = None
    pwa.save(update_fields=['status', 'published_at', 'updated_at'])
    messages.success(request, 'PWA unpublished.')
    return redirect('project-pwa-edit', project_uuid=project_uuid, pwa_uuid=pwa.uuid)


@group_required('admins')
def delete(request, project_uuid, pwa_uuid):
    pwa = _get_pwa(project_uuid, pwa_uuid)
    if request.method != 'POST':
        return render(request, 'project_pwa/delete_confirm.html', {
            'pwa': pwa,
            'project_uuid': project_uuid,
        })

    # FileField.delete() removes the storage objects without saving the model;
    # retain them here so deleting the database row does not leave uploads behind.
    logo = pwa.logo
    background = pwa.background
    app_background = pwa.app_background
    pwa.delete()
    if logo:
        logo.delete(save=False)
    if background:
        background.delete(save=False)
    if app_background:
        app_background.delete(save=False)
    messages.success(request, 'PWA deleted.')
    return redirect('project-pwa-list', project_uuid=project_uuid)


def public(request, pwa_uuid):
    pwa = _published_pwa(pwa_uuid)
    guest = _current_guest(request, pwa)
    return render(request, 'project_pwa/public.html', {
        'pwa': pwa,
        'config': _get_config(pwa),
        'guest': guest,
        'languages': _get_languages(pwa),
        'language': _get_language(request, pwa, guest),
        'content': _get_content(pwa),
        'guest_data': _guest_pwa_data(guest) if guest else None,
    })


@require_POST
def access(request, pwa_uuid):
    pwa = _published_pwa(pwa_uuid)
    code = request.POST.get('code', '').strip()
    room = request.POST.get('room', '').strip()
    language = request.POST.get('language', '').lower()
    guest = Guest.check_valid_booking(pwa.project_uuid, code, room) if code and room else None

    if not _guest_is_valid_for_pwa(guest, pwa):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'ok': False,
                'error': 'Los datos no son válidos o no tienes una reserva activa.',
            }, status=401)
        return render(request, 'project_pwa/public.html', {
            'pwa': pwa,
            'config': _get_config(pwa),
            'guest': None,
            'languages': _get_languages(pwa),
            'language': language if language in _get_languages(pwa) else _get_languages(pwa)[0],
            'content': _get_content(pwa),
            'error': 'Los datos no son válidos o no tienes una reserva activa.',
        }, status=401)

    _grant_guest_pwa_access(request, pwa, guest, language)
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'ok': True,
            'app_url': reverse('project-pwa-app', kwargs={'pwa_uuid': pwa.uuid}),
            'guest_data': _guest_pwa_data(guest),
        })
    return redirect('project-pwa-app', pwa_uuid=pwa.uuid)


def access_auto(request, pwa_uuid, guest_uuid):
    """Open a PWA directly from a guest-specific booking link."""
    pwa = _published_pwa(pwa_uuid)
    guest = Guest.objects.filter(UUID=guest_uuid, project_id=pwa.project_uuid).first()

    # The URL itself is the credential, but it is only valid while the guest's
    # booking is active and for the PWA's own project.
    if not _guest_is_valid_for_pwa(guest, pwa):
        return render(request, 'project_pwa/public.html', {
            'pwa': pwa,
            'config': _get_config(pwa),
            'guest': None,
            'languages': _get_languages(pwa),
            'language': _get_language(request, pwa),
            'content': _get_content(pwa),
            'error': 'El enlace no es válido o la reserva ya no está activa.',
        }, status=403)

    languages = _get_languages(pwa)
    language = (guest.language or '').lower()
    _grant_guest_pwa_access(request, pwa, guest, language if language in languages else languages[0])
    return redirect('project-pwa-app', pwa_uuid=pwa.uuid)


@require_POST
def logout(request, pwa_uuid):
    pwa = _published_pwa(pwa_uuid)
    request.session.pop(_guest_session_key(pwa), None)
    request.session.pop(_language_session_key(pwa), None)
    request.session[_logged_out_session_key(pwa)] = True
    return redirect('project-pwa-public', pwa_uuid=pwa.uuid)


def app(request, pwa_uuid):
    pwa = _published_pwa(pwa_uuid)
    guest = _current_guest(request, pwa)
    if guest is None:
        return redirect('project-pwa-public', pwa_uuid=pwa.uuid)
    return render(request, 'project_pwa/app.html', {
        'pwa': pwa,
        'config': _get_config(pwa),
        'content': _get_content(pwa),
        'guest': guest,
        'language': _get_language(request, pwa, guest),
        'guest_data': _guest_pwa_data(guest),
    })


def manifest(request, pwa_uuid):
    pwa = _published_pwa(pwa_uuid)
    config = _get_config(pwa)
    data = {
        'name': pwa.name,
        'short_name': pwa.name[:32],
        'start_url': reverse('project-pwa-public', kwargs={'pwa_uuid': pwa.uuid}),
        'display': 'standalone',
        'background_color': '#ffffff',
        'theme_color': config['header_bg'],
    }
    if pwa.logo:
        data['icons'] = [{'src': pwa.logo.url, 'sizes': 'any', 'type': 'image/png'}]
    return JsonResponse(data)


def service_worker(request, pwa_uuid):
    _published_pwa(pwa_uuid)
    response = HttpResponse(
        "self.addEventListener('install', event => self.skipWaiting());\n"
        "self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));\n",
        content_type='application/javascript',
    )
    response['Service-Worker-Allowed'] = '/pwa/{}/'.format(pwa_uuid)
    return response
