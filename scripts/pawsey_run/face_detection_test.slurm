#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=face_detection_test.out

module load broadwell cuda

module load python/3.6.1

module load opencv-gpu
module load dlib-gpu
module load tensorflow
module load hdf5
module load cython

module load pandas
module load numpy
module load pip

unset PYTHONPATH
if cd thickshake; then git pull; else git clone https://github.com/markshelton/thickshake && cd thickshake; fi
pip install virtualenv && virtualenv venv && source venv/bin/activate
python setup.py develop
STORE="store.h5" && python3 thickshake augment detect_faces -q -s 100 -d -f 