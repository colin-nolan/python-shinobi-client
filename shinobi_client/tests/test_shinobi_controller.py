import unittest

import requests

from shinobi_client.shinobi_controller import ShinobiController, start_shinobi


class TestShinobiController(unittest.TestCase):
    """
    Tests for `ShinobiController`.
    """
    def setUp(self):
        self._shinobi_controller = ShinobiController()

    def tearDown(self):
        self._shinobi_controller.stop()

    def test_start(self):
        shinobi = self._shinobi_controller.start()
        home_page_request = requests.get(shinobi.url)
        self.assertTrue(home_page_request.ok)

    def test_stop(self):
        shinobi = self._shinobi_controller.start()
        self._shinobi_controller.stop()
        self.assertRaises(requests.exceptions.ConnectionError, requests.get, shinobi.url)

    def test_stop_when_not_started(self):
        self._shinobi_controller.stop()


class TestStartShinobi(unittest.TestCase):
    """
    Tests for `start_shinobi`.
    """
    def test_use_in_context(self):
        with start_shinobi() as shinobi:
            home_page_request = requests.get(shinobi.url)
            self.assertTrue(home_page_request.ok)


if __name__ == "__main__":
    unittest.main()
