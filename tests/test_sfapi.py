from SuperfacilityAPI import SuperfacilityAPI


def test_status():
    sfapi = SuperfacilityAPI()
    sfapi.status()


def test_system_names():
    sfapi = SuperfacilityAPI()
    sfapi.system_names()
    sfapi.systems
