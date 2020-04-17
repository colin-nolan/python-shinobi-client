from asyncio import sleep
from typing import Callable

from requests import Response


class ShinobiSuperUserCredentialsRequiredError(RuntimeError):
    """
    Raised if an operation requires super user credentials that have not been supplied.
    """


def raise_if_errors(shinobi_response: Response, raise_if_json_not_ok: bool = True):
    """
    Raises an exception if the response from Shinobi indicated there were errors.
    :param shinobi_response: the response from Shinobi
    :param raise_if_json_not_ok: raise an exception if Shinobi returns a 2XX but the JSON has `"ok": false`
    """
    shinobi_response.raise_for_status()
    json_response = shinobi_response.json()
    if raise_if_json_not_ok and not json_response["ok"]:
        # Yes, the API returns a 2XX when everything is not ok...
        raise RuntimeError(json_response["msg"])


def wait_and_verify(verifier: Callable[[], bool], *, wait_iterations: int = 10,
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
        if verifier():
            return True
        sleep(iteration_wait_in_milliseconds_multiplier * i)
    return False
