import unittest
from abc import ABCMeta
from typing import Tuple, ClassVar, Dict

from shinobi_client._common import generate_random_string
from shinobi_client.shinobi_controller import ShinobiController
from shinobi_client.client import ShinobiClient


def _create_email_and_password() -> Tuple[str, str]:
    """
    Create email and password.
    :return: email and password tuple
    """
    random_string = generate_random_string()
    return f"{random_string}@example.com", random_string


class TestWithShinobi(unittest.TestCase, metaclass=ABCMeta):
    """
    Superclass for tests that use Shinobi`.

    Shinobi takes a reasonable amount of time to setup so sharing between all tests in class (at the cost of reduced
    test isolation) might make sense.
    """
    _shinobi_controller_singleton: ClassVar[ShinobiController]
    _shinobi_client_singleton: ClassVar[ShinobiClient]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._shinobi_controller_singleton = ShinobiController()
        cls._shinobi_client_singleton = cls._shinobi_controller_singleton.start()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._shinobi_controller_singleton.stop()

    def setUp(self):
        super().setUp()
        self._shinobi_client: ShinobiClient = self.__class__._shinobi_client_singleton
        self._superless_shinobi_client = ShinobiClient(self._shinobi_client.host, self._shinobi_client.port)

    def _create_user(self) -> Dict:
        """
        Creates a user.
        :return: model of the created user
        """
        email, password = _create_email_and_password()
        return self._shinobi_client.user.create(email, password)
