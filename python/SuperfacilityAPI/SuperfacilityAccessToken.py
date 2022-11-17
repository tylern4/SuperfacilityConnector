from authlib.integrations.requests_client import (
    OAuth2Session,
    OAuthError
)
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import sys
from datetime import datetime
from pathlib import Path
import requests
import getpass
import json
import os


iris_instructions = """
Go to https://iris.nersc.gov

Click `Profile`

Scroll to `Superfacility API Clients`

`+ New Client`

Copy the private key.

Your current IP address is {}
"""


class SuperfacilityAccessToken:
    client_id = None
    private_key = None
    key_path = None
    session = None

    def __init__(self, name: str = None,
                 client_id: str = None,
                 private_key: str = None,
                 key_path: str = None):
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
            if name is not None:
                self.key_path = list(Path.joinpath(
                    Path.home(), ".superfacility").glob(f"{name}*.pem"))[0]
            elif client_id is not None:
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

    @staticmethod
    def save_token(key_format: str = 'json', tag: str = "sfapi"):
        sfdir = Path.joinpath(Path.home(), ".superfacility")
        sfdir.mkdir(exist_ok=True)

        ipadder = requests.get("https://ifconfig.io/ip")
        print(iris_instructions.format(ipadder.text))

        client_id = input("Enter client id: ")
        key_name = sfdir / f"{tag}-{client_id}.pem"
        editor = os.getenv("EDITOR", "vim")
        os.system(f'{editor} {key_name}')
        try:
            key_name.chmod(0o600)
        except FileNotFoundError:
            print("No key info entered")

    @property
    def token(self):
        if self.session is not None:
            self.access_token = self.session.fetch_token()['access_token']

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
            cid = self.key_path.stem.split('-')[-1]

        if self.key_path is not None:
            pkey = self.__check_file_and_open()
        elif self.private_key is not None:
            pkey = self.private_key
        else:
            # If no private key don't look for getting a token
            return None

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
            return None
