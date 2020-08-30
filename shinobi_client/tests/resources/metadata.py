import json
import os
from typing import Dict, Any

_RESOURCE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

_MONITORS_DIRECTORY = os.path.join(_RESOURCE_DIRECTORY, "monitors")
EXAMPLE_MONITOR_LOCATIONS = {
    1: os.path.join(_MONITORS_DIRECTORY, "example-1.json"),
    2: os.path.join(_MONITORS_DIRECTORY, "example-2.json"),
    3: os.path.join(_MONITORS_DIRECTORY, "details-as-json.json"),
}


def get_monitor_configuration(example_monitor_id: Any = 1) -> Dict:
    """
    Gets the example monitor configuration with the given ID (or first monitor if no ID is given).
    :param example_monitor_id: ID of monitor to load
    :return: loaded monitor
    """
    return json.load(open(EXAMPLE_MONITOR_LOCATIONS[example_monitor_id], "r"))

