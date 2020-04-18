from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple

import requests

from shinobi_client.client import ShinobiClient
from shinobi_client._common import raise_if_errors, wait_and_verify


@dataclass
class ShinobiMonitorAlreadyExistsError(ValueError):
    monitor_id: str


@dataclass
class ShinobiMonitorDoesNotExistError(ValueError):
    monitor_id: str


@dataclass
class ShinobiUnsupportedKeysInConfigurationError(ValueError):
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
    def is_configuration_equivalent(configuration_1: Dict, configuration_2: Dict) -> bool:
        """
        Determines whether the given configurations are equivalent when considering only the key/values that can be set
        and the value types that matter.
        :param configuration_1: first configuration
        :param configuration_2: second configuration
        :return: `True` if the given configurations are equivalent
        """
        configurations = (configuration_1, configuration_2)
        comparable_configurations = []
        for configuration in configurations:
            comparable_configurations.append(
                set(map(lambda item: (item[0], str(item[1])),
                        ShinobiMonitorOrm.filter_only_supported_keys(configuration).items())))
        assert len(comparable_configurations) == 2
        return comparable_configurations[0] == comparable_configurations[1]

    @staticmethod
    def validate_configuration(configuration: Dict):
        """
        Validates that the configuration only contains supported keys.
        :param configuration: the configuration to validate
        :raises ShinobiUnsupportedKeysInConfigurationError: if the configuration contains supported keys
        """
        unsupported_keys = set(configuration.keys()) - ShinobiMonitorOrm.SUPPORTED_KEYS
        if len(unsupported_keys) > 0:
            raise ShinobiUnsupportedKeysInConfigurationError(unsupported_keys)

    @property
    def base_url(self) -> str:
        return f"http://{self.shinobi_client.host}:{self.shinobi_client.port}/{self.api_key}"

    def __init__(self, shinobi_client: ShinobiClient, email: str, password: str):
        """
        Constructor.
        :param shinobi_client: client connected to Shinobi installation
        :param email: email of user to setup monitors for
        :param password: password of user to setup monitors for
        """
        self.shinobi_client = shinobi_client
        user = self.shinobi_client.user.get(email, password)
        self.api_key = user["auth_token"]
        self.group_key = user["ke"]

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
        return content

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
                return (json_response, )
        else:
            return tuple(json_response)

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
        ShinobiMonitorOrm.validate_configuration(configuration)
        current_configuration = self.get(monitor_id)
        if not current_configuration:
            raise ShinobiMonitorDoesNotExistError(monitor_id)

        if ShinobiMonitorOrm.is_configuration_equivalent(current_configuration, configuration):
            return False

        self._configure(monitor_id, configuration)

        if verify and not wait_and_verify(lambda: ShinobiMonitorOrm.is_configuration_equivalent(
                self.get(monitor_id), configuration)):
            raise RuntimeError(f"Could not change configuration of monitor \"{monitor_id}\" to: {configuration}")

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
        response = requests.post(f"{self.base_url}/configureMonitor/{self.group_key}/{monitor_id}",
                                 json=dict(data=configuration))
        raise_if_errors(response)
