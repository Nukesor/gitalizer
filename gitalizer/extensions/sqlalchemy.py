"""Sqlalchemy helper."""
import functools
import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.ext.declarative import declarative_base


class DB(object):
    """Create an engine for easy session creation."""

    def __init__(self, config):
        """Lazy initializer which takes an `app` and sets up sentry."""
        self.engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
        self.Model = declarative_base(bind=self.engine)

        query_class = Query
        # Inject sqlalchemy into db helper class
        for module in sqlalchemy, sqlalchemy.orm:
            for key in module.__all__:
                if not hasattr(self, key):
                    setattr(self, key, getattr(module, key))
        # Note: self.Table does not attempt to be a SQLAlchemy Table class.
        self.Table = _make_table(self)
        self.relationship = _wrap_with_default_query_class(self.relationship, query_class)
        self.relation = _wrap_with_default_query_class(self.relation, query_class)
        self.dynamic_loader = _wrap_with_default_query_class(self.dynamic_loader, query_class)

    @property
    def session(self):
        """Short handle for getting a session.

        Also needed for backwards compatibility during refactoring.
        """
        return self.get_session()

    def get_session(self):
        """Create a new session."""
        session = sessionmaker(bind=self.engine)()
        return session

#    def Table(self, *args, **kwargs):
#        """Creating a sqlalchemy table with the current db metadata."""
#        if len(args) > 1 and isinstance(args[1], self.Column):
#            args = (args[0], self.Model.metadata) + args[1:]
#        info = kwargs.pop('info', None) or {}
#        info.setdefault('bind_key', None)
#        kwargs['info'] = info
#        return sqlalchemy.Table(*args, **kwargs)


def _set_default_query_class(d, query_class):
    if 'query_class' not in d:
        d['query_class'] = query_class


def _wrap_with_default_query_class(fn, query_class):
    @functools.wraps(fn)
    def newfn(*args, **kwargs):
        _set_default_query_class(kwargs, query_class)
        if "backref" in kwargs:
            backref = kwargs['backref']
            if isinstance(backref, str):
                backref = (backref, {})
            _set_default_query_class(backref[1], query_class)
        return fn(*args, **kwargs)
    return newfn


def _make_table(db):
    def _make_table(*args, **kwargs):
        if len(args) > 1 and isinstance(args[1], db.Column):
            args = (args[0], db.Model.metadata) + args[1:]
        info = kwargs.pop('info', None) or {}
        info.setdefault('bind_key', None)
        kwargs['info'] = info
        return sqlalchemy.Table(*args, **kwargs)
    return _make_table
