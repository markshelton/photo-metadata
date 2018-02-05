#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=log.out

module load broadwell gcc/4.8.5 cuda

module load python/3.6.1

module load opencv-gpu # compiled with gcc/4.8.5 ??
module load dlib-gpu # compiled with gcc/5.4.0 ??
module load tensorflow # resets PYTHON_VERSION to 2.7.1 ??
module load hdf5
module load cython

module load pandas
#module load numpy
#module load setuptools
module load pip

#commands
if cd thickshake; then git pull; else git clone https://github.com/markshelton/thickshake && cd thickshake; fi
python3 setup.py install --user # install dependencies
pip3 install --user -e . # install local package
export LC_ALL=C.UTF-8 && export LANG=C.UTF-8 # python language encoding
STORE="store.h5" && python3 thickshake augment detect_faces -q -s 100 -d -f #script
