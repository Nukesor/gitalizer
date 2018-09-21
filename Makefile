.PHONY: default, dev-install, upload

default: dev-install

setup:
	virtualenv -p python venv
	venv/bin/pip install --upgrade pip
	venv/bin/python setup.py develop

dev-install:
	python setup.py develop

clean:
	rm -rf dist
	rm -rf build
	rm -rf pueue.egg-info

dist:
	python setup.py sdist --formats=gztar,zip

upload: clean dist
	twine upload dist/*
