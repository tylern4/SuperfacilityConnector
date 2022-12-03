## SuperfacilityAPI

### __init__
```

SuperfacilityAPI

Parameters
----------
client_id : str, optional
    Client ID obtained from iris, by default None
private_key : str, optional
    Private key obtained from iris, by default None

```

### delete_job
```

Removes job from queue

Parameters
----------
site : str, optional
    Site to remove job from, by default 'cori'
jobid : int, optional
    Jobid to remove, by default None

Returns
-------
Dict

```

### get_jobs
```

Used to get information about slurm jobs on a system

Parameters
----------
site : str, optional
    NERSC site where slurm job is running, by default 'cori'
sacct : bool, optional
    Whether to use sacct[true] or squeue[false], by default True
jobid : int, optional
    Slurm job id to get information for, by default None
user : int, optional
    Username to get information for, by default None

Returns
-------
Dict

```

### groups
```

Get the groups for your accout

Returns
-------
Dict

```

### ls
```

ls comand on a site

Parameters
----------
site : str, optional
    Name of the site you want to ls at, by default 'cori'
remote_path : str, optional
    Path on the system, by default None

Returns
-------
Dict

```

### post_job
```

Adds a new job to the queue

Parameters
----------
site : str, optional
    Site to add job to, by default 'cori'
script : str, optional
    Path or script to call sbatch on, by default None
isPath : bool, optional
    Is the script a path on the site or a file, by default True

Returns
-------
int
    slurm jobid

```

### projects
```

Get information about your projects

Parameters
----------
repo_name : str, optional
    Get information about a specific project, by default None

Returns
-------
Dict

```

### roles
```

Get roles for your account

Returns
-------
Dict

```

### status
```

Gets status of NERSC systems

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

```

### system_names
```

Returns list of all systems at NERSC

Returns
-------
List

```

### tasks
```

Used to get SuperfacilityAPI tasks

Parameters
----------
task_id : int, optional
    SuperfacilityAPI task number, by default None

Returns
-------
Dict

```