import requests

from shinobi_client.client import ShinobiClient
from shinobi_client._common import raise_if_errors


class ShinobiWrongPasswordError(RuntimeError):
    """
    TODO
    """


class ShinobiApiKey:
    """
    TODO
    """
    def __init__(self, shinobi_client: ShinobiClient):
        """
        Constructor
        :param shinobi_client: client for Shinobi
        """
        self.shinobi_client = shinobi_client

    def get(self, email: str, password: str):
        user = self.shinobi_client.user.get(email)
        if user is None:
            raise RuntimeError(f"No user found with the given email: {email}")

        # API reference: https://shinobi.video/docs/api#content-login-by-api--get-temporary-api-key
        response = requests.post(
            f"http://{self.shinobi_client.host}:{self.shinobi_client.port}/?json=true",
            data={
                "mail": user["mail"],
                "pass": password,
                "ke": user["ke"]
            })
        raise_if_errors(response, raise_if_json_not_ok=False)

        if not response.json()["ok"]:
            # We can only assume this means that the password was incorrect...
            raise ShinobiWrongPasswordError((email, user))

        return response.json()["$user"]["auth_token"]
