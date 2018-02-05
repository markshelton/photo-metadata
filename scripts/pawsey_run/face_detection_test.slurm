#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=face_detection_test.out

module load broadwell gcc/5.4.0 cuda

module swap python python/3.6.1

module load opencv-gpu
module load dlib-gpu
module load tensorflow
module load hdf5
module load cython

module load pandas
module load numpy
module load setuptools
module load pip

unset PYTHONPATH
if cd thickshake; then git pull; else git clone https://github.com/markshelton/thickshake && cd thickshake; fi
STORE="store.h5" && python3 thickshake augment detect_faces -q -s 100 -d -f 
