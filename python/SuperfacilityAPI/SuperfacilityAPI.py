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
from . import SuperfacilityAccessToken

# Configurations in differnt files
from .SuperfacilityErrors import (
    permissions_warning,
    warning_fourOfour,
    no_client,
    FourOfourException,
    InternalServerError,
    NoClientException,
    SuperfacilityCmdFailed,
    SuperfacilitySiteDown,
    ApiTokenError
)
from .api_version import API_VERSION
from .nersc_systems import (
    NERSC_DEFAULT_COMPUTE,
    nersc_systems,
    NerscCompute,
    NerscFilesystems
)

from enum import Flag, auto, Enum

global HAVE_PANDAS
try:
    import pandas as pd
    HAVE_PANDAS = True
except ImportError:
    HAVE_PANDAS = False


sacct_columns = ['account', 'admincomment', 'alloccpus', 'allocnodes', 'alloctres', 'associd', 'avecpu',
                 'avecpufreq',  'avediskread', 'avediskwrite', 'avepages', 'averss', 'avevmsize', 'blockid',
                 'cluster', 'comment', 'constraints', 'consumedenergy', 'consumedenergyraw', 'cputime', 'cputimeraw',
                 'dbindex', 'derivedexitcode', 'elapsed', 'elapsedraw', 'eligible', 'end', 'exitcode', 'flags',
                 'gid', 'group', 'jobid', 'jobidraw', 'jobname', 'layout', 'maxdiskread', 'maxdiskreadnode',
                 'maxdiskreadtask', 'maxdiskwrite', 'maxdiskwritenode', 'maxdiskwritetask', 'maxpages',
                 'maxpagesnode', 'maxpagestask', 'maxrss', 'maxrssnode', 'maxrsstask', 'maxvmsize', 'maxvmsizenode',
                 'maxvmsizetask', 'mcslabel', 'mincpu', 'mincpunode', 'mincputask', 'ncpus', 'nnodes',
                 'nodelist', 'ntasks', 'priority', 'partition', 'qos', 'qosraw', 'reason', 'reqcpufreq',
                 'reqcpufreqmin', 'reqcpufreqmax', 'reqcpufreqgov', 'reqcpus', 'reqmem', 'reqnodes', 'reqtres',
                 'reservation', 'reservationid', 'reserved', 'resvcpu', 'resvcpuraw', 'start', 'state', 'submit',
                 'suspended', 'systemcpu', 'systemcomment', 'timelimit', 'timelimitraw', 'totalcpu', 'tresusageinave',
                 'tresusageinmax', 'tresusageinmaxnode', 'tresusageinmaxtask', 'tresusageinmin', 'tresusageinminnode',
                 'tresusageinmintask', 'tresusageintot', 'tresusageoutave', 'tresusageoutmax', 'tresusageoutmaxnode',
                 'tresusageoutmaxtask', 'tresusageoutmin', 'tresusageoutminnode', 'tresusageoutmintask',
                 'tresusageouttot', 'uid', 'user', 'usercpu', 'wckey', 'wckeyid', 'workdir', ]

squeue_columns = ['account', 'tres_per_node', 'min_cpus', 'min_tmp_disk', 'end_time', 'features', 'group',
                  'over_subscribe', 'jobid', 'name', 'comment', 'time_limit', 'min_memory', 'req_nodes',
                  'command', 'priority', 'qos', 'reason', '', 'st', 'user', 'reservation', 'wckey', 'exc_nodes',
                  'nice', 's:c:t', 'exec_host', 'cpus', 'nodes', 'dependency', 'array_job_id', 'sockets_per_node',
                  'cores_per_socket', 'threads_per_core', 'array_task_id', 'time_left', 'time', 'nodelist',
                  'contiguous', 'partition', 'nodelist(reason)', 'start_time', 'state', 'uid', 'submit_time', 'licenses', 'core_spec', 'schednodes', 'work_dir', ]


