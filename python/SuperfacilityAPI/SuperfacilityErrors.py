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


class SuperfacilityError(Exception):
    pass


class FourOfourException(SuperfacilityError):
    pass


class InternalServerError(SuperfacilityError):
    pass


class ApiTokenError(SuperfacilityError):
    pass


class NoClientException(SuperfacilityError):
    pass


class PermissionsException(SuperfacilityError):
    pass


class SuperfacilityCmdFailed(SuperfacilityError):
    pass


class SuperfacilitySiteDown(SuperfacilityError):
    pass
