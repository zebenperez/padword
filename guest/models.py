from django.db import models
from django.utils.translation import ugettext as _

# Create your models here.

class Guest(models.Model):
    name = models.CharField(max_length=255, verbose_name='Name')
    surname = models.CharField(max_length=255, verbose_name='Surname')
    class Meta:
        managed = False
        db_table = 'guests'
        verbose_name = _('Guest')

