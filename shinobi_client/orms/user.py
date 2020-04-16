import json
from copy import deepcopy
from dataclasses import dataclass

from time import sleep
from typing import Optional, Dict, Tuple

import requests
from logzero import logger

from shinobi_client import ShinobiClient
from shinobi_client._common import raise_if_errors, ShinobiSuperUserCredentialsRequiredError


@dataclass
class ShinobiWrongPasswordError(ValueError):
    """
    TODO
    """
    email: str
    password: str


@dataclass
class ShinobiUserAlreadyExistsError(ValueError):
    """
    TODO
    """
    email: str


class ShinobiUserOrm:
    """
    Shinobi user ORM.
    """
    SUPPORTED_MODIFIABLE_PROPERTIES = {"password"}

    @staticmethod
    def _create_improved_user_entry(user: Dict) -> Dict:
        """
        Creates a copy of the given user details with extra information.
        :param user: user details to improve
        :return: improved user details
        """
        user = deepcopy(user)
        user["email"] = user["mail"]
        if "pass" in user:
            user["password"] = user["pass"]
        return user

    @property
    def _base_url(self) -> str:
        if self.shinobi_client.super_user_token is None:
            raise ShinobiSuperUserCredentialsRequiredError()
        return f"http://{self.shinobi_client.host}:{self.shinobi_client.port}" \
               f"/super/{self.shinobi_client.super_user_token}/accounts"

    def __init__(self, shinobi_client: ShinobiClient):
        """
        Constructor.
        :param shinobi_client: client connected to Shinobi installation
        """
        self.shinobi_client = shinobi_client

    def get(self, email: str, password: str = None) -> Optional[Dict]:
        """
        Gets details about the user with the given email address.
        :param email: user's email address
        :param password: password of the user - if supplied will get the details as the user opposed to the super user
        :return: details about user else `None` if the user does not exist
        :raises ShinobiWrongPasswordError: raised if an incorrect email/password pair is supplied
        """
        return self._get_as_user(email, password) if password else self._get_as_super_user(email)

    def _get_as_user(self, email: str, password: str) -> Dict:
        """
        Gets details about the user with the given email address, using the user's own credentials.
        :param email: user's email address
        :param password: user's password
        :return: details about user
        :raises ShinobiWrongPasswordError: raised if an incorrect email/password pair is supplied
        """
        response = requests.post(
            f"http://{self.shinobi_client.host}:{self.shinobi_client.port}/?json=true",
            data={
                "mail": email,
                "pass": password
            })
        raise_if_errors(response, raise_if_json_not_ok=False)

        if not response.json()["ok"]:
            # We can only assume this means that the password was incorrect...
            raise ShinobiWrongPasswordError(email, password)

        user = response.json()["$user"]
        user["pass"] = password
        return ShinobiUserOrm._create_improved_user_entry(user)

    def _get_as_super_user(self, email: str) -> Optional[Dict]:
        """
        Gets details about the user with the given email address, using the super user's credentials.
        :param email: user's email address
        :return: details about user else `None` if the user does not exist
        """
        # XXX: For some reason, Shinobi doesn't have an endpoint to query an individual user as superuser
        users = self.get_all()
        matched_users = tuple(filter(lambda user: user["mail"] == email, users))
        assert len(matched_users) <= 1, f"More than one user found with the email address: {email}"
        if len(matched_users) == 0:
            return None
        return ShinobiUserOrm._create_improved_user_entry(matched_users[0])

    def get_all(self) -> Tuple:
        """
        Gets details about all users.
        :return: tuple where each element contains details about a specific user
        """
        response = requests.get(f"{self._base_url}/list")
        raise_if_errors(response)
        return tuple(ShinobiUserOrm._create_improved_user_entry(user) for user in response.json()["users"])

    def create(self, email: str, password: str, verify_create: bool = True) -> Dict:
        """
        Creates a user with the given details.
        :param email: email address of the user
        :param password: password for the user
        :param verify_create: whether to wait to confirm that the user has been created
        :return: details about created user
        """
        # Not trusting Shinobi's API to give back anything useful if the user already exists
        if self.get(email):
            raise ShinobiUserAlreadyExistsError(email)

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
        response = requests.post(f"{self._base_url}/registerAdmin", json=dict(data=data))
        raise_if_errors(response)
        create_user = response.json()

        # This is worth doing as Shinobi's API is all over the place - it happily returns OK for invalid requests
        if verify_create:
            if not self._wait_and_verify(email, True):
                raise RuntimeError("Unable to verify created user")

        return ShinobiUserOrm._create_improved_user_entry(create_user["user"])

    def modify(self, email: str, **kwargs) -> Optional[bool]:
        """
        Modify a user.
        :param email: the email address of the user to modify.
        :param kwargs: new property values (currently supported: `password`).
        :return: whether the user was modified or `None` if not able to confirm
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
        response = requests.post(f"{self._base_url}/editAdmin", json=dict(data=data, account=account))
        raise_if_errors(response)

        rows_changed = response.json().get("rowsChanged")
        if rows_changed is None:
            logger.info("Shinobi did not return information on whether the user has been changed")
            return None
        return rows_changed == 1

    def delete(self, email: str, verify_delete: bool = True) -> bool:
        """
        Deletes the user with the given email address.
        :param email: email address of user
        :param verify_delete: whether to wait to confirm that the user has been deleted
        :return: `True` if the user has been deleted, else `False` if they haven't because they didn't exist
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
        response = requests.post(f"{self._base_url}/deleteAdmin", json=dict(account=account))
        raise_if_errors(response)

        if verify_delete:
            if not self._wait_and_verify(email, False):
                raise RuntimeError(f"User with email \"{email}\" was not deleted")

        return True

    def _wait_and_verify(self, email: str, user_should_exist: bool, *, wait_iterations: int = 10,
                         iteration_wait_in_milliseconds_multiplier: int = 100):
        """
        Wait to verify if the user with the given email address exists (if they should) or doesn't (if they shouldn't).
        :param email: email of user to check
        :param user_should_exist: whether the user should exist
        :param wait_iterations: number of times to try if state not valid
        :param iteration_wait_in_milliseconds_multiplier: waiting for `wait_iterations` * `iteration_wait_in_milliseconds_multiplier`
                                                          between each iteration
        :return: `True` if verified state matches desired, else `False`
        """
        for i in range(wait_iterations):
            user = self.get(email)
            if user and user_should_exist:
                return True
            elif not user and not user_should_exist:
                return True
            sleep(iteration_wait_in_milliseconds_multiplier * i)
        return False
