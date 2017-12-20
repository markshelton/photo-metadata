#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 8:00:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
module load maali
srun --export=ALL maali -t opencv -v 3.3.1 -n -d