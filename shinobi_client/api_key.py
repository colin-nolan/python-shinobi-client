from typing import Dict

from shinobi_client.client import ShinobiClient


class ShinobiApiKey:
    """
    API key ORM.

    Not thread safe.
    """
    def __init__(self, shinobi_client: ShinobiClient):
        """
        Constructor
        :param shinobi_client: client for Shinobi
        """
        self.shinobi_client = shinobi_client

    def get(self, email: str, password: str) -> Dict:
        """
        Gets the API key for the user with the given email address and password.
        :param email: user's email address
        :param password: user's password
        :return: the user's API key
        :raises ShinobiWrongPasswordError: raised if an incorrect email/password pair is supplied
        """
        return self.shinobi_client.user.get(email, password)["auth_token"]
