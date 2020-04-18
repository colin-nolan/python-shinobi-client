import unittest
from copy import deepcopy

from shinobi_client._common import generate_random_string
from shinobi_client.orms.monitor import ShinobiMonitorOrm, ShinobiMonitorAlreadyExistsError, \
    ShinobiMonitorDoesNotExistError
from shinobi_client.tests._common import TestWithShinobi, _create_email_and_password
from shinobi_client.tests.resources.metadata import get_monitor_configuration

EXAMPLE_MONITOR_1_CONFIGURATION = get_monitor_configuration(1)
EXAMPLE_MONITOR_2_CONFIGURATION = get_monitor_configuration(2)


def _create_monitor_id() -> str:
    """
    Creates random monitor identifier.
    :return: created identifier
    """
    return generate_random_string()


class TestShinobiMonitorOrm(TestWithShinobi):
    """
    Tests for `ShinobiMonitorOrm`.
    """
    def setUp(self):
        super().setUp()
        email, password = _create_email_and_password()
        self._shinobi_client.user.create(email, password)
        self.monitor_orm = ShinobiMonitorOrm(self._superless_shinobi_client, email, password)

    def test_get_when_does_not_exist(self):
        monitor_id = _create_monitor_id()
        self.assertIsNone(self.monitor_orm.get(monitor_id))

    def test_get_all_when_no_monitors(self):
        monitors = self.monitor_orm.get_all()
        self.assertEqual(tuple(), monitors)

    def test_get_all_when_single_monitor(self):
        monitor_id = self._create_monitor()
        monitors = self.monitor_orm.get_all()
        self.assertCountEqual((monitor_id, ), (monitor["mid"] for monitor in monitors))

    def test_get_all_when_multiple_monitors(self):
        monitor_ids = []
        for i in range(3):
            monitor_id = self._create_monitor()
            monitor_ids.append(monitor_id)

        monitors = self.monitor_orm.get_all()
        self.assertCountEqual(monitor_ids, (monitor["mid"] for monitor in monitors))

    def test_create(self):
        monitor_id = _create_monitor_id()
        created_monitor = self.monitor_orm.create(monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)
        self.assertEqual(EXAMPLE_MONITOR_1_CONFIGURATION["host"], created_monitor["host"])
        self.assertEqual(int(EXAMPLE_MONITOR_1_CONFIGURATION["port"]), int(created_monitor["port"]))

        retrieved = self.monitor_orm.get(monitor_id)
        self.assertEqual(monitor_id, retrieved["mid"])
        self.assertEqual(EXAMPLE_MONITOR_1_CONFIGURATION["details"], retrieved["details"])

    def test_create_when_already_exists(self):
        monitor_id = self._create_monitor()
        self.assertRaises(ShinobiMonitorAlreadyExistsError,
                          self.monitor_orm.create, monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)

    def test_create_with_multiple_users(self):
        user_1_orm = self.monitor_orm
        user_2 = self._shinobi_client.user.create(*_create_email_and_password())
        user_2_orm = ShinobiMonitorOrm(self._superless_shinobi_client, user_2["email"], user_2["password"])

        monitor_id = _create_monitor_id()
        user_1_orm.create(monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)

        self.assertEqual(0, len(user_2_orm.get_all()))

    def test_modify_when_not_exist(self):
        monitor_id = _create_monitor_id()
        self.assertRaises(ShinobiMonitorDoesNotExistError,
                          self.monitor_orm.modify, monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)

    def test_modify(self):
        for key in EXAMPLE_MONITOR_1_CONFIGURATION.keys():
            with self.subTest(modified=key):
                monitor_id = _create_monitor_id()
                original_monitor = self.monitor_orm.create(monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)

                new_configuration = deepcopy(EXAMPLE_MONITOR_1_CONFIGURATION)
                new_configuration[key] = EXAMPLE_MONITOR_2_CONFIGURATION[key]
                assert original_monitor[key] != new_configuration[key]

                modified = self.monitor_orm.modify(monitor_id, new_configuration)
                self.assertTrue(modified)

                modified_monitor = self.monitor_orm.get(monitor_id)
                self.assertEqual(new_configuration[key], str(modified_monitor[key]))

                comparable_expected_configuration = filter(
                    lambda item: item[0] != key, ShinobiMonitorOrm.filter_only_supported_keys(
                        new_configuration).items())
                comparable_actual_configuration = map(lambda item: (item[0], str(item[1])), filter(
                    lambda item: item[0] != key, ShinobiMonitorOrm.filter_only_supported_keys(modified_monitor).items()))
                self.assertCountEqual(comparable_expected_configuration, comparable_actual_configuration)

    def test_modify_to_same(self):
        monitor_id = _create_monitor_id()
        self.monitor_orm.create(monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)
        modified = self.monitor_orm.modify(monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)
        self.assertFalse(modified)

    def test_delete_when_not_exists(self):
        monitor_id = _create_monitor_id()
        self.assertFalse(self.monitor_orm.delete(monitor_id))

    def test_delete(self):
        monitor_id = self._create_monitor()
        self.assertTrue(self.monitor_orm.delete(monitor_id))
        self.assertIsNone(self.monitor_orm.get(monitor_id))

    def _create_monitor(self):
        monitor_id = _create_monitor_id()
        self.monitor_orm.create(monitor_id, EXAMPLE_MONITOR_1_CONFIGURATION)
        return monitor_id


if __name__ == "__main__":
    unittest.main()
