#!/usr/bin/bash

virtualenv -p python venv
venv/bin/pip install --upgrade pip

# Install numpy manually since pip fucks up some dependencies
venv/bin/python setup.py develop
