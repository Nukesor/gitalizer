.PHONY: default, dev-install, upload

default: dev-install

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
