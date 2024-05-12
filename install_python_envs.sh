ORIG_PATH="${PATH}"

# TODO: Support python 3.12
for PYTHON_VERSION in 38 39 310 311; do
    echo "Installing python ${PYTHON_VERSION} environment"
    export PATH="/opt/python/cp${PYTHON_VERSION}-cp${PYTHON_VERSION}/bin:${ORIG_PATH}"

    hash -r
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath --force
    pipx install poetry==1.8

    # Install python requirements
    export PIP_DISABLE_PIP_VERSION_CHECK=1
    export PIP_ROOT_USER_ACTION=ignore
    pip install wheel meson ninja twine
done
