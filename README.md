### Superfacility Connector

Connector to the SuperfaclityAPI in python with a command line program.

Install with `pip install SuperfacilityConnector`.

### Functions without keys

```
$ sfapi status cori

╒════════╤═════════════╤══════════════════╤═══════════════╤═════════╤══════════╤═══════════════════════════╕
│ name   │ full_name   │ description      │ system_type   │ notes   │ status   │ updated_at                │
╞════════╪═════════════╪══════════════════╪═══════════════╪═════════╪══════════╪═══════════════════════════╡
│ cori   │ Cori        │ System is active │ compute       │ []      │ active   │ 2021-12-17T13:00:00-08:00 │
╘════════╧═════════════╧══════════════════╧═══════════════╧═════════╧══════════╧═══════════════════════════╛
```

To get the status of all systems use.

```
$ sfapi status all
```


### Functions with read-only keys

The `sfapi` command line looks for keys in `$HOME/.superfacility` in the format of `.pem`. Save the private key as `clientid.pem` where clienid is the client id given from iris (i.e. `mqyqtld6l6roq.pem`). 

You can also specify a different clientid and location of a pem file with the `--clientid` and `--private` options to `sfapi`.

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
sfapi sbatch SITE --local /path/to/local/slurm.sh
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
