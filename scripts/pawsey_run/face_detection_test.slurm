#!/bin/sh
#SBATCH -pgpuq
#SBATCH -t 0:10:00
#SBATCH --gres=gpu:4
#SBATCH --account=interns2017
#SBATCH --export=NONE
#SBATCH --output=face_detection_test.out
module load maali
STORE="store.h5" && python3 augment detect_faces -q -s 100 -d -f 