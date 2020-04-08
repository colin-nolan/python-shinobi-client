import unittest

from shinobi_client.api_key import ShinobiApiKey, ShinobiWrongPasswordError
from shinobi_client.tests._common import TestWithShinobi


class TestShinobiApiKey(TestWithShinobi):
    """
    Tests for `ShinobiApiKey`.
    """
    def setUp(self):
        super().setUp()
        self.api_key = ShinobiApiKey(self._shinobi_client)

    def test_get_for_non_existent_user(self):
        self.assertRaises(RuntimeError, self.api_key.get, "does_not@exist", "password")

    def test_get_with_wrong_password(self):
        user = self._create_user()
        self.assertRaises(ShinobiWrongPasswordError, self.api_key.get, user["email"], "invalid")

    def test_get_api_key(self):
        user = self._create_user()
        api_key = self.api_key.get(user["email"], user["password"])



if __name__ == "__main__":
    unittest.main()
