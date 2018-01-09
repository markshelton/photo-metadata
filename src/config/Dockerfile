ARG TENSORFLOW_VERSION=1.4.0
ARG OPENCV_VERSION=3.3.1.11
ARG DLIB_VERSION=19.7

# Tensorflow Base Image
# https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/docker
FROM tensorflow/tensorflow:$TENSORFLOW_VERSION-py3

ARG OPENCV_VERSION
ARG DLIB_VERSION

#Download Ubuntu Packages
RUN apt-get update \
    && apt-get install -y \
    build-essential \
    cmake \
    gfortran \
    libatlas-base-dev \
    libboost-all-dev \
    libgtk2.0-dev \
    libjpeg-dev \
    liblapacke-dev \
    libpng-dev \
    libsm6 \
    libxext6 \
    pkg-config \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-tk \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Load Python Environment
COPY config/requirements.txt /home/app/config/
WORKDIR /home/app
RUN pip3 install --no-cache-dir \
    ipykernel \
    jupyter \
    matplotlib \
    opencv-python==$OPENCV_VERSION \
    opencv-contrib-python==$OPENCV_VERSION \
    dlib==$DLIB_VERSION \
    && python3 -m ipykernel.kernelspec
RUN pip3 install --no-cache-dir -r config/requirements.txt

#Copy over Thickshake Library
COPY lib/ /lib/thickshake/
ENV PYTHONPATH $PYTHONPATH:/lib/thickshake

# Expose Jupyter
EXPOSE 8888 

#Expose Tensorboard
EXPOSE 6006

# Start Jupyter Server
CMD ["/run_jupyter.sh", "--allow-root", "--NotebookApp.token=''"]