permissions_warning = """
This may be caused by a permissions error.

Check in iris that your key is correct and still active.

iris.nersc.gov > Profile > Superfacility API Clients
"""

no_client = """
Make sure you provided your client ID and private key properly.

sfapi = SuperfacilityAPI(client_id, private_key)
"""

warning_fourOfour = """
#############################
404 Error. Webpage not found!

{}

#############################
"""


class FourOfourException(Exception):
    pass


class NoClientException(Exception):
    pass


class PermissionsException(Exception):
    pass
