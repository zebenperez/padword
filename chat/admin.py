from django.contrib import admin
from chat.models import *
# Register your models here.


class MessageAdmin(admin.ModelAdmin):
	list_display = ('user','room', 'content', 'get_readed_by')
	search_fields = ['content', 'room']
	
	def get_readed_by(self, obj):
		out =""
		for item in obj.readed_by.all():
			out += "%s, "%(item.username)
			
		return out	
	get_readed_by.short_description = "leido"
	

admin.site.register(Message, MessageAdmin)
admin.site.register(Room)
admin.site.register(LastConnection)
admin.site.register(MessageImage)
