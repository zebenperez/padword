from django import template
        
register = template.Library()


'''
    Inclusion Tags
'''
@register.inclusion_tag('web/locks/wifi-level.html')
def get_wifi_icon(gateways):
    gateway_list = []
    try:
        g_list = gateways.split(";")
        for gateway in g_list:
            g = gateway.split("|")
            gateway_list.append({'name': g[0], 'level': int(g[1])})
    except: pass
    return {'gateway_list': gateway_list}
 
@register.inclusion_tag('web/gateways/lock-list.html')
def get_locks_by_gateway(project, gateway_id):
    return {'lock_list': project.gateway_lock_list(gateway_id),}

