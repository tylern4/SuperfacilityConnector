#!/usr/bin/env python3

import click
import json
import logging
from pathlib import Path
from sfapi_client import Client
from sfapi_client.jobs import JobCommand
from sfapi_client.compute import Machine
from sfapi_client.exceptions import SfApiError

NERSC_DEFAULT_COMPUTE = Machine.perlmutter


def click_json(elemets):
    click.echo(json.dumps(elemets, default=str))


def check_file_and_open(file_path: Path):
    ...


@click.group()
@click.option('--client', '-c', default=None,
              help='Client ID for your key. Can be used to specify which key to look for in $HOME/.superfacility.')
@click.option('--debug', '-d', is_flag=True, default=False,
              help='Print debug messages from sfapi and SuperfacilityConnector')
@click.pass_context
def cli(ctx, client=None, clientid=None, debug=False):
    ctx.ensure_object(dict)
    if debug:
        logging.basicConfig(encoding='utf-8', level=logging.DEBUG)
    else:
        logging.basicConfig(encoding='utf-8', level=logging.ERROR)

    ctx.obj['client'] = Client(key=client)


@cli.command()
@click.argument('site', default=NERSC_DEFAULT_COMPUTE)
@click.pass_context
def status(ctx, site):
    client: Client = ctx.obj['client']

    if site in ['compute', 'computes']:
        site = 'perlmutter'
    elif site in ['filesystem', 'filesystems']:
        site = 'dtns,global_homes,global_common,community_filesystem'
    elif site in ['login', 'logins']:
        site = 'perlmutter,jupyter,dtns'

    try:
        if site == 'all':
            ret = client.resources.status()
        else:
            ret = [client.resources.status(site) for site in site.split(",")]

        if isinstance(ret, list):
            elemets = [arg.model_dump() for arg in ret]
        elif isinstance(ret, dict):
            elemets = [arg.model_dump() for _, arg in ret.items()]
        else:
            elemets = ret.model_dump()

        click_json(elemets)
    except SfApiError as err:
        click.echo(f"SfApiError: {type(err).__name__}: {err}")
    except Exception as err:
        click.echo(f"{type(err).__name__}: {err}")


@cli.command()
@click.argument('site', default=NERSC_DEFAULT_COMPUTE)
@click.pass_context
def outages(ctx, site):
    client: Client = ctx.obj['client']

    if site in ['compute', 'computes']:
        site = 'perlmutter'
    elif site in ['filesystem', 'filesystems']:
        site = 'dtns,global_homes,global_common,community_filesystem'
    elif site in ['login', 'logins']:
        site = 'perlmutter,jupyter,dtns'

    try:
        if site == 'all':
            ret = client.resources.planned_outages()
        else:
            ret = [client.resources.planned_outages(site) for site in site.split(",")]

        if isinstance(ret, list):
            elemets = [a.model_dump() for arg in ret for a in arg]
        elif isinstance(ret, dict):
            elemets = [a.model_dump() for _, arg in ret.items() for a in arg]
        else:
            elemets = ret.model_dump()

        click_json(elemets)
    except SfApiError as err:
        click.echo(f"SfApiError: {type(err).__name__}: {err}")
    except Exception as err:
        click.echo(f"{type(err).__name__}: {err}")


@cli.command()
@click.pass_context
def token(ctx):
    client: Client = ctx.obj['client']
    click.echo(client.token)


@cli.command()
@click.pass_context
def whoami(ctx):
    client: Client = ctx.obj['client']
    click_json(client.user().model_dump())


@cli.command()
@click.pass_context
def groups(ctx):
    client: Client = ctx.obj['client']
    user = client.user()
    ret = user.groups()
    elemets = [arg.model_dump() for arg in ret]
    for ele in elemets:
        del ele["client"]
        del ele["users_"]

    click_json(elemets)

# @cli.command()
# @click.argument('site', default=NERSC_DEFAULT_COMPUTE)
# @click.option('--path', '-p', default=None, help='Path to slurm submit file at NERSC.')
# @click.option('--local', '-l', default=None, help='Path to local file to submit.')
# @click.pass_context
# def sbatch(ctx, site, path, local):
#     client: Client = ctx.obj['client']
#     script = None
#     isPath = False

