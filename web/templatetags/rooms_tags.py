from django import template

from padword.commons import show_exc
from web.models import Room, LockGroup

register = template.Library()

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

