from dataclasses import dataclass
from typing import Dict, Optional, List, Set

import requests

from shinobi_client.client import ShinobiClient
from shinobi_client._common import raise_if_errors, wait_and_verify


@dataclass
class ShinobiMonitorAlreadyExistsError(ValueError):
    """
    TODO
    """
    monitor_id: str


@dataclass
class ShinobiMonitorDoesNotExistError(ValueError):
    """
    TODO
    """
    monitor_id: str


@dataclass
class ShinobiUnsupportedKeysInConfigurationError(ValueError):
    """
    TODO
    """
    unsupported_keys: Set[str]


class ShinobiMonitorOrm:
    """
    Shinobi monitor ORM.

    Uses API:
    https://shinobi.video/docs/api#content-add-edit-or-delete-a-monitor
    """
    SUPPORTED_KEYS = {"name", "details", "type", "ext", "protocol", "host", "path", "port", "fps", "mode", "width",
                      "height"}

    @staticmethod
    def filter_only_supported_keys(configuration: Dict) -> Dict:
        """
        TODO
        :param configuration:
        :return:
        """
        return dict(filter(lambda item: item[0] in ShinobiMonitorOrm.SUPPORTED_KEYS, configuration.items()))

    @staticmethod
    def is_configuration_equivalent(configuration_1: Dict, configuration_2: Dict) -> bool:
        """
        TODO
        :param configuration_1:
        :param configuration_2:
        :return:
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
        TODO
        :param configuration:
        :return:
        :raises ShinobiUnsupportedKeysInConfigurationError:
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
        :param email:
        :param password:
        """
        self.shinobi_client = shinobi_client
        user = self.shinobi_client.user.get(email, password)
        self.api_key = user["auth_token"]
        self.group_key = user["ke"]

    def get(self, monitor_id: str) -> Optional[Dict]:
        """
        TODO
        :param monitor_id:
        :return:
        """
        response = requests.get(f"{self.base_url}/monitor/{self.group_key}/{monitor_id}")
        response.raise_for_status()
        content = response.json()
        if not content:
            return None
        return content

    def get_all(self) -> Dict[str, Dict]:
        """
        TODO
        :return:
        """
        response = requests.get(f"{self.base_url}/monitor/{self.group_key}")
        response.raise_for_status()
        return {entry["mid"]: entry for entry in response.json()}

    def create(self, monitor_id: str,  configuration: Dict, verify: bool = True) -> Dict:
        """
        TODO
        :param monitor_id:
        :param configuration:
        :param verify:
        :return:
        :raises MonitorAlreadyExistsError:
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
        TODO

        :param monitor_id:
        :param configuration:
        :param verify:
        :return:
        """
        ShinobiMonitorOrm.validate_configuration(configuration)
        current_configuration = self.get(monitor_id)
        if not current_configuration:
            raise ShinobiMonitorDoesNotExistError(monitor_id)

        # comparable_input_configuration = set(map(lambda item: (item[0], str(item[1])), configuration.items()))
        # comparable_current_configuration = set(
        #     map(lambda item: (item[0], str(item[1])),
        #         ShinobiMonitorOrm.filter_only_supported_keys(current_configuration).items()))
        if ShinobiMonitorOrm.is_configuration_equivalent(current_configuration, configuration):
            return False

        # TODO: it's unclear whether the other things need to be set (else their value may be changed)?
        # configuration = {**current_configuration, **configuration}
        self._configure(monitor_id, configuration)

        if verify and not wait_and_verify(lambda: ShinobiMonitorOrm.is_configuration_equivalent(
                self.get(monitor_id), configuration)):
            raise RuntimeError(f"Could not change configuration of monitor \"{monitor_id}\" to: {configuration}")

        return True

    def delete(self, monitor_id: str, verify: bool = True) -> bool:
        """
        TODO
        :param monitor_id:
        :param verify:
        :return:
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
        TODO
        :param monitor_id:
        :param configuration:
        :return:
        """
        response = requests.post(f"{self.base_url}/configureMonitor/{self.group_key}/{monitor_id}",
                                 json=dict(data=configuration))
        raise_if_errors(response)
