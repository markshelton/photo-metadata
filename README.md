# Thickshake

Thickshake is a Python package for improving your library catalogue.

It contains functions to assist with:

* metadata extraction from MARC-based library photo archives
* image processing using pre-trained neural networks (e.g. face detection)
* machine learning pipelines based on image features and library metadata

## Installation

Install Docker on your machine as described in the [Docker documentation](http://docs.docker.com/engine/installation/).

```bash
git clone https://github.com/markshelton/thickshake
cd thickshake
make start ENV=dev && rm -ri src docs # development
make start ENV=prod # production
```

## System Design

![System design flowchart](/docs/assets/system_overview.png)

## Usage (Note: WIP)

```python
import thickshake

# Convert metadata files from one format to another
# e.g. MARCXML -> SQL Dump, MARC21 -> HDF5
thickshake.convert_metadata_format(input_file, output_file)

# Apply an image processing technique
# (usually involving a pre-trained neural net)
thickshake.process_image(image_file, method=thickshake.DETECT_FACES)

# Train and apply a machine learning classifier
clf = thickshake.fit_model(image_dir, metadata_file, label="subject_name")
clf.predict(image_file, metadata_file)

# Apply metadata parsing and image processing techniques
# to add to or improve metadata e.g. subject name, gps coordinates
thickshake.augment_metadata(image_dir, metadata_file, output_file)
```

## Docker

Docker-Compose contains:

App Container (Image: [markshelton/thickshake](https://hub.docker.com/r/markshelton/thickshake/))

* Python 3.5
* Tensorflow 1.4.0
* OpenCV 3.3.1
* dlib 19.7

Database Container (Image: [postgres](https://hub.docker.com/_/postgres/))

* PostgreSQL 10.1

Make commands:

```bash
make start # loads and builds images, creates data volume, creates virtual network, opens shell
make stop # saves python environment, stops containers, removes virtual network
make restart # stops and restarts containers and virtual network
make jupyter # opens jupyter service in default internet browser
make shell # opens interactive session with app container
make push # tags app image and pushes image to DockerHub
```

## Contributing

Pull requests are welcome.

## License

To be determined.
