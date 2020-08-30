import json
from copy import deepcopy
from dataclasses import dataclass
from json import JSONDecodeError
from typing import Dict, Optional, Set, Tuple, Union

import requests

from shinobi_client.client import ShinobiClient
from shinobi_client._common import raise_if_errors, wait_and_verify


@dataclass
class ShinobiMonitorAlreadyExistsError(ValueError):
    monitor_id: str


@dataclass
class ShinobiMonitorDoesNotExistError(ValueError):
    monitor_id: str


class InvalidConfigurationError(ValueError):
    def __init__(self, error_message: str, configuration: Dict):
        super().__init__(error_message)
        self.error_message = error_message
        self.configuration = configuration


@dataclass
class ShinobiUnsupportedKeysInConfigurationError(InvalidConfigurationError):
    unsupported_keys: Set[str]


class ShinobiMonitorOrm:
    """
    Shinobi monitor ORM.

    Uses API: https://shinobi.video/docs/api#content-add-edit-or-delete-a-monitor

    Not thread safe.
    """
    SUPPORTED_KEYS = {"name", "details", "type", "ext", "protocol", "host", "path", "port", "fps", "mode", "width",
                      "height"}

    @staticmethod
    def filter_only_supported_keys(configuration: Dict) -> Dict:
        """
        Filter the given configuration to only the key/values pairs that can be set.
        :param configuration: configuration to filter (not modified)
        :return: filtered configuration
        """
        return dict(filter(lambda item: item[0] in ShinobiMonitorOrm.SUPPORTED_KEYS, configuration.items()))

    @staticmethod
    def would_configuration_change(configuration: Dict, existing_configuration: Dict) -> bool:
        """
        Determines whether the existing configuration would change if Shinobi is given the new configuration.
        :param configuration: new configuration
        :param existing_configuration: existing configuration
        :return: `True` if the existing configuration would change
        """
        new_keys = set(configuration.keys()) - set(existing_configuration.keys())
        if len(new_keys) > 0:
            return True
        for key, value in configuration.items():
            if key == "details":
                break
            if str(existing_configuration[key]) != str(value):
                return True

        if "details" not in configuration:
            return False

        # Note: details that are missing with either take default values or will not change
        configuration_details = ShinobiMonitorOrm._parse_details(configuration["details"])
        existing_configuration_details = ShinobiMonitorOrm._parse_details(existing_configuration["details"])
        return ShinobiMonitorOrm.would_configuration_change(configuration_details, existing_configuration_details)

    @staticmethod
    def validate_configuration(configuration: Dict):
        """
        Validates that the configuration only contains supported keys.
        :param configuration: the configuration to validate
        :raises InvalidConfigurationError: if the configuration is deemed invalid
        """
        if "name" not in configuration:
            # Shinobi returns `{'ok': False}` (2XX), with no information if the name is omitted
            raise InvalidConfigurationError("\"name\" is not in the configuration", configuration)
        if "details" not in configuration:
            # Shinobi errors if the "details" field is omitted
            raise InvalidConfigurationError(f"\"details\" is not in the configuration", configuration)
        else:
            # "details" must be JSON
            try:
                ShinobiMonitorOrm._parse_details(configuration["details"])
            except (JSONDecodeError, ValueError) as e:
                raise InvalidConfigurationError(
                    "Configuration \"details\" was invalid: {configuration['details']}", configuration) from e

        unsupported_keys = set(configuration.keys()) - ShinobiMonitorOrm.SUPPORTED_KEYS
        if len(unsupported_keys) > 0:
            raise ShinobiUnsupportedKeysInConfigurationError(unsupported_keys)

    @staticmethod
    def _create_improved_monitor_entry(monitor: Dict) -> Dict:
        """
        Creates a copy of the given monitor details with extra information.
        :param monitor: monitor details to improve
        :return: improved monitor details
        """
        monitor = deepcopy(monitor)
        assert "id" not in monitor
        monitor["id"] = monitor["mid"]
        if "ok" in monitor:
            del monitor["ok"]
        # Shinobi UI returns JSON but the API returns a string - parsing JSON string
        monitor["details"] = ShinobiMonitorOrm._parse_details(monitor["details"])
        return monitor

    @staticmethod
    def _parse_details(details: Union[Dict, str]) -> Dict:
        """
        Parses the details out of the given details.
        :param details: representation of configuration details
        :return: parsed details (may not be a copy)
        :raises ValueError: if the parsed details are not a dictionary
        """
        # Note: in older versions of Shinobi the details were stored in a JSON dumped string.
        #       Newer config is in JSON.
        parsed_details = json.loads(details) if isinstance(details, str) else details
        if not isinstance(parsed_details, dict):
            raise ValueError(f"Details is not a valid JSON object: {parsed_details}")
        return parsed_details

    @property
    def base_url(self) -> str:
        return f"http://{self.shinobi_client.host}:{self.shinobi_client.port}/{self.api_key}"

    @property
    def user(self) -> Dict:
        return deepcopy(self._user)

    def __init__(self, shinobi_client: ShinobiClient, email: str, password: str):
        """
        Constructor.
        :param shinobi_client: client connected to Shinobi installation
        :param email: email of user to setup monitors for
        :param password: password of user to setup monitors for
        :raises ShinobiWrongPasswordError: if the email and password given is incorrect
        """
        self.shinobi_client = shinobi_client
        self._user = self.shinobi_client.user.get(email, password)
        self.api_key = self._user["auth_token"]
        self.group_key = self._user["ke"]

    def get(self, monitor_id: str) -> Optional[Dict]:
        """
        Gets the monitor with the given ID.
        :param monitor_id: ID of the monitor to get
        :return: details about the monitor else `None` if not found
        """
        response = requests.get(f"{self.base_url}/monitor/{self.group_key}/{monitor_id}")
        response.raise_for_status()
        content = response.json()
        if not content:
            return None
        return ShinobiMonitorOrm._create_improved_monitor_entry(content)

    def get_all(self) -> Tuple[Dict]:
        """
        Gets details about all monitors.
        :return: monitors
        """
        response = requests.get(f"{self.base_url}/monitor/{self.group_key}")
        response.raise_for_status()
        json_response = response.json()

        # Yes, the type of response weirdly changes depending on the number of monitors currently set...
        if isinstance(json_response, Dict):
            if len(json_response) == 0:
                return tuple()
            else:
                return (ShinobiMonitorOrm._create_improved_monitor_entry(json_response), )
        else:
            return tuple(ShinobiMonitorOrm._create_improved_monitor_entry(entry) for entry in json_response)

    def create(self, monitor_id: str,  configuration: Dict, verify: bool = True) -> Dict:
        """
        Creates a monitor with the given ID and configuration.
        :param monitor_id: ID of monitor
        :param configuration: configuration of monitor
        :param verify: wait and verify that the monitor has been created if `True`
        :return: details about the created monitor
        :raises MonitorAlreadyExistsError: raised if a monitor with the given ID already exists
        """
        if "-" in monitor_id:
            # Shinobi silently removes dashes so just making them illegal
            raise ValueError("\"monitor_id\" cannot contain \"-\"")

        configuration = ShinobiMonitorOrm.filter_only_supported_keys(configuration)
        ShinobiMonitorOrm.validate_configuration(configuration)
        if self.get(monitor_id):
            raise ShinobiMonitorAlreadyExistsError(monitor_id)

        self._configure(monitor_id, configuration)

        retrieved_monitor = None

        def retrieve_monitor():
            nonlocal retrieved_monitor
            retrieved_monitor = self.get(monitor_id)
            return retrieved_monitor is not None

        if verify:
            if not wait_and_verify(retrieve_monitor):
                raise RuntimeError(f"Could not create monitor \"{monitor_id}\" with configuration: ${configuration}")
            assert retrieved_monitor is not None
        else:
            retrieved_monitor = self.get(monitor_id)

        return retrieved_monitor

    def modify(self, monitor_id: str, configuration: Dict, verify: bool = True) -> bool:
        """
        Modified a monitor with the given ID with the given configuration.
        :param monitor_id: ID of the monitor
        :param configuration: updated configuration of the monitor
        :param verify: wait and verify that the monitor has been modified if `True`
        :return: `True` if the monitor has been modified
        :raises ShinobiMonitorDoesNotExistError: raised if a monitor with the given ID does not exist
        """
        configuration = ShinobiMonitorOrm.filter_only_supported_keys(configuration)
        ShinobiMonitorOrm.validate_configuration(configuration)
        current_configuration = self.get(monitor_id)
        if not current_configuration:
            raise ShinobiMonitorDoesNotExistError(monitor_id)

        if not ShinobiMonitorOrm.would_configuration_change(configuration, current_configuration):
            return False

        self._configure(monitor_id, configuration)

        if verify and not wait_and_verify(lambda: not ShinobiMonitorOrm.would_configuration_change(
                configuration, self.get(monitor_id))):
            raise RuntimeError(f"Could not change configuration of monitor \"{monitor_id}\". "
                               f"Got {self.get(monitor_id)} expected {configuration}")

        return True

    def delete(self, monitor_id: str, verify: bool = True) -> bool:
        """
        Deletes the monitor with the given ID.

        NoOp if the monitor does not exist.
        :param monitor_id: ID of the monitor
        :param verify: wait and verify that the monitor has been deleted if `True`
        :return: `True` if the monitor was deleted
        """
        # Note: if we don"t do this check, Shinobi errors (and the connection hangs) if asked to remove a non-existent
        #       monitor
        if not self.get(monitor_id):
            return False

        response = requests.post(f"{self.base_url}/configureMonitor/{self.group_key}/{monitor_id}/delete")
        raise_if_errors(response)
        if verify and not wait_and_verify(lambda: self.get(monitor_id) is None):
            raise RuntimeError(f"Could not delete monitor: {monitor_id}")

        return True

    def _configure(self, monitor_id: str, configuration: Dict):
        """
        Configures the monitor with the given ID with the given configuration.

        Will create the monitor if it does not exist.
        :param monitor_id: ID of the monitor
        :param configuration: configuration of the monitor
        """
        # Note: Shinobi used to represent "details" as a JSON dumped string but not needs to be JSON
        configuration["details"] = ShinobiMonitorOrm._parse_details(configuration["details"])
        response = requests.post(f"{self.base_url}/configureMonitor/{self.group_key}/{monitor_id}",
                                 json=dict(data=configuration))
        raise_if_errors(response)
