# Historical Image Classification

## Environment Preparation

### Setup Docker Container

Requirements: Python3, Tensorflow, OpenCv, Jupyter
Exposes 8888 for Jupyter, 6006 for Tensorboard

```powershell
Set-NetConnectionProfile -InterfaceAlias "vEthernet (DockerNAT)" -NetworkCategory Private
```

```bash
docker pull so77id/tensorflow-opencv-cpu-py3:latest
docker run -it --name slwa \
 -p 8888:8888 -p 6006:6006 \
 -v /c/Users/mark/Development/photo-metadata/src:/src \
 so77id/tensorflow-opencv-cpu-py3:latest \
 bash
jupyter notebook /src/notebooks --allow-root
docker start -i slwa
```

TODO: Setup DockerFile - multi-stage build
https://blog.onebar.io/reducing-docker-image-size-using-multi-stage-build-4ec8ee111aae

### Start Running on Pawsey Supercomputers

Granted access to Magnus, Athena and Zeus

TODO: Getting Face extraction to work on Pawsey / high-res

TODO: Setup Tensorflow on Pawsey
https://support.pawsey.org.au/documentation/display/US/Tensorflow

```bash
wget http://developer.download.nvidia.com/compute/redist/cudnn/v6.0/cudnn-8.0-linux-x64-v6.0.tgz $MYGROUP/software/sles12sp2/src
module load maali
maali -t bazel -v 0.8.0 -d
maali -t tensorflow -v 1.4.0 -d
```

## Pre-Processing

### Metadata Parsing

MARCXML -> Python 'dict' -> HDF5

http://www.loc.gov/marc/bibliographic/ecbdlist.html - MARC21 bibliographic list - tag definitions (html format)
https://github.com/rism-international/marcxml-tools - Analyse MARCXML file to determine which fields are in dataset
https://github.com/edsu/pymarc - Convert MARCXML to semi-parsed Python 'Record' objects and then to Python dict
[Custom] - Map tags identified by MARCXML-Tools into human-readable keys
https://github.com/h5py/h5py - Load Python dict into HDF5 storage

Config File

* "035$a" : "control_id"
* "041$a" : "language_code"
* "043$a" : "location_code"
* "100$a" : "subject_main_name"
* "100$d" : "subject_main_dates"
* "100$e" : "subject_main_relation"
* "110$a" : "subject_main_company_name"
* "110$e" : "subject_main_company_relation"
* "245$a" : "note_title"
* "260$c" : "date_created"
* "264$c" : "date_created_approx"
* "300$a" : "physical_extent"
* "300$b" : "physical_details"
* "500$a" : "note_general"
* "520$a" : "note_summary"
* "600$a" : "subject_person_name"
* "600$d" : "subject_person_dates"
* "610$a" : "subject_company_name"
* "650$a" : "note_topical_term"
* "650$z" : "location_division"
* "651$a" : "location_name"
* "830$a" : "series_title"
* "830$v" : "series_volume"
* "856$u" : "note_url"
* "856$z" : "note_public"

Flatten

TODO: Flatten nested dictionary into flat file
TODO: Load flat file into HDF5

collection -> image
collection -> subject

image_id | image_attributes | collection_attributes | subject_attributes

### Data Preparation

http://machinelearninguru.com/deep_learning/data_preparation/hdf5/hdf5.html

TODO: Convert images into pixel arrays
TODO: Load pixel arrays into HDF5

## Machine Learning

* Run the image in your input through the convolution/subsampling layers
* Just before your final fully connected (decision) layer, concatenate the other features you have available
* Feed all (pre-processed image and other features) into decision layer.

TODO: Ask SLWA which features they have pre-populated when receiving a collection

### Face Detection

Images -> Face BB -> Face Images
https://docs.opencv.org/3.3.0/d7/d8b/tutorial_py_face_detection.html
