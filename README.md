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
make start ENV=dev # development
make start ENV=prod # production
```

## System Design

![System design flowchart](/docs/assets/system_overview.png)

## Usage

Commands:

```sh
thickshake load # Imports a catalogue file into the database (MARC, XML, JSON).

thickshake augment caption_images # Automatically captions images. [TODO]
thickshake augment detect_faces # Detects faces in images.
thickshake augment identify_faces # Identifies faces in images. [TODO]
thickshake augment read_text # Reads text embedded in images. [WIP]
thickshake augment parse_dates # Parses dates from text fields.
thickshake augment parse_links # Parses links from text fields.
thickshake augment parse_locations # Parses locations from text fields.
thickshake augment parse_sizes # Parses image sizes from urls.
thickshake augment run_all # Runs all augment functions.
thickshake augment run_parsers # Runs all metadata parsing functions.
thickshake augment run_processors # Runs all image processing functions.

thickshake export dump # Exports a report / flat file from the database (CSV, JSON).
thickshake export marc # Exports a catalogue file from the database(MARC, XML, JSON). [WIP]
thickshake export query # Exports the results of a SQL query from the database (CSV, JSON).

thickshake inspect # Inspects the state of the database (lists tables and number of records).
thickshake convert # Converts a catalogue file between formats (MARC, XML, JSON).

thickshake show copyright # Show GNU LGPL3 copying permission statement.
thickshake show license # Show full GNU LGPL3 license.
thickshake show readme # Show Thickshake Readme document.
thickshake show warranty # Show GNU LGPL3 warranty statement.
```

Shared Options:

* "-f", "--force", help="overwrite existing files"
* "-d", "--dry-run", help="run without writing files"
* "-g", "--graphics", help="display images in GUI"
* "-s", "--sample", help="perform on random sample (default: 0 / None)"
* "-v", "--verbosity", help="either CRITICAL, ERROR, WARNING, INFO or DEBUG"

## Docker

Docker-Compose contains:

App Container (Image: [markshelton/thickshake](https://hub.docker.com/r/markshelton/thickshake/))

* Python 3.5
* Tensorflow 1.4.0
* OpenCV 3.3.1
* dlib 19.7

Database Container (Image: [postgres](https://hub.docker.com/_/postgres/))

* PostgreSQL 10.1

Database Manager Container (Image: [thajeztah/pgadmin4](https://hub.docker.com/r/thajeztah/pgadmin4/))

* pgAdmin 4

Make commands:

```bash
make start # loads and builds images, creates data volume, creates virtual network, opens shell
make stop # saves python environment, stops containers, removes virtual network
make restart # stops and restarts containers and virtual network
make notebook # opens jupyter service in default internet browser
make dashboard # opens pgadmin dashboard in default internet browser
make shell # opens interactive session with app container
make push # tags app image and pushes image to DockerHub
```

Troubleshooting:

* pgAdmin: Add New Server
  * Hostname: docker inspect thickshake_db -f '{{.NetworkSettings.Networks.compose_default.Gateway}}'
  * Username / Password: docker inspect thickshake_db -f '{{.Config.Env}}'
* Volume not mounting properly (Windows)
  * powershell > Set-NetConnectionProfile -InterfaceAlias "vEthernet (DockerNAT)" -NetworkCategory Private

## Contributing

Pull requests are welcome.

## License

To be determined.
