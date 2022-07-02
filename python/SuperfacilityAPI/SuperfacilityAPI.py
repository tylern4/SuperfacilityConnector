from typing import Dict, List
from authlib.integrations.requests_client import (
    OAuth2Session,
    OAuthError
)
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import requests
import sys
from time import sleep
from datetime import datetime
import json
import logging
from pathlib import Path
import urllib.parse

# Configurations in differnt files
from .error_warnings import (
    permissions_warning,
    warning_fourOfour,
    no_client,
    FourOfourException,
    NoClientException,
)
from .api_version import API_VERSION
from .nersc_systems import (
    NERSC_DEFAULT_COMPUTE,
    nersc_systems,
    nersc_compute,
    nersc_filesystems,
)


class SuperfacilityAPI:
    _status = None
    access_token = None

    def __init__(self, token=None):
        """SuperfacilityAPI

        Parameters
        ----------
        client_id : str, optional
            Client ID obtained from iris, by default None
        private_key : str, optional
            Private key obtained from iris, by default None
        """
        self.API_VERSION = API_VERSION
        # Base url for sfapi requests
        self.base_url = f'https://api.nersc.gov/api/v{self.API_VERSION}'
        self.headers = {'accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded'}

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

    def __generic_request(self, sub_url: str, header: Dict = None) -> Dict:
        """PRIVATE: Used to make a GET request to the api given a fully qualified sub url.


        Parameters
        ----------
        sub_url : str
            Url of the specific funtion to request.

        Returns
        -------
        Dict
            Dictionary given by requests.Responce.json()
        """
        try:
            # Perform a get request
            resp = requests.get(
                self.base_url+sub_url, headers=self.headers if header is None else header)
            status = resp.status_code
            # Raise error based on reposnce status [200 OK] [500 err]
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err, file=sys.stderr)
            if status == 404:
                print(warning_fourOfour.format(
                    self.base_url+sub_url), file=sys.stderr)
                raise FourOfourException(
                    f"404 not found {self.base_url+sub_url}")

            if self.access_token is None:
                warning = no_client
                print(warning, file=sys.stderr)
                raise NoClientException("warning")
            else:
                warning = permissions_warning

            return warning

        json_resp = resp.json()
        return json_resp

    def __generic_post(self, sub_url: str, header: Dict = None, data: Dict = None) -> Dict:
        """PRIVATE: Used to make a POST request to the api given a fully qualified sub url.


        Parameters
        ----------
        sub_url : str
            Url of the specific funtion to request.

        Returns
        -------
        Dict
            Dictionary given by requests.Responce.json()
        """

        try:
            # Perform a get request
            resp = requests.post(
                self.base_url+sub_url,
                headers=self.headers if header is None else header,
                data="" if data is None else urllib.parse.urlencode(data))
            status = resp.status_code
            # Raise error based on reposnce status [200 OK] [500 err]
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err, file=sys.stderr)
            if status == 404:
                print(warning_fourOfour.format(
                    self.base_url+sub_url), file=sys.stderr)
                return None

            if self.access_token is None:
                warning = no_client
            else:
                warning = permissions_warning
            print(warning, file=sys.stderr)
            return None

        json_resp = resp.json()
        return json_resp

    def __generic_delete(self, sub_url: str, header: Dict = None) -> Dict:
        """PRIVATE: Used to make a DELETE request to the api given a fully qualified sub url.


        Parameters
        ----------
        sub_url : str
            Url of the specific funtion to request.

        Returns
        -------
        Dict
            Dictionary given by requests.Responce.json()
        """

        try:
            # Perform a get request
            resp = requests.delete(
                self.base_url+sub_url,
                headers=self.headers if header is None else header)
            status = resp.status_code
            # Raise error based on reposnce status [200 OK] [500 err]
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err, file=sys.stderr)
            if status == 404:
                print(warning_fourOfour.format(
                    self.base_url+sub_url), file=sys.stderr)
                return None

            if self.access_token is None:
                warning = no_client
            else:
                warning = permissions_warning
            print(warning, file=sys.stderr)
            return None

        json_resp = resp.json()
        return json_resp

    def __get_system_status(self) -> None:
        """Gets the system status and all systems and stores them.
        """
        self._status = self.__generic_request('/status')
        self.systems = [system['name'] for system in self._status]

    def system_names(self) -> List:
        """Returns list of all systems at NERSC

        Returns
        -------
        List
        """
        self.__get_system_status()
        return self.systems

    def status(self, name: str = None, notes: bool = False, outages: bool = False, planned: bool = False, new: bool = False) -> Dict:
        """Gets status of NERSC systems

        Parameters
        ----------
        name : str, optional
            Name of system to get the status for, by default None
            Can be combined with notes/outages/planned to get detailed status
        notes : bool, optional
            Get notes on the status, by default False
        outages : bool, optional
            Get current outages, by default False
        planned : bool, optional
            Get planned outages, by default False
        new : bool, optional
            Get newest version of the status, by default False

        Returns
        -------
        Dict
        """
        sub_url = '/status'
        if notes:
            sub_url = '/status/notes'

        if outages:
            sub_url = '/status/outages'

        if planned:
            sub_url = '/status/outages/planned'

        if name is not None and name in nersc_systems:
            sub_url = f'{sub_url}/{name}'

        if sub_url == '/status' and not new:
            if self._status is None:
                self.__get_system_status()
            return self._status

        return self.__generic_request(sub_url)

    def ls(self, token: str = None, site: str = NERSC_DEFAULT_COMPUTE, remote_path: str = None) -> Dict:
        """ls comand on a site

        Parameters
        ----------
        site : str, optional
            Name of the site you want to ls at, by default NERSC_DEFAULT_COMPUTE
        remote_path : str, optional
            Path on the system, by default None

        Returns
        -------
        Dict
        """
        if remote_path is None:
            return None

        sub_url = f'/utilities/ls'
        path = remote_path.replace("/", "%2F")

        sub_url = f'{sub_url}/{site}/{path}'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def projects(self, token: str = None) -> Dict:
        """Get information about your projects

        Parameters
        ----------
        repo_name : str, optional
            Get information about a specific project, by default None

        Returns
        -------
        Dict
        """

        sub_url = '/account/projects'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def get_groups(self, token: str = None, groups: str = None) -> Dict:
        """Get information about your groups

        Parameters
        ----------
        repo_name : str, optional
            Get information about a specific project, by default None

        Returns
        -------
        Dict
        """

        sub_url = '/account/groups'
        if groups is not None:
            sub_url = f'/account/groups/{groups}'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def create_groups(self, token: str = None, name: str = "", repo_name: str = ""):
        """Create new groups

        Parameters
        ----------
        repo_name : str, optional
            Get information about a specific project, by default None

        Returns
        -------
        Dict
        """

        sub_url = '/account/groups'

        data = {"name": name, "repo_name": repo_name}
        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_post(sub_url, data=data)

    def roles(self, token: str = None) -> Dict:
        """Get roles for your account

        Returns
        -------
        Dict
        """
        sub_url = '/account/roles'
        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def tasks(self, token: str = None, task_id: int = None) -> Dict:
        """Used to get SuperfacilityAPI tasks

        Parameters
        ----------
        task_id : int, optional
            SuperfacilityAPI task number, by default None

        Returns
        -------
        Dict
        """
        sub_url = '/tasks'
        if task_id is not None:
            sub_url = f'{sub_url}/{task_id}'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def get_job(self, token: str = None, site: str = NERSC_DEFAULT_COMPUTE, sacct: bool = True,
                jobid: int = None, user: str = None, partition: str = None) -> Dict:
        """Used to get information about slurm jobs on a system

        Parameters
        ----------
        site : str, optional
            NERSC site where slurm job is running, by default NERSC_DEFAULT_COMPUTE
        sacct : bool, optional
            Whether to use sacct[true] or squeue[false], by default True
        jobid : int, optional
            Slurm job id to get information for, by default None
        user : int, optional
            Username to get information for, by default None

        Returns
        -------
        Dict

        """
        if site not in nersc_compute:
            return None

        sub_url = f'/compute/jobs/{site}'
        if jobid is not None:
            sub_url = f'{sub_url}/{jobid}'

        sub_url = f'{sub_url}?sacct={"true" if sacct else "false"}'

        if user is not None:
            sub_url = f'{sub_url}&kwargs=user%3D{user}'
        elif partition is not None:
            sub_url = f'{sub_url}&kwargs=partition%3D{partition}'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def post_job(self, token: str = None,
                 site: str = NERSC_DEFAULT_COMPUTE,
                 script: str = None, isPath: bool = True,
                 run_async: bool = False, timeout: int = 30, sleeptime: int = 2) -> int:
        """Adds a new job to the queue

        Parameters
        ----------
        site : str, optional
            Site to add job to, by default NERSC_DEFAULT_COMPUTE
        script : str, optional
            Path or script to call sbatch on, by default None
        isPath : bool, optional
            Is the script a path on the site or a file, by default True

        Returns
        -------
        int
            slurm jobid
        """
        if site not in nersc_compute:
            return None
        sub_url = f'/compute/jobs/{site}'
        script.replace("/", "%2F")

        is_path = 'true' if isPath else 'false'
        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        data = {'job': script, 'isPath': is_path}
        resp = self.__generic_post(sub_url, data=data)

        logging.debug("Submitted new job, wating for responce.")
        if resp == None:
            return {'error': -1, 'jobid': None, 'task_id': None}
        task_id = resp['task_id']
        default = {'error': None, 'jobid': None, 'task_id': task_id}
        if run_async:
            logging.debug(task_id)
            logging.debug(default)
            return default

        # Waits (up to {timeout} seconds) for the job to be submited before returning
        for i in range(timeout):
            if i > 0:
                sleep(sleeptime)

            logging.debug(f"Running {i}")
            task = self.tasks(self.access_token, resp['task_id'])
            logging.debug(f"task = {task}")
            if task is not None and task['status'] == 'completed':
                jobinfo = json.loads(task['result'])
                return {'error': jobinfo['error'], 'jobid': jobinfo['jobid'], 'task_id': task_id}

        return default

    def delete_job(self, token: str = None, site: str = NERSC_DEFAULT_COMPUTE, jobid: int = None) -> Dict:
        """Removes job from queue

        Parameters
        ----------
        site : str, optional
            Site to remove job from, by default NERSC_DEFAULT_COMPUTE
        jobid : int, optional
            Jobid to remove, by default None

        Returns
        -------
        Dict
        """
        if site not in nersc_compute:
            return None
        sub_url = f'/compute/jobs/{site}/{jobid}'
        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_delete(sub_url)

    def custom_cmd(self, token: str = None, run_async: bool = False,
                   site: str = NERSC_DEFAULT_COMPUTE, cmd: str = None,
                   timeout: int = 30, sleeptime: int = 2) -> Dict:
        """Run custom command

        Parameters
        ----------
        site : str, optional
            Site to remove job from, by default NERSC_DEFAULT_COMPUTE
        cmd: str,
            Command to run

        Returns
        -------
        Dict
        """
        if site not in nersc_compute:
            return None
        sub_url = f'/utilities/command/{site}'
        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        data = {'executable': cmd}

        resp = self.__generic_post(sub_url, data=data)
        logging.debug("Submitted new job, wating for responce.")
        logging.debug(f"{resp}")
        if resp == None:
            return {'error': -1, 'task_id': None}

        task_id = resp['task_id']

        # If we want the call async just return task_id
        if run_async:
            return {'error': None, 'task_id': task_id}

        # Waits (up to {timeout} seconds) for the job to be submited before returning
        for i in range(timeout):
            if i > 0:
                sleep(sleeptime)
            task = self.tasks(self.access_token, resp['task_id'])
            if isinstance(task, dict) and task['status'] == 'completed':
                return json.loads(task['result'])
            sleep(sleeptime)

        try:
            # Gives back error if something went wrong
            task = self.tasks(self.access_token, resp['task_id'])
            ret = json.loads(task['result'])
            ret['task_id'] = task_id
            return ret
        except TypeError as e:
            logging.error(f"{type(e).__name__} : {e}")
            return {'jobid': f"{type(e).__name__} : {e}"}

    ################## In Progress #######################
    def download(self, token: str = None, site: str = NERSC_DEFAULT_COMPUTE, remote_path: str = None,
                 binary: bool = True, local_path: str = '.', save: bool = False) -> Dict:

        if site is None or remote_path is None:
            return False

        if site not in [NERSC_DEFAULT_COMPUTE, 'perlmutter']:
            return False

        sub_url = '/utilities/download'
        file_name = f'{local_path}/{remote_path.split("/")[-1]}'
        path = remote_path.replace("/", "%2F")

        sub_url = f'{sub_url}/{site}/{path}'

        if binary:
            sub_url = f'{sub_url}?binary=true'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        res = self.__generic_request(sub_url)
        if res is not None:
            if res['error'] is None:
                if save:
                    with open(file_name, "wb") as f:
                        byte = bytes(res['file'], 'utf8')
                        f.write(byte)
                    return True
                else:
                    return res
        else:
            return False if save else None
