from django.test import SimpleTestCase, override_settings

from guest.models import Guest
from web.models import Project, Room


@override_settings(TIME_ZONE="UTC")
class InHouseDateFormattingTests(SimpleTestCase):
    def test_converts_server_date_to_project_timezone(self):
        project = Project(time_zone_name="Europe/Madrid")

        date = Guest._format_in_house_date("2026-01-15 12:00:00", project)

        self.assertEqual(date, "2026-01-15 13:00:00")

    def test_room_timezone_takes_precedence_over_project_timezone(self):
        project = Project(time_zone_name="Europe/Madrid")
        room = Room(time_zone_name="Atlantic/Canary")

        date = Guest._format_in_house_date("2026-07-15 12:00:00", project, room)

        self.assertEqual(date, "2026-07-15 13:00:00")

# Create your tests here.
