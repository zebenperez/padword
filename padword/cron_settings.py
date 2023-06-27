CRONJOBS = [
    ('10 12 * * *', 'padword.cron.avantio_booking_schedule', [], {'project_uuid': '0fa03300-2646-b206-981b-b078262cacc5'},'>> /var/www/django/padword/cron.log'),
    ('0 */2 * * *', 'padword.cron.avantio_notification_schedule', [], {'project_uuid': '0fa03300-2646-b206-981b-b078262cacc5'}, '>> /var/www/django/padword/cron.log'),
]
