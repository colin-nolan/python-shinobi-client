import unittest

from shinobi_client.tests._common import TestWithShinobi, _create_email_and_password


class TestShinobi(TestWithShinobi):
    """
    Tests for `Shinobi`.
    """
    def setUp(self):
        super().setUp()
        self.shinobi = self._shinobi

    def test_get_user(self):
        email, password = _create_email_and_password()
        self.shinobi.user.create(email, password)
        self.assertIsNotNone(self.shinobi.user.get(email))

    def test_get_api_key(self):
        email, password = _create_email_and_password()
        self.shinobi.user.create(email, password)
        self.assertIsNotNone(self.shinobi.api_key.get(email, password))



if __name__ == "__main__":
    unittest.main()
