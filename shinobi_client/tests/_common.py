import unittest
from abc import ABCMeta
from typing import Tuple, ClassVar, Dict
from uuid import uuid4

from shinobi_client.shinobi_controller import ShinobiController
from shinobi_client.shinobi import Shinobi


def _create_email_and_password() -> Tuple[str, str]:
    """
    Create email and password.
    :return: email and password tuple
    """
    random_string = str(uuid4())
    return f"{random_string}@example.com", random_string


class TestWithShinobi(unittest.TestCase, metaclass=ABCMeta):
    """
    Superclass for tests that use Shinobi`.

    Shinobi takes a reasonable amount of time to setup so sharing between all tests in class (at the cost of reduced
    test isolation) might make sense.
    """
    _shinobi_controller_singleton: ClassVar[ShinobiController]
    _shinobi_singleton: ClassVar[Shinobi]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._shinobi_controller_singleton = ShinobiController()
        cls._shinobi_singleton = cls._shinobi_controller_singleton.start()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._shinobi_controller_singleton.stop()

    def setUp(self):
        super().setUp()
        self._shinobi: Shinobi = self.__class__._shinobi_singleton

    def _create_user(self) -> Dict:
        """
        Creates a user.
        :return: model of the created user
        """
        email, password = _create_email_and_password()
        return self._shinobi.user.create(email, password)
