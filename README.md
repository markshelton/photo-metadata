# Thickshake

Thickshake is a Python library for historical image classification.

It contains functions to assist with:

* metadata extraction from MARC-based library photo archives
* face detection, normalisation, and encoding of historical photos
* identification of subjects in images using machine learning

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
* Tensorflow 1.4.0
* OpenCV 3.3.1
* dlib 19.7

Make commands:

```bash
make start # loads container, launches jupyter in browser, opens container shell in terminal
make stop # saves pip environment, stops container
make restart # stops and starts container
```

## Contributing

Pull requests are welcome.

## License

To be determined.
