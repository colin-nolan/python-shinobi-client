import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from tempfile import mkdtemp
from time import sleep
from typing import Callable, Optional, Dict

import git
import requests
from get_port import find_free_port
from uuid import uuid4

DEFAULT_DOCKER_SHINOBI_GIT_REPO_URL = "https://github.com/colin-nolan/docker-shinobi"
DEFAULT_DOCKER_SHINOBI_GIT_REPO_BRANCH = "master"


def _requires_docker_shinobi(caller: Callable):
    def wrapper(self: "ShinobiController", *args, **kwargs):
        self._clone_docker_shinobi()
        return caller(self, *args, **kwargs)

    return wrapper


class ShinobiAlreadyRunningError(RuntimeError):
    """
    Error raised if it is a problem that Shinobi is already running.
    """


@dataclass
class Shinobi:
    """
    Model of Shinobi installation.
    """
    super_user_email: str
    super_user_password: str
    super_user_token: str
    port: str
    host: str

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}"


class ShinobiController:
    """
    Controls the running of a Shinobi installation from Python.

    Designed for temporarily running Shinobi, e.g. for testing.
    """
    @staticmethod
    def _wait_for_start(shinobi: Shinobi):
        """
        Blocks until service is ready.
        :param shinobi: started shinobi
        """
        interval = 0.05
        while True:
            try:
                requests.get(shinobi.url)
                return
            except requests.exceptions.ConnectionError:
                sleep(interval)
                interval += 0.01

    @property
    def _temp_directory(self) -> str:
        if self.__temp_directory is None:
            self.__temp_directory = mkdtemp(prefix=f"{self.__class__.__name__}-", dir=self.temp_root_location)
        return self.__temp_directory

    @property
    def _shinobi_directory(self) -> str:
        return os.path.join(self._temp_directory, os.path.basename(self.docker_shinobi_git_repo_url))

    def __init__(self, docker_shinobi_git_repo_url: str = DEFAULT_DOCKER_SHINOBI_GIT_REPO_URL,
                 docker_shinobi_git_repo_branch: str = DEFAULT_DOCKER_SHINOBI_GIT_REPO_BRANCH,
                 temp_root_location: str = "/tmp"):
        """
        Constructor.
        :param docker_shinobi_git_repo_url: URL of the Git repository that
        :param temp_root_location: location in which temp files are created (must be mountable using Docker)
        """
        self.temp_root_location = temp_root_location
        self.docker_shinobi_git_repo_url = docker_shinobi_git_repo_url
        self.docker_shinobi_git_repo_branch = docker_shinobi_git_repo_branch
        self.__temp_directory: Optional[str] = None
        self._stop = None

    def __enter__(self) -> Shinobi:
        return self.start()

    def __exit__(self, *args):
        self.stop()

    @_requires_docker_shinobi
    def start(self) -> Shinobi:
        """
        Starts an installation of Shinobi.
        :return: details about the started installation
        :raises ShinobiAlreadyRunningError: if Shinobi is already running
        """
        if self._stop:
            raise ShinobiAlreadyRunningError()

        environment = self._create_run_environment()

        self._stop = lambda: subprocess.check_output(
            ["docker-compose", "down"],
            cwd=self._shinobi_directory, env=environment)

        subprocess.check_output(
            ["docker-compose", "up", "--build", "--detach", "--renew-anon-volumes"],
            cwd=self._shinobi_directory, env=environment)
        shinobi = Shinobi(
            super_user_email=environment["SHINOBI_SUPER_USER_EMAIL"],
            super_user_password=environment["SHINOBI_SUPER_USER_PASSWORD"],
            super_user_token=environment["SHINOBI_SUPER_USER_TOKEN"],
            port=environment["SHINOBI_HOST_PORT"],
            # XXX: hardcoding assumption that the Docker daemon is on the host
            host="0.0.0.0"
        )
        ShinobiController._wait_for_start(shinobi)

        return shinobi

    def stop(self):
        """
        Stops any running instance of a Shinobi installation.
        :return: whether an installation was stopped
        """
        if not self._stop:
            return False
        self._stop()
        self._stop = None
        return True

    def _create_run_environment(self) -> Dict[str, str]:
        """
        Creates the environment in which the containerised Shinobi can run.
        :return: environment
        """
        # Mac does have/allow mounting of /etc/timezone and /etc/localtime so faking them
        timezone_file_location = os.path.join(self._temp_directory, "timezone")
        Path(timezone_file_location).touch()
        localtime_file_location = os.path.join(self._temp_directory, "localtime")
        Path(localtime_file_location).touch()

        port, port_find_error = find_free_port()
        if port_find_error:
            raise RuntimeError(f"Error finding free port: {port_find_error}")

        return dict(
            **os.environ,
            SHINOBI_VIDEO_LOCATION=os.path.join(self._temp_directory, "videos"),
            MYSQL_USER_PASSWORD=str(uuid4()),
            MYSQL_ROOT_PASSWORD=str(uuid4()),
            SHINOBI_SUPER_USER_EMAIL=str(uuid4()),
            SHINOBI_SUPER_USER_PASSWORD=str(uuid4()),
            SHINOBI_SUPER_USER_TOKEN=str(uuid4()),
            SHINOBI_DATA_LOCATION=os.path.join(self._temp_directory, "data"),
            SHINOBI_TIMEZONE=timezone_file_location,
            SHINOBI_LOCALTIME=localtime_file_location,
            SHINOBI_HOST_PORT=str(port)
        )

    def _clone_docker_shinobi(self):
        """
        Clones repository for running containerised Shinobi.
        """
        if not os.path.exists(self._shinobi_directory):
            git.Repo.clone_from(self.docker_shinobi_git_repo_url, self._shinobi_directory,
                                branch=self.docker_shinobi_git_repo_branch)


def start_shinobi(*args, **kwargs) -> ShinobiController:
    """
    Wrapper for starting Shinobi easily in a context, e.g.
    ```
    with start_shinobi() as shinobi:
        print(shinobi)
    ```
    :param args: positional arguments to pass to `ShinobiController.__init__`
    :param kwargs: key word arguments to pass to `ShinobiController.__init__`
    :return: created Shinboi controller
    """
    return ShinobiController(*args, **kwargs)
