ARG TENSORFLOW_VERSION=1.4.0
ARG OPENCV_VERSION=3.3.1
ARG DLIB_VERSION=19.7

# Tensorflow Base Image
# https://github.com/tensorflow/tensorflow/tree/master/tensorflow/tools/docker
FROM tensorflow/tensorflow:$TENSORFLOW_VERSION-py3

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
    libpq-dev \
    libsm6 \
    libxext6 \
    pkg-config \
    python3 \
    python3-dev \
    python3-numpy \
    python3-pip \
    python3-tk \
    tesseract-ocr \
    wget \
    && rm -rf /var/lib/apt/lists/*

ARG OPENCV_VERSION

# Download OpenCV
WORKDIR /
RUN wget -O opencv.zip https://github.com/Itseez/opencv/archive/${OPENCV_VERSION}.zip \
    && unzip opencv.zip \
    && wget -O opencv_contrib.zip https://github.com/Itseez/opencv_contrib/archive/${OPENCV_VERSION}.zip \
    && unzip opencv_contrib

# Install OpenCV
RUN cd /opencv-${OPENCV_VERSION}/ \
    && mkdir build \
    && cd build \
    && cmake \
    -D CMAKE_BUILD_TYPE=RELEASE \
    -D INSTALL_C_EXAMPLES=OFF \
    -D INSTALL_PYTHON_EXAMPLES=ON \
    -D BUILD_EXAMPLES=OFF \
    -D BUILD_opencv_python2=OFF \
    -D BUILD_opencv_python3=ON \
    -D OPENCV_EXTRA_MODULES_PATH=/opencv_contrib-${OPENCV_VERSION}/modules \
    -D CMAKE_INSTALL_PREFIX=$(python3 -c "import sys; print(sys.prefix)") \
    -D PYTHON_EXECUTABLE=$(which python3) \
    -D WITH_FFMPEG=OFF \
    -D WITH_CUDA=OFF \
    .. \
    && make -j8 \
    && make install \
    && ldconfig \
    && rm /opencv.zip \
    && rm /opencv_contrib.zip \
    && rm -r /opencv-${OPENCV_VERSION} \
    && rm -r /opencv_contrib-${OPENCV_VERSION}

ARG DLIB_VERSION

# Download dlib
RUN wget -O dlib.tar.bz2 http://dlib.net/files/dlib-${DLIB_VERSION}.tar.bz2 \
    && tar -vxjf dlib.tar.bz2

# Install dlib
RUN cd dlib-${DLIB_VERSION} \
    && cd examples \
    && mkdir build \
    && cd build \
    && cmake .. \
    && cmake --build . --config Release \
    && cd /dlib-${DLIB_VERSION} \
    && python3 setup.py install \
    && cd $WORKDIR \
    && rm /dlib.tar.bz2

# Load Python Environment
COPY requirements.txt /home/app/
WORKDIR /home/app
RUN pip3 install -r requirements.txt && python3 -m ipykernel.kernelspec

# Set EnvVars for Python encoding
ENV PYTHONIOENCODING=utf-8
ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Expose Jupyter
EXPOSE 8888 

#Expose Tensorboard
EXPOSE 6006

#Expose Postgresql
EXPOSE 5432

# Start Jupyter Server
CMD ["/run_jupyter.sh", "--allow-root", "--NotebookApp.token=''"]