#     if path is not None:
#         isPath = True
#         script = path
#     elif local is not None:
#         script = check_file_and_open(local)


# @cli.command()
# @click.argument('site', default=NERSC_DEFAULT_COMPUTE)
# @click.option('--path', '-p', default=None, help='Path to slurm submit file at NERSC.')
# @click.pass_context
# def ls(ctx, site, path):
#     client: Client = ctx.obj['client']

#     ret = sfapi.ls(site=site, remote_path=path)
#     try:
#         click_json(ret['entries'])
#     except Exception as err:
#         click.echo(f"{type(err).__name__}: {err}")


# @cli.command()
# @click.argument('site', default=NERSC_DEFAULT_COMPUTE)
# @click.option('--path', '-p', default=None, help='Path to slurm submit file at NERSC.')
# @click.pass_context
# def cat(ctx, site, path):
#     client: Client = ctx.obj['client']

#     ret = sfapi.download(site=site, remote_path=path, save=False)
#     logging.debug(ret)

#     try:
#         click.echo_via_pager(ret['file'])
#     except Exception as err:
#         click.echo(f"{type(err).__name__}: {err}")


@cli.command()
@click.argument('site', default=NERSC_DEFAULT_COMPUTE)
@click.option('--user', '-u', default=None, help='User to to get queue info for.')
@click.option('--jobid', '-j', default=None, help='Specific jobid to get queue info for.')
@click.pass_context
def squeue(ctx, site, user, jobid):
    client: Client = ctx.obj['client']
    compute = client.compute(site)

    try:
        ret = compute.jobs(user=user, jobids=jobid, command=JobCommand.sacct)
        if isinstance(ret, list):
            elemets = [arg.model_dump() for arg in ret]
        elif isinstance(ret, dict):
            elemets = [arg.model_dump() for _, arg in ret.items()]

        for ele in elemets:
            del ele['compute']

        click_json(elemets)
    except Exception as err:
        click.echo(f"{type(err).__name__}: {err}")
        exit(1)


# @cli.command()
# @click.argument('site', default=NERSC_DEFAULT_COMPUTE)
# @click.option('--user', '-u', default=None, help='User to to get queue info for.')
# @click.option('--jobid', '-j', default=None, help='Specific jobid to get queue info for.')
# @click.pass_context
# def sqs(ctx, site, user, jobid):
#     client: Client = ctx.obj['client']
#     try:
#         ret = sfapi.sqs(site=site, user=user, jobid=jobid, dataframe=True)
#         click.echo(ret)
#     except Exception as err:
#         click.echo(f"{type(err).__name__}: {err}")
#         exit(1)


# @cli.command()
# @click.argument('jobid')
# @click.argument('site', default=NERSC_DEFAULT_COMPUTE)
# @click.pass_context
# def scancel(ctx, site, jobid):
#     client: Client = ctx.obj['client']
#     logging.info(f"Running delete on {jobid}@{site}")

#     ret = sfapi.delete_job(site=site, jobid=jobid)
#     click.echo(ret)


# @cli.command()
# @click.argument('taskid')
# @click.pass_context
# def task(ctx, taskid):
#     client: Client = ctx.obj['client']
#     # Waits (up to {timeout} seconds) for the job to be submited before returning
#     timeout = 40
#     sleeptime = 1
#     from time import sleep
#     for i in range(timeout):
#         if i > 0:
#             sleep(sleeptime)

#         logging.debug(f"Running {i}")
#         task = sfapi.tasks(task_id=taskid)
#         logging.debug(f"task = {task}")
#         if task is not None and task['status'] == 'completed':
#             jobinfo = json.loads(task['result'])
#             click.echo(
#                 {'error': jobinfo['error'], 'jobid': jobinfo['jobid'], 'task_id': taskid})
#             return


if __name__ == '__main__':
    cli(obj={})
