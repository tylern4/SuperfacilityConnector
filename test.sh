#!/bin/bash
#SBATCH -N 1
#SBATCH -C haswell
#SBATCH -A nstaff
#SBATCH -J test_cori
#SBATCH --time=00:01:00

echo $HOSTNAME
