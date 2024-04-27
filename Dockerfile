# A WIP manylinux_2_24 build environment for building BounceRL wheels.
# The c/c++ libs build, but I haven't started the Python side yet.

# Debian 9 (stretch)
FROM quay.io/pypa/manylinux_2_24_x86_64

# Set up debian archive mirrors since Stretch is EOL
RUN echo "deb [trusted=yes] http://archive.debian.org/debian/ stretch main non-free contrib" > /etc/apt/sources.list
RUN echo "deb-src [trusted=yes] http://archive.debian.org/debian/ stretch main non-free contrib" >> /etc/apt/sources.list
RUN echo "deb [trusted=yes] http://archive.debian.org/debian-security/ stretch/updates main non-free contrib" >> /etc/apt/sources.list

# Default to python 3.10
ENV PYTHON_VERSION=310
ENV PATH="/opt/python/cp${PYTHON_VERSION}-cp${PYTHON_VERSION}/bin:${PATH}"
RUN hash -r

# Install system dependencies:
# - XTest + multilib for c/c++ builds
RUN apt-get update && apt-get install -y libxtst-dev \
      gcc-multilib \
      g++-multilib

# Set up user and project directory
RUN useradd -ms /bin/bash user
USER user
RUN mkdir /home/user/bounce_rl
WORKDIR /home/user/bounce_rl
ENV PATH="/home/user/.local/bin:${PATH}"

# Install pipx and poetry
RUN python3 -m pip install --user pipx
RUN python3 -m pipx ensurepath --force
RUN pipx install poetry==1.8

# Install python requirements
COPY requirements.txt /home/user/bounce_rl/requirements.txt
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PIP_ROOT_USER_ACTION=ignore
RUN pip install wheel meson ninja twine
RUN pip install -r requirements.txt

# Copy over the repo
COPY --chown=user:user ./ /home/user/bounce_rl/ 
