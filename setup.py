"""Setuptools file for gitalizer."""
from setuptools import setup, find_packages

setup(
    name='gitalizer',
    author='Arne Beer',
    author_email='privat@arne.beer',
    version='0.1.0',
    description='A git/github repository data collector for Git to analyse privacy implications of exposing Git metadata',
    keywords='git aggregator metadata github',
    url='http://github.com/nukesor/gitalizer',
    license='MIT',
    install_requires=[
        # Base
        'alembic~=0.8',
        'SQLAlchemy~=1.1.4',
        'sqlalchemy-utils~=0.32',
        'psycopg2-binary',

        # Aggregator
        'pygithub~=1.35',
        'pygit2~=0.27',
        'gitpython~=2.1',
        'pytz~=2018.3',

        # Logging
        'raven',

        # Time handling
        'pendulum~=1.4',
        'pytzdata~=2018.3',

        # Location handling
        'geopy',
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Environment :: Console',
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'gitalizer=gitalizer:cli',
        ],
    })