class NerscSystemState(Flag):
    ACTIVE = auto()
    DOWN = auto()
    DEGRADED = auto()
    MAINTNAINCE = auto()
    UNKNOWN = auto()

    def __str__(self):
        return f'{self.name.lower()}'


class SuperfacilityAPI:
    _status = None
    access_token = None

    def __init__(self, token=None, base_url=None):
        """SuperfacilityAPI

        Parameters
        ----------
        client_id : str, optional
            Client ID obtained from iris, by default None
        private_key : str, optional
            Private key obtained from iris, by default None
        """
        self.API_VERSION = API_VERSION
        if base_url is None:
            # Base url for sfapi requests
            self.base_url = f'https://api.nersc.gov/api/v{self.API_VERSION}'
        else:
            self.base_url = base_url
        self.headers = {'accept': 'application/json',
                        'Content-Type': 'application/x-www-form-urlencoded'}
        self.access_token = token

    def __generic_get(self, sub_url: str, header: Dict = None) -> Dict:
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
        logging.debug(f"__generic_get {sub_url}")
        json_resp = {}
        if isinstance(self.access_token, str):
            self.headers['Authorization'] = f'Bearer {self.access_token}'
        elif isinstance(self.access_token, SuperfacilityAccessToken):
            self.headers['Authorization'] = f'Bearer {self.access_token.token}'
        else:
            raise PermissionError("No Token Provided")

        try:
            logging.debug(
                f"Getting from {self.base_url+sub_url}")
            # Perform a get request
            resp = requests.get(
                self.base_url+sub_url, headers=self.headers if header is None else header)

            status = resp.status_code
            # Raise error based on reposnce status [200 OK] [500 err]
            resp.raise_for_status()
            json_resp = resp.json()
        except requests.exceptions.HTTPError as err:
            if status == 404:
                logging.warning(warning_fourOfour.format(
                    self.base_url+sub_url))
                raise FourOfourException(
                    f"404 not found {self.base_url+sub_url}")
            elif status == 500:
                logging.warning(f"500 Internal Server Error {err}")
                raise InternalServerError(f"500 Internal Server Error {err}")
            elif status == 403:
                logging.warning(
                    f"The security token included in the request is invalid. {err}")
                raise ApiTokenError(
                    f"The security token included in the request is invalid.  {err}")
        except requests.exceptions.TooManyRedirects as err:
            logging.warning(f"TooManyRedirects {err}")
            raise InternalServerError(f"TooManyRedirects {err}")

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
        logging.debug(f"__generic_post {sub_url}")
        json_resp = {}

        if isinstance(self.access_token, str):
            self.headers['Authorization'] = f'Bearer {self.access_token}'
        elif isinstance(self.access_token, SuperfacilityAccessToken):
            self.headers['Authorization'] = f'Bearer {self.access_token.token}'
        else:
            raise PermissionError("No Token Provided")

        try:
            logging.debug(
                f"Sending {data} to {self.base_url+sub_url}")
            # Perform a get request
            resp = requests.post(
                self.base_url+sub_url,
                headers=self.headers if header is None else header,
                data="" if data is None else urllib.parse.urlencode(data))
            status = resp.status_code
            # Raise error based on reposnce status [200 OK] [500 err]
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if status == 404:
                logging.warning(warning_fourOfour.format(
                    self.base_url+sub_url))
                raise FourOfourException(
                    f"404 not found {self.base_url+sub_url}")
            elif status == 403:
                logging.warning(
                    f"The security token included in the request is invalid. {err}")
                raise ApiTokenError(
                    f"The security token included in the request is invalid.  {err}")
            elif status == 500:
                if self.access_token is None:
                    logging.warning(no_client)
                    raise NoClientException(no_client)
                logging.warning(f"500 Internal Server Error")
                raise InternalServerError(f"500 Internal Server Error")

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
        logging.debug(f"__generic_delete {sub_url}")
        json_resp = {}

        if isinstance(self.access_token, str):
            self.headers['Authorization'] = f'Bearer {self.access_token}'
        elif isinstance(self.access_token, SuperfacilityAccessToken):
            self.headers['Authorization'] = f'Bearer {self.access_token.token}'
        else:
            raise PermissionError("No Token Provided")

        try:
            # Perform a get request
            resp = requests.delete(
                self.base_url+sub_url,
                headers=self.headers if header is None else header)
            status = resp.status_code
            # Raise error based on reposnce status [200 OK] [500 err]
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            if status == 404:
                logging.warning(warning_fourOfour.format(
                    self.base_url+sub_url))
                raise FourOfourException(
                    f"404 not found {self.base_url+sub_url}")
            elif status == 403:
                logging.warning(
                    f"The security token included in the request is invalid. {err}")
                raise ApiTokenError(
                    f"The security token included in the request is invalid.  {err}")
            elif status == 500:
                if self.access_token is None:
                    logging.warning(no_client)
                    raise NoClientException(no_client)

                logging.warning(f"500 Internal Server Error")
                raise InternalServerError(f"500 Internal Server Error")

        json_resp = resp.json()
        return json_resp

    def __get_system_status(self) -> None:
        """Gets the system status and all systems and stores them.
        """
        logging.debug("Getting full status")
        self._status = self.__generic_get('/status/')
        logging.debug(f"Putting {self._status} into the systems")
        self.systems = [system['name'] for system in self._status]

    def system_names(self) -> List:
        """Returns list of all systems at NERSC

        Returns
        -------
        List
        """
        self.__get_system_status()
        return self.systems

    def status(self, name: str = None, notes: bool = False,
               outages: bool = False, planned: bool = False,
               new: bool = False) -> Dict:
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

        if name == "muller":
            return {'name': 'muller', 'full_name': 'muller', 'description': 'System is active',
                    'system_type': 'compute', 'notes': [], 'status': 'active', 'updated_at': 'never'}

        if sub_url == '/status' and not new:
            if self._status is None:
                self.__get_system_status()
            return self._status

        return self.__generic_get(sub_url)

    def system_status(self, name: str = "perlmutter"):
        """system_status

        Args:
            name (str, optional): Name of the system to check status. Defaults to "perlmutter".

        Returns:
            NerscSystemState: State of the system as an enum
        """
        # Default to unknown state
        state = NerscSystemState.UNKNOWN
        # Call the status command to get current status
        data = self.status(name=name)
        # If there's an error return unknown state
        if not isinstance(data, dict):
            return state

        # Active comes up for up and degraded so we split them based on descrition
        if data['status'] == 'active':
            return NerscSystemState.ACTIVE
        elif data['status'] == 'degraded':
            return NerscSystemState.DEGRADED
        else:
            state = NerscSystemState.DOWN
            if data['description'] == "Scheduled Maintenance":
                state = NerscSystemState.MAINTNAINCE

        return state

    def check_status(self, name: str = "perlmutter"):
        """Check Status

        Args:
            name (str, optional): Name to get status od. Defaults to "perlmutter".

        Returns:
            bool: Gives bool value if site is up/down, true/false
        """
        # Get status enum
        current_status = self.system_status(name=name)

        down = (NerscSystemState.DOWN | NerscSystemState.MAINTNAINCE |
                NerscSystemState.UNKNOWN)
        # Check if status is any of the down states and return false
        if current_status in down:
            logging.debug(f"{name} is {current_status}")
            return False

        return True

    def ls(self, remote_path: str, site: str = NERSC_DEFAULT_COMPUTE) -> Dict:
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

        return self.__generic_get(sub_url)

    def projects(self) -> Dict:
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

        return self.__generic_get(sub_url)

    def get_groups(self, groups: str = None) -> Dict:
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

        return self.__generic_get(sub_url)

    def create_groups(self, name: str = "", repo_name: str = ""):
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

        return self.__generic_post(sub_url, data=data)

    def roles(self, ) -> Dict:
        """Get roles for your account

        Returns
        -------
        Dict
        """
        sub_url = '/account/roles'

        return self.__generic_get(sub_url)

    def tasks(self, task_id: int = None) -> Dict:
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

        return self.__generic_get(sub_url)

    def get_jobs(self, site: str = NERSC_DEFAULT_COMPUTE, sacct: bool = True,
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

        if site not in NerscCompute:
            return {'status': "", 'output': [], 'error': ""}

        if not self.check_status(name=site):
            logging.debug(site)
            raise SuperfacilitySiteDown(
                f'{site} is down, Reason: {self.system_status(name=site)}')
            # return {'status': "", 'output': [], 'error': ""}

        sub_url = f'/compute/jobs/{site}'
        if jobid is not None:
            sub_url = f'{sub_url}/{jobid}'

        sub_url = f'{sub_url}?sacct={"true" if sacct else "false"}'

        if user is not None:
            sub_url = f'{sub_url}&kwargs=user%3D{user}'
        elif partition is not None:
            sub_url = f'{sub_url}&kwargs=partition%3D{partition}'

        return self.__generic_get(sub_url)

    def squeue(self,
               site: str = NERSC_DEFAULT_COMPUTE,
               jobid: int = None,
               user: str = None,
               partition: str = None,
               dataframe: bool = False):
        """squeue

        Returns similar information as squeue command line

        Args:
            site (str, optional): _description_. Defaults to NERSC_DEFAULT_COMPUTE.
            sacct (bool, optional): _description_. Defaults to True.
            jobid (int, optional): _description_. Defaults to None.
            user (str, optional): _description_. Defaults to None.
            partition (str, optional): _description_. Defaults to None.
        """

        jobs = self.get_jobs(site=site,
                             jobid=jobid,
                             user=user,
                             partition=partition,
                             sacct=False)
        if 'output' in jobs:
            jobs = jobs['output']

        if dataframe and HAVE_PANDAS:
            if len(jobs) == 0:
                return pd.DataFrame(columns=squeue_columns)
            else:
                return pd.DataFrame(jobs)

        return jobs

    def sacct(self,
              site: str = NERSC_DEFAULT_COMPUTE,
              jobid: int = None,
              user: str = None,
              partition: str = None,
              dataframe: bool = False):
        """sacct

        Returns similar information as sacct command line

        Args:
            site (str, optional): _description_. Defaults to NERSC_DEFAULT_COMPUTE.
            sacct (bool, optional): _description_. Defaults to True.
            jobid (int, optional): _description_. Defaults to None.
            user (str, optional): _description_. Defaults to None.
            partition (str, optional): _description_. Defaults to None.
        """

        jobs = self.get_jobs(site=site,
                             jobid=jobid,
                             user=user,
                             partition=partition,
                             sacct=True)
        if 'output' in jobs:
            jobs = jobs['output']

        if dataframe and HAVE_PANDAS:
            if len(jobs) == 0:
                return pd.DataFrame(columns=sacct_columns)
            else:
                return pd.DataFrame(jobs)

        return jobs

    def post_job(self, site: str = NERSC_DEFAULT_COMPUTE,
                 script: str = None, isPath: bool = True,
                 run_async: bool = False,
                 timeout: int = 30,
                 sleeptime: int = 2) -> int:
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

        job_info = {'error': None, 'jobid': None, 'task_id': None}

        if site not in NerscCompute:
            job_info['error'] = 'not a compute site'
            return job_info

        if not self.check_status(name=site):
            logging.debug(site)
            raise SuperfacilitySiteDown(
                f'{site} is down, Reason: {self.system_status(name=site)}')

        sub_url = f'/compute/jobs/{site}'
        script.replace("/", "%2F")
        is_path = 'true' if isPath else 'false'
        data = {'job': script, 'isPath': is_path}
        resp = self.__generic_post(sub_url, data=data)

        logging.debug("Submitted new job, wating for responce.")
        if resp == None:
            return {'error': -1, 'jobid': None, 'task_id': None}

        task_id = resp['task_id']
        job_info['task_id'] = task_id
        if run_async:
            logging.debug(task_id)
            logging.debug(job_info)
            return job_info

        # Waits (up to {timeout} seconds) for the job to be submited before returning
        for i in range(timeout):
            if i > 0:
                sleep(sleeptime)

            logging.debug(f"Checking {i} ...")
            task = self.tasks(resp['task_id'])
            logging.debug(f"task = {task}")
            if task is not None and task['status'] == 'completed':
                jobinfo = json.loads(task['result'])
                return {
                    'error': jobinfo['error'],
                    'jobid': jobinfo['jobid'],
                    'task_id': task_id
                }

        return job_info

    def sbatch(self, site: str = NERSC_DEFAULT_COMPUTE,
               script: str = None, isPath: bool = True) -> int:
        """Adds a new job to the queue like sbatch

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
        # We can check if the path is on the nersc system
        if isPath:
            out = self.ls(script)
            if out['status'] == "ERROR":
                raise FileNotFoundError(f"{script} Not found on {site}")
        # Then see if it's a path on the current system
        elif Path(script).exists():
            logging.debug(
                f"Looks like the script is a path, opending {script}")
            with open(Path(script)) as contents:
                script = contents.read()
        else:
            logging.debug(f"Looks like the script is a string {script}")

        job_output = self.post_job(site=site, script=script, isPath=isPath)

        return job_output['jobid']

    def delete_job(self, site: str = NERSC_DEFAULT_COMPUTE, jobid: int = None) -> Dict:
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
        if site not in NerscCompute:
            return None

        down = NerscSystemState.DOWN | NerscSystemState.MAINTNAINCE | NerscSystemState.UNKNOWN
        current_status = self.system_status()
        if current_status is down:
            logging.debug(
                f"System is {current_status}, job cannot check jobs")
            return None

        sub_url = f'/compute/jobs/{site}/{jobid}'
        logging.debug(f"Calling {sub_url}")

        return self.__generic_delete(sub_url)

    def scancel(self, jobid: int, site: str = NERSC_DEFAULT_COMPUTE) -> bool:
        """Removes job from queue

        Parameters
        ----------
        jobid : int
            Jobid to remove
        site : str, optional
            Site to remove job from, by default NERSC_DEFAULT_COMPUTE


        Returns
        -------
        bool
        """
        del_job = self.delete_job(site=site, jobid=jobid)
        return (del_job['status'] == 'OK')

    def custom_cmd(self,
                   run_async: bool = False,
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
        if site not in NerscCompute:
            return None
        sub_url = f'/utilities/command/{site}'

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
            task = self.tasks(resp['task_id'])
            if isinstance(task, dict) and task['status'] == 'completed':
                return json.loads(task['result'])
            sleep(sleeptime)

        try:
            # Gives back error if something went wrong
            task = self.tasks(resp['task_id'])
            ret = json.loads(task['result'])
            ret['task_id'] = task_id
            return ret
        except TypeError as e:
            logging.warning(f"{type(e).__name__} : {e}")
            return {'jobid': f"{type(e).__name__} : {e}"}

    ################## In Progress #######################
    def download(self,
                 site: str = NERSC_DEFAULT_COMPUTE, remote_path: str = None,
                 binary: bool = False, local_path: str = '.', save: bool = False) -> Dict:

        if site is None:
            raise SuperfacilityCmdFailed("Need site to download from")
        if remote_path is None:
            raise SuperfacilityCmdFailed("Need a remote path to download")

        if site not in ['perlmutter', 'cori']:
            raise SuperfacilityCmdFailed(f"Cannot download from {site}")

        sub_url = '/utilities/download'
        file_name = f'{local_path}/{remote_path.split("/")[-1]}'
        path = remote_path.replace("/", "%2F")

        sub_url = f'{sub_url}/{site}/{path}'

        if binary:
            sub_url = f'{sub_url}?binary=true'

        res = self.__generic_get(sub_url)
        if res is not None:
            if res['error'] is None:
                if save:
                    with open(file_name, "wb") as f:
                        byte = bytes(res['file'], 'utf8')
                        f.write(byte)
                    return res
                else:
                    return res
        else:
            return res
