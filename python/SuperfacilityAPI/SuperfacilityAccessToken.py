from authlib.integrations.requests_client import (
    OAuth2Session,
    OAuthError
)
from authlib.oauth2.rfc7523 import PrivateKeyJWT
import sys
from datetime import datetime
from pathlib import Path
import requests
import logging
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
        self.__token_lifetime = datetime.now()
        self.__renew_token()

    @staticmethod
    def save_token(tag: str = "sfapi"):
        sfdir = Path.joinpath(Path.home(), ".superfacility")
        sfdir.mkdir(exist_ok=True)

        ipadder = requests.get("https://ifconfig.me/ip")

        # Sorry for the weird one liner!
        O_24 = '.'.join(ipadder.text.split('.')[:-1]) + '.0/24'
        print(iris_instructions.format(O_24))

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
        logging.debug(
            f"Token lifetime {(datetime.now()-self.__token_lifetime).seconds}")
        if ((datetime.now()-self.__token_lifetime).seconds) > 500:
            logging.debug(
                f"Token lifetime {(self.__token_lifetime - datetime.now()).seconds} renewing token")
            self.__renew_token()

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
        token_url = "https://oidc.nersc.gov/c2id/token"
        logging.debug(f"{self.__token_lifetime - datetime.now()}")
        self.__token_lifetime = datetime.now()

        if self.client_id is None:
            logging.debug("Getting client_id from file path")
            cid = self.key_path.stem.split('-')[-1]
        else:
            cid = self.client_id

        logging.debug(f"Getting token for {cid}")

        if self.key_path is not None:
            logging.debug(
                f"Getting private key from file path {self.key_path}")
            pkey = self.__check_file_and_open()
        elif self.private_key is not None:
            pkey = self.private_key
            logging.debug(
                f"Private key provided as string")
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
            logging.debug(
                f"Oauth error {e}\nMake sure your api key is still active in iris.nersc.gov")
            return None
