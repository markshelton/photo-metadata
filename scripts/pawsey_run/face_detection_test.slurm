#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=log.out

#architecture
module use /group/interns2017/mcytowski/software/sles12sp2/modulefiles/
module load broadwell gcc/5.4.0 cuda/8.0.61
module load python/2.7.1

#c libraries
module load opencv-gpu
module load dlib-gpu
module load tensorflow
module load hdf5
module load cython

#python libraries
module load pandas
module load setuptools
module load pip

#library install
if cd thickshake; then git pull; else git clone https://github.com/markshelton/thickshake && cd thickshake; fi
python setup.py install --user

#env variables
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
export STORE="store.h5"

INPUT_IMAGES_DIR="../../images/JPEG_Convert_OriginalSize"
OUTPUT_IMAGES_DIR="images"

#script
python thickshake augment detect_faces -q -s 100 -f -ii $INPUT_IMAGES_DIR -oi $OUTPUT_IMAGES_DIR