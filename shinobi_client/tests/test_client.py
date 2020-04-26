import unittest

from shinobi_client.tests._common import TestWithShinobi, _create_email_and_password


class TestShinobiClient(TestWithShinobi):
    """
    Tests for `ShinobiClient`.
    """
    def test_get_user(self):
        email, password = _create_email_and_password()
        self.shinobi_client.user.create(email, password)
        self.assertIsNotNone(self.shinobi_client.user.get(email))

    def test_get_api_key(self):
        email, password = _create_email_and_password()
        self.shinobi_client.user.create(email, password)
        self.assertIsNotNone(self.shinobi_client.api_key.get(email, password))


if __name__ == "__main__":
    unittest.main()
