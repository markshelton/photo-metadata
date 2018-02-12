#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=log.out

# modules install
module use /group/interns2017/mcytowski/software/sles12sp2/modulefiles/ #local install path
module load broadwell gcc/5.4.0 cuda/8.0.61 python/2.7.1 #architecture
module load opencv-gpu dlib-gpu tensorflow hdf5 cython #c libraries
module load pandas setuptools pip #python libraries

#module fixes
export PYTHONPATH=$(p=$(echo $PYTHONPATH | tr ":" "\n" | grep -v "/3.6.1/" | tr "\n" ":"); echo ${p%:}) #numpy/pandas fix
export PYTHONPATH=$PYTHONPATH:/group/interns2017/mcytowski/software/sles12sp2/apps/broadwell/gcc/5.4.0/cuda/8.0.61/opencv-gpu/3.3.1/lib/python2.7/site-packages #opencv fix

#library install
if cd thickshake; then git pull; else git clone https://github.com/markshelton/thickshake && cd thickshake; fi
python setup.py install --user

#env variables
export LC_ALL=C.UTF-8 && export LANG=C.UTF-8
export STORE="data/output/store.h5"

#flags
INPUT_IMAGES_DIR="../../images/JPEG_Convert_OriginalSize"
OUTPUT_IMAGES_DIR="data/output/images"

#script
python -m thickshake augment detect_faces -q -s 100 -f -ii $INPUT_IMAGES_DIR -oi $OUTPUT_IMAGES_DIR