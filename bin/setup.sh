#!/usr/bin/bash

pacman -S proj

virtualenv -p python venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt -r requirements-dev.txt
