# A WIP manylinux_2_24 build environment for building BounceRL wheels.
# The c/c++ libs build, but I haven't started the Python side yet.

# Debian 9 (stretch)
FROM quay.io/pypa/manylinux_2_24_x86_64

# Set up debian archive mirrors since Stretch is EOL
RUN echo "deb [trusted=yes] http://archive.debian.org/debian/ stretch main non-free contrib" > /etc/apt/sources.list
RUN echo "deb-src [trusted=yes] http://archive.debian.org/debian/ stretch main non-free contrib" >> /etc/apt/sources.list
RUN echo "deb [trusted=yes] http://archive.debian.org/debian-security/ stretch/updates main non-free contrib" >> /etc/apt/sources.list

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

# Set up per-version python environments
COPY install_python_envs.sh /home/user/bounce_rl/
RUN /home/user/bounce_rl/install_python_envs.sh

# Copy over the repo
COPY --chown=user:user ./ /home/user/bounce_rl/ 
