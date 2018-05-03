#!/usr/bin/bash

virtualenv -p python venv
venv/bin/pip install --upgrade pip

# Install some libraries manually as pip fucks up dependencies.
venv/bin/pip install cython
venv/bin/pip install geopy

# Install the rest.
venv/bin/pip install -r requirements.txt -r requirements-dev.txt
