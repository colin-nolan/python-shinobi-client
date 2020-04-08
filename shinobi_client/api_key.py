import requests

from shinobi_client.shinobi import Shinobi
from shinobi_client._common import raise_if_errors


class ShinobiWrongPasswordError(RuntimeError):
    """
    TODO
    """


class ShinobiApiKey:
    """
    TODO
    """
    def __init__(self, shinobi: Shinobi):
        """
        TODO
        :param shinobi:
        """
        self.shinobi = shinobi

    def get(self, email: str, password: str):
        user = self.shinobi.user.get(email)
        if user is None:
            raise RuntimeError(f"No user found with the given email: {email}")

        # API reference: https://shinobi.video/docs/api#content-login-by-api--get-temporary-api-key
        response = requests.post(
            f"http://{self.shinobi.host}:{self.shinobi.port}/?json=true",
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
