from django import template

from padword.commons import show_exc
from web.models import Room
from web.models_lock import LockGroup

register = template.Library()


'''
    Filter
'''
@register.filter
def get_lock_group(room):
    return LockGroup.objects.filter(uuid=room.lock_group_uuid).first()

'''
    Inclusion Tags
'''
@register.inclusion_tag('web/rooms/room-group-list.html')
def room_group_list(project):
    return {'project': project, 'group_list': LockGroup.objects.filter(project_uuid=project.uuid)}

@register.inclusion_tag('web/rooms/rooms-by-group.html')
def room_list(project, group=None):
    if group != None:
        return {'room_list': Room.objects.filter(project_uuid=project.uuid, lock_group_uuid=group.uuid)}
    else:
        return {'room_list': Room.objects.filter(project_uuid=project.uuid, lock_group_uuid="")}

@register.inclusion_tag('web/rooms-by-project/room-group-list.html')
def room_group_list_by_project(project, search_name):
    return {'project': project, 'group_list': LockGroup.objects.filter(project_uuid=project.uuid), 'search_name': search_name}

@register.inclusion_tag('web/rooms-by-project/rooms-by-group.html')
def room_list_by_project(project, search_name="", group=None):
    kwargs = {'project_uuid': project.uuid}
    if group != None:
        kwargs['lock_group_uuid'] = group.uuid
    if search_name != "":
        kwargs['alias__icontains'] = search_name
    return {'room_list': Room.objects.filter(**kwargs), 'search_name': search_name}
    #if group != None:
    #    return {'room_list': Room.objects.filter(project_uuid=project.uuid, lock_group_uuid=group.uuid), 'search_name': search_name}
    #else:
    #    return {'room_list': Room.objects.filter(project_uuid=project.uuid, lock_group_uuid="")}

