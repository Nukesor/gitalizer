"""This file's sole purpose is constructing an `app` object from the factory function."""

import os
from gitalizer import create_app
app = create_app(os.environ.get('GITALIZER_CONFIG', 'develop'))
