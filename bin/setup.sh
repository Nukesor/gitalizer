#!/usr/bin/bash

virtualenv -p python venv
venv/bin/pip install --upgrade pip

# Install numpy manually since pip fucks up some dependencies
venv/bin/pip install numpy

# Install the rest.
venv/bin/pip install -r requirements.txt -r requirements-dev.txt
