#!/bin/bash --login
#SBATCH --job-name=tf_test
#SBATCH --partition=gpuq
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=1
#SBATCH --gres=gpu:4
#SBATCH --constraint=p100
#SBATCH --time=00:10:00
#SBATCH --account=interns2017
#SBATCH --export=NONE

module load gcc/5.4.0 broadwell
module load tensorflow

srun --export=ALL python tf_cnn_benchmarks/tf_cnn_benchmarks.py --num_gpus=4 --batch_size=64 --model=resnet50 --variable_update=parameter_server
