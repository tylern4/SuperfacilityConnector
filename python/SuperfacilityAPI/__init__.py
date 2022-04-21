
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


class SuperfacilityAccessToken:
    client_id = None
    private_key = None
    key_path = None
    session = None

    def __init__(self, client_id: str = None, private_key: str = None, key_path: str = None):
        """SuperfacilityAPI

        Parameters
        ----------
        client_id : str, optional
            Client ID obtained from iris, by default None
        private_key : str, optional
            Private key obtained from iris, by default None
        """
        # TODO: Check a better way to store these, esspecially private key
        if client_id is not None and private_key is not None:
            self.client_id = client_id
            self.private_key = private_key
        elif key_path is not None and Path(key_path).exists():
            self.key_path = key_path
        elif Path.joinpath(Path.home(), ".superfacility").exists():
            if client_id is not None:
                self.client_id = client_id
                self.key_path = Path.joinpath(
                    Path.home(), f".superfacility/{client_id}.pem")
            else:
                self.key_path = list(Path.joinpath(
                    Path.home(), ".superfacility").glob("*.pem"))[0]

        # Create an access token in the __renew_toekn function
        self.access_token = None
        self.__renew_token()

        # Set the status at the begining to none,
        # If status is called later it will be stored here
        # for faster calls later
        self._status = None

    @property
    def token(self):
        # If key is older than 5 minutes renew
        if self.access_token is not None and (datetime.now() - self.__token_time).seconds > (5*60):
            self.__renew_token()

        return self.access_token

    def __check_file_and_open(self) -> str:
        contents = None
        if self.key_path.is_file():
            with open(self.key_path.absolute()) as f:
                contents = f.read()
        return contents

    def __renew_token(self):
        # Create access token from client_id/private_key
        self.__token_time = datetime.now()

        token_url = "https://oidc.nersc.gov/c2id/token"

        if self.client_id is not None:
            cid = self.client_id
        else:
            cid = str(self.key_path).split("/")[-1][:-4]

        if self.key_path is not None:
            pkey = self.__check_file_and_open()
        elif self.private_key is not None:
            pkey = self.private_key
        else:
            # If no private key don't look for getting a token
            return

        self.session = OAuth2Session(
            cid,  # client_id
            pkey,  # client_secret
            PrivateKeyJWT(token_url),  # authorization_endpoint
            grant_type="client_credentials",
            token_endpoint=token_url  # token_endpoint
        )
        # Get's the access token
        try:
            self.access_token = self.session.fetch_token()['access_token']
        except OAuthError as e:
            print(
                f"Oauth error {e}\nMake sure your api key is still active in iris.nersc.gov", file=sys.stderr)
            exit(2)


class SuperfacilityAPI:
    _status = None

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

    def __generic_post(self, sub_url: str, header: Dict = None, data: str = None) -> Dict:
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
                data="" if data is None else data)
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

    def projects(self, token: str = None, repo_name: str = None) -> Dict:
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
        if repo_name is not None:
            sub_url = f'/account/projects/{repo_name}/jobs'

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

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
                jobid: int = None, user: int = None) -> Dict:
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

        if isinstance(token, str):
            self.access_token = token
            self.headers['Authorization'] = f'Bearer {self.access_token}'

        return self.__generic_request(sub_url)

    def post_job(self, token: str = None, site: str = NERSC_DEFAULT_COMPUTE, script: str = None, isPath: bool = True) -> int:
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

        resp = self.__generic_post(
            sub_url, data=f'job={script}&isPath={is_path}')
        task_id = resp['task_id']
        logging.debug("Submitted new job, wating for responce.")
        if resp == None:
            return {'jobid': "post returned none"}
        # Waits (up to 10 seconds) for the job to be submited before returning
        for _ in range(10):
            task = self.tasks(self.access_token, resp['task_id'])
            if task['status'] == 'completed':
                return json.loads(task['result'])
            sleep(1)

        # Gives back error if something went wrong
        task = self.tasks(self.access_token, resp['task_id'])
        ret = json.loads(task['result'])
        ret['task_id'] = task_id
        return ret

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
