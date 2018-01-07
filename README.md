# Thickshake

Thickshake is a Python library for dealing with historical image classification.

It contains functions to assist with:

* metadata extraction from MARC-based library photo archives
* face detection, normalisation, and encoding from historical photos
* identification of subjects in images via machine learning

## Installation

Install Docker on your machine as described in the [Docker documentation](http://docs.docker.com/engine/installation/).

```bash
git clone https://github.com/markshelton/thickshake
cd thickshake
docker up
```

## Usage

```python
import thickshake
thickshake.detect_subjects(image, image_metadata)
# returns a list of faces and their identities
```

## Docker

Docker image contains:

* Python 3.5
* Tensorflow
* OpenCV
* dlib

Docker commands:

```bash
docker start # loads container, launches jupyter in browser, opens container shell in terminal
docker stop # saves pip environment, stops container
docker restart # stops and starts container
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
