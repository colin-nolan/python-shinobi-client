import json
from copy import deepcopy
from typing import Optional, Dict, Tuple
import requests
from requests import Response
from logzero import logger


class ShinobiUserOrm:
    """
    TODO
    """
    SUPPORTED_MODIFIABLE_PROPERTIES = {"password"}

    def __init__(self, host: str, port: int, super_user_token: str):
        """
        TODO
        :param host:
        :param port:
        :param super_user_token:
        """
        self.host = host
        self.port = port
        self.super_user_token = super_user_token

    def get(self, email: str) -> Optional[Dict]:
        """
        TODO
        :param email:
        :return:
        """
        # XXX: For some reason, Shinobi doesn't have an endpoint to query an individual user
        users = self.get_all()
        matched_users = tuple(filter(lambda user: user["mail"] == email, users))
        assert len(matched_users) <= 1, f"More than one user found with the email address: {email}"
        if len(matched_users) == 1:
            return self._create_improved_user_entry(matched_users[0])
        else:
            return None

    def get_all(self) -> Tuple:
        """
        TODO
        :return:
        """
        response = requests.get(
            f"http://{self.host}:{self.port}/super/{self.super_user_token}/accounts/list")
        self._raise_if_errors(response)
        return  tuple(self._create_improved_user_entry(user) for user in response.json()["users"])

    def create(self, email: str, password: str, verify_create: bool = True) -> Dict:
        """
        TODO
        :param email:
        :param password:
        :param verify_create:
        :return:
        """
        # Not trusting Shinobi's API to give back anything useful if the user already exists
        if self.get(email):
            raise ValueError(f"User with email \"{email}\" already exists")

        # The required post does not align with the API documentation (https://shinobi.video/docs/api)
        # Exploiting the undocumented API successfully used by UI.
        # See source: https://gitlab.com/Shinobi-Systems/Shinobi/-/blob/dev/libs/webServerSuperPaths.js
        data = {
            "mail": email,
            "pass": password,
            "password_again": password,
            "details": json.dumps({
                "factorAuth": "0", "size": "", "days": "", "event_days": "", "log_days": "", "max_camera": "",
                "permissions": "all", "edit_size": "1", "edit_days": "1", "edit_event_days": "1",
                "edit_log_days": "1", "use_admin": "1", "use_aws_s3": "1", "use_whcs": "1", "use_sftp": "1",
                "use_webdav": "1", "use_discordbot": "1", "use_ldap": "1", "aws_use_global": "0",
                "b2_use_global": "0", "webdav_use_global": "0"})
        }
        response = requests.post(
            f"http://{self.host}:{self.port}/super/{self.super_user_token}/accounts/registerAdmin",
            json=dict(data=data))
        self._raise_if_errors(response)
        create_user = response.json()

        # This is worth doing as Shinobi's API is all over the place - it happily returns OK for invalid requests
        if verify_create:
            assert self.get(email), "Unable to verify created user"

        return self._create_improved_user_entry(create_user["user"])

    def modify(self, email: str, **kwargs) -> Optional[bool]:
        """
        TODO
        :param email:
        :param kwargs:
        :return:
        """
        unsupported_properties = set(kwargs.keys()) - {"mail"} - self.__class__.SUPPORTED_MODIFIABLE_PROPERTIES
        if len(unsupported_properties) > 0:
            raise NotImplementedError(f"Cannot modify user properties: {unsupported_properties}")

        existing_user = self.get(email)
        if existing_user is None:
            raise ValueError(f"Cannot modify user as they do not exist: {email}")

        data = {
            "mail": email,
            "pass": kwargs["password"],
            "password_again": kwargs["password"],
        }
        account = {
            "mail": email,
            "uid": existing_user["uid"],
            "ke": existing_user["ke"]
        }
        response = requests.post(
            f"http://{self.host}:{self.port}/super/{self.super_user_token}/accounts/editAdmin",
            json=dict(data=data, account=account))
        self._raise_if_errors(response)

        rows_changed = response.json().get("rowsChanged")
        if rows_changed is None:
            logger.info("Shinobi did not return information on whether the user has been changed")
            return None
        return rows_changed == 1

    def delete(self, email: str, verify_delete: bool = True) -> bool:
        """
        TODO
        :param email:
        :param verify_delete:
        :return:
        """
        user = self.get(email)
        if user is None:
            return False

        account = {
            "uid": user["uid"],
            "ke": user["ke"],
            "mail": email
        }

        # Odd interface, defined here:
        # https://gitlab.com/Shinobi-Systems/Shinobi/-/blob/dev/libs/webServerSuperPaths.js#L385
        response = requests.post(
            f"http://{self.host}:{self.port}/super/{self.super_user_token}/accounts/deleteAdmin",
            json=dict(account=account))
        self._raise_if_errors(response)

        if verify_delete:
            assert self.get(email) is None, f"User with email \"{email}\" was not deleted"

        return True

    def _create_improved_user_entry(self, user: Dict) -> Dict:
        """
        TODO
        :param user:
        :return:
        """
        user = deepcopy(user)
        user["email"] = user["mail"]
        return user

    def _raise_if_errors(self, shinobi_response: Response):
        """
        TODO
        :param shinobi_response:
        :return:
        """
        shinobi_response.raise_for_status()
        json_response = shinobi_response.json()
        if not json_response["ok"]:
            # Yes, the API returns a non-400 when everything is not ok...
            raise RuntimeError(json_response["msg"])
