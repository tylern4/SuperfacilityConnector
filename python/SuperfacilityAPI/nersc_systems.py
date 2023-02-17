from enum import Enum, EnumMeta


nersc_systems = ['perlmutter', 'cori', 'dna', 'dtns', 'global_homes', 'projectb', 'global_common',
                 'community_filesystem', 'matlab', 'jupyter', 'nersc_center', 'helpportal', 'website',
                 'rstudio', 'sgns', 'network', 'ldap', 'integ_datalanguage', 'mathematica', 'globus',
                 'spin', 'jgi_int_webservers', 'jgidb', 'int', 'webservers', 'iris', 'sciencedatabases',
                 'myproxy', 'newt', 'ssh-proxy', 'mongodb', 'nomachine', 'regent', 'archive']

# https://stackoverflow.com/a/62854511


class MyEnumMeta(EnumMeta):
    def __contains__(cls, item):
        return item in cls.__members__.values()


class NerscCompute(str, Enum, metaclass=MyEnumMeta):
    CORI = 'cori'
    PERLMUTTER = 'perlmutter'
    MULLER = 'muller'


class NerscFilesystems(str, Enum, metaclass=MyEnumMeta):
    DNA = 'dna'
    DTN = 'dtns'
    HOME = 'global_homes'
    GLOBAL_COMMON = 'global_common'
    CFS = 'community_filesystem'


NERSC_DEFAULT_COMPUTE = NerscCompute.PERLMUTTER
