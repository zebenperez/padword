import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _


def pwa_logo_path(instance, filename):
    return 'project_pwa/{}/logo/{}'.format(instance.uuid, filename)


def pwa_background_path(instance, filename):
    return 'project_pwa/{}/background/{}'.format(instance.uuid, filename)


def pwa_app_background_path(instance, filename):
    return 'project_pwa/{}/app-background/{}'.format(instance.uuid, filename)


class ProjectPWA(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        PUBLISHED = 'published', _('Published')
        ARCHIVED = 'archived', _('Archived')

    project_uuid = models.CharField(max_length=255, db_index=True, verbose_name=_('Project UUID'))
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=120, verbose_name=_('Name'))
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    logo = models.ImageField(upload_to=pwa_logo_path, blank=True, null=True)
    background = models.ImageField(upload_to=pwa_background_path, blank=True, null=True)
    app_background = models.ImageField(upload_to=pwa_app_background_path, blank=True, null=True)
    config = models.JSONField(default=dict, blank=True)
    content = models.JSONField(default=dict, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = _('Project PWA')
        verbose_name_plural = _('Project PWAs')

    def __str__(self):
        return '{} - {}'.format(self.project_uuid, self.name)
