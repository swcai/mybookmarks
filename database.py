#!/usr/bin/env python
#
# Modified and simplified from Tornado project

"""A lightweight wrapper around sqlite3."""

import copy
import sqlite3
import itertools
import logging
import time
import unittest

# TODO fix ERROR number
class Connection(object):
    """A lightweight wrapper around Sqlite3 DB-API connections.

    The main value we provide is wrapping rows in a dict/object so that
    columns can be accessed by name. Typical usage:

        db = database.Connection("mydatabase")
        for article in db.query("SELECT * FROM articles"):
            print article.title

    Cursors are hidden by the implementation, but other than that, the methods
    are very similar to the DB-API.

    We explicitly set the timezone to UTC and the character encoding to
    UTF-8 on all connections to avoid time zone and encoding errors.
    """
    def __init__(self, database):
        self.database = database
        self._db = None
        self._last_use_time = time.time()
        try:
            self.reconnect()
        except:
            logging.error("Cannot connect to sqlite3 (%s)", self.database,
                          exc_info=True)

    def __del__(self):
        self.close()

    def close(self):
        """Closes this database connection."""
        if getattr(self, "_db", None) is not None:
            self._db.close()
            self._db = None

    def reconnect(self):
        """Closes the existing database connection and re-opens it."""
        self.close()
        self._db = sqlite3.connect(self.database)

    def commit(self):
        if self._db is not None:
            self._db.commit()
            
    def iter(self, query, *parameters):
        """Returns an iterator for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            for row in cursor:
                yield Row(zip(column_names, row))
        finally:
            cursor.close()

    def query(self, query, *parameters):
        """Returns a row list for the given query and parameters."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            column_names = [d[0] for d in cursor.description]
            return [Row(itertools.izip(column_names, row)) for row in cursor]
        finally:
            cursor.close()

    def get(self, query, *parameters):
        """Returns the first row returned for the given query."""
        rows = self.query(query, *parameters)
        if not rows:
            return None
        elif len(rows) > 1:
            raise Exception("Multiple rows returned for Database.get() query")
        else:
            return rows[0]

    def execute(self, query, *parameters):
        """Executes the given query, returning the lastrowid from the query."""
        cursor = self._cursor()
        try:
            self._execute(cursor, query, parameters)
            return cursor.lastrowid
        finally:
            cursor.close()

    def executemany(self, query, parameters):
        """Executes the given query against all the given param sequences.

        We return the lastrowid from the query.
        """
        cursor = self._cursor()
        try:
            cursor.executemany(query, parameters)
            return cursor.lastrowid
        finally:
            cursor.close()

    def _cursor(self):
        return self._db.cursor()

    def _execute(self, cursor, query, parameters):
        try:
            return cursor.execute(query, parameters)
        except OperationalError:
            logging.error("Error connecting to Sqlite3 (%s)", self.database)
            raise

class Row(dict):
    """A dict that allows for object-like property access syntax."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

# Alias some common SQLITE3 exceptions
IntegrityError = sqlite3.IntegrityError
OperationalError = sqlite3.OperationalError

class DatabaseTests(unittest.TestCase):
    def setUp(self):
        pass

    def testBasic(self):
        db = Connection(":memory:")
        db.execute("""CREATE TABLE articles (
            id integer primary key,
            title text,
            author text
        );""")
        ls = [("abc", "stanley"), ("def", "stanley cai")]
        for (title, author) in ls:
            db.execute('INSERT INTO "articles" (title,author) '
                'VALUES ("%s", "%s")' % (title, author))
                
        for article in db.query("SELECT * FROM articles"):
            print article.title
        
if __name__ == '__main__':
    unittest.main()