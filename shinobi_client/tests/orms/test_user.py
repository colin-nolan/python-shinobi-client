import unittest
from typing import Dict

from shinobi_client.orms.user import ShinobiUserOrm
from shinobi_client.shinobi import Shinobi
from shinobi_client.tests._common import _create_email_and_password, TestWithShinobi


class TestShinobiUserOrm(TestWithShinobi):
    def setUp(self):
        super().setUp()
        self.user_orm = ShinobiUserOrm(
            Shinobi(host=self._shinobi.host, port=int(self._shinobi.port),
                    super_user_token=self._shinobi.super_user_token),
        )

    def test_create(self):
        email, password = _create_email_and_password()
        self.user_orm.create(email, password)
        user = self.user_orm.get(email)
        self.assertEqual(email, user["mail"])

    def test_create_and_verify(self):
        email, password = _create_email_and_password()
        self.user_orm.create(email, password, verify_create=True)
        user = self.user_orm.get(email)
        self.assertEqual(email, user["mail"])

    def test_get(self):
        user = self._create_user()
        retrieved_user = self.user_orm.get(user["email"])
        self.assertEqual(user["mail"], retrieved_user["mail"])

    def test_get_when_does_not_exist(self):
        user = self.user_orm.get("example@doesnotexist.com")
        self.assertIsNone(user)

    def test_get_all(self):
        emails = []
        for i in range(3):
            emails.append(self._create_user()["mail"])

        matched_users = tuple(filter(lambda user: user["mail"] in emails, self.user_orm.get_all()))
        self.assertEqual(len(emails), len(matched_users))

    def test_modify(self):
        user = self._create_user()
        _, password = _create_email_and_password()
        assert user["pass"] != password
        changed = self.user_orm.modify(user["email"], password=password)
        self.assertTrue(changed is None or changed is True)

    def test_modify_when_user_not_exist(self):
        email, password = _create_email_and_password()
        self.assertRaises(ValueError, self.user_orm.modify, email, password=password)

    def test_delete(self):
        user = self._create_user()
        self.user_orm.delete(user["email"])
        self.assertIsNone(self.user_orm.get(user["email"]))

    def test_delete_and_verify(self):
        user = self._create_user()
        self.user_orm.delete(user["email"], verify_delete=True)
        self.assertIsNone(self.user_orm.get(user["email"]))

    def test_delete_when_user_not_exist(self):
        email, _ = _create_email_and_password()
        self.assertFalse(self.user_orm.delete(email))

    def _create_user(self) -> Dict:
        """
        Creates a user.
        :return: model of the created user
        """
        email, password = _create_email_and_password()
        return self.user_orm.create(email, password)


if __name__ == "__main__":
    unittest.main()
