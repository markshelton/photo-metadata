#!/bin/bash --login 
#SBATCH --partition=gpuq 
#SBATCH --nodes=1 
#SBATCH --ntasks-per-node=1 
#SBATCH --gres=gpu:4 
#SBATCH --constraint=p100 
#SBATCH --time=01:00:00 
#SBATCH --account=interns2017 
#SBATCH --export=NONE
module load maali
maali -t tensorflow -v 1.4.0 -d
