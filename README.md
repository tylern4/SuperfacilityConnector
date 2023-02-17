

### Superfacility Connector

Connector to the SuperfaclityAPI in python with a command line program.

Install with `pip install SuperfacilityConnector`.

### Functions without keys

```
$ sfapi status cori | jq

[
  {
    "full_name": "Cori",
    "description": "System is active",
    "status": "active",
    "updated_at": "2022-04-14T23:03:00-07:00"
  }
]
```

To get the status of all systems use.

```
$ sfapi status all
```


### Functions with read-only keys

The `sfapi` command line looks for keys in `$HOME/.superfacility` in the format of `.pem`. Save the private key as `clientid.pem` where clienid is the client id given from iris (i.e. `mqyqtld6l6roq.pem`). 

To have the sfapi help manage keys you can use,

```
sfapi manage-keys --client home
```

Which will give insructions on how to obtain a key and save the key in the right format to be used later.


List the roles associated with the clientid.

```
sfapi roles
```

List the projects associated with the clientid, including NERSC hours.

```
sfapi projects
```

Execute the `ls` command on the remote site.

```
sfapi ls SITE --path /path/at/nersc
```


### Functions with read-write keys

Submit a job to a site, either with a file already on the system or with a file on your own system. Returns the jobid associated with the newly created job.

```
sfapi sbatch SITE --path /path/at/nersc/slurm.sh 
sfapi sbatch SITE --local slurm.sh
```

View the queue, can view the full queue for a system or by specifc user or job.

```
sfapi squeue SITE 
sfapi squeue SITE --jobid JOBID 
sfapi squeue SITE --user NERSC_USERNAME
```

Used to cancel a job based on the jobid.

```
sfapi scancel SITE --jobid JOBID 
```
