#!/bin/bash
#SBATCH -N 1
#SBATCH -C cpu
#SBATCH -A nstaff
#SBATCH -J sfapi_test
#SBATCH --qos=debug
#SBATCH --time=00:01:00

echo $HOSTNAME
