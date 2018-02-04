#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=face_detection_test.out

module use /group/interns2017/software/sles12sp2/modulefiles
module load broadwell cuda gcc/5.4.0
module load python/3.6.1
module load dlib-gpu
module load tensorflow
module load opencv-gpu
module load keras
module load hdf5

STORE="store.h5" && python augment detect_faces -q -s 100 -d -f 