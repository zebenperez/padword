from django.test import SimpleTestCase, override_settings

from guest.models import Guest
from web.models import Project, Room


class _KeyCodes:
    def __init__(self, keycodes):
        self.keycodes = keycodes

    def filter(self, **kwargs):
        locks = kwargs["lock__in"]
        return [keycode for keycode in self.keycodes if keycode.lock in locks]


class _Lock:
    def __init__(self, lock_id, alias):
        self.id = lock_id
        self.alias = alias
        self.room = ""
        self.uuid = "lock-{}".format(lock_id)


class _KeyCode:
    def __init__(self, lock, code):
        self.lock = lock
        self.lock_id = lock.id
        self.code = code


class KeycodesStatusTests(SimpleTestCase):
    def status_for(self, codes):
        first_lock = _Lock(1, "Habitación")
        second_lock = _Lock(2, "Entrada")
        locks = [first_lock, second_lock]
        guest = type("GuestWithLocks", (), {
            "get_locks": lambda self: locks,
            "keycodes": _KeyCodes([
                _KeyCode(first_lock, codes[0]),
                _KeyCode(second_lock, codes[1]),
            ]),
        })()
        return Guest.keycodes_status.fget(guest)

    def test_is_complete_only_when_every_lock_has_a_code(self):
        status = self.status_for(("1234", "1234"))

        self.assertEqual(status["status"], "complete")
        self.assertEqual(status["css_class"], "text-success")
        self.assertEqual(status["tooltip"], "Code: 1234")
        self.assertFalse(status["has_empty_code"])

    def test_is_partial_when_one_lock_is_missing_a_code(self):
        status = self.status_for(("1234", ""))

        self.assertEqual(status["status"], "partial")
        self.assertEqual(status["css_class"], "text-orange")
        self.assertEqual(status["tooltip"], "")
        self.assertTrue(status["has_empty_code"])

    def test_is_empty_when_no_lock_has_a_code(self):
        status = self.status_for(("", ""))

        self.assertEqual(status["status"], "empty")
        self.assertEqual(status["css_class"], "text-danger")
        self.assertEqual(status["tooltip"], "")
        self.assertTrue(status["has_empty_code"])


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
