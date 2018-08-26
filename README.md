# Gitalizer

This program is a combination of a Github data aggregator and a basic analysis tool.
The purpose of this program is to show the possible dangers of performing data mining on git meta data.

This program is not written to be used in a malicious way! Please just don't do it.
I rather want people to understand, that somebody else might use it this way and that they might even be already doing it.

The original idea was to add a web interface on top of everything, but there wasn't enough time in the scope of my thesis for this.


## Installation:

- Make sure you have Python 3.6 and `virtualenv` installed
- Run the `bin/setup.sh` script.
- Install following packages. They are required for various analysis or visualizations:
    1. proj
    2. geos
    3. agg

- Setup PostgreSQL and create a database
- Copy the `./gitalizer/example-config.py` to `./gitalizer/config.py` and adjust all parameters to your needs.

## Run stuff

If you want to run commands from the commandlines, execute `source ./venv/bin/activate`.
These commands let you enter the virtual environment.

Afterwards you can check what commands are available with simply executing `gitalizer`.
