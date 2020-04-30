import string
from asyncio import sleep
from typing import Callable
import random

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
        message = json_response.get("msg", json_response)
        raise RuntimeError(message)


def wait_and_verify(verifier: Callable[[], bool], *, wait_iterations: int = 10,
                    iteration_wait_in_milliseconds_multiplier: int = 100):
    """
    Wait to verify an event has happened.
    :param verifier: callable that returns `True` if the event been waiting upon has been verified
    :param wait_iterations: number of times to try if state not valid
    :param iteration_wait_in_milliseconds_multiplier: waiting for `wait_iterations` * `iteration_wait_in_milliseconds_multiplier`
                                                      between each iteration
    :return: `True` if the event has been verified, else `False`
    """
    for i in range(wait_iterations):
        if verifier():
            return True
        sleep(iteration_wait_in_milliseconds_multiplier * i)
    return False


def generate_random_string(length: int = 8) -> str:
    """
    Generates a short random string.
    :param length: length of generated string
    :return: generated string
    """
    alphabet = string.ascii_lowercase
    return "".join(random.choices(alphabet, k=length))
