import json
import os
from typing import Dict

RESOURCE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))

EXAMPLE_MONITOR_LOCATIONS = {
    1: os.path.join(RESOURCE_DIRECTORY, "example-monitor-1.json"),
    2: os.path.join(RESOURCE_DIRECTORY, "example-monitor-2.json")
}


def get_monitor_configuration(example_monitor_id: int = 1) -> Dict:
    """
    Gets the example monitor configuration with the given ID (or first monitor if no ID is given).
    :param example_monitor_id: ID of monitor to load
    :return: loaded monitor
    """
    return json.load(open(EXAMPLE_MONITOR_LOCATIONS[example_monitor_id], "r"))

