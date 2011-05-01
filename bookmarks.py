#!/usr/bin/env python

import json
import time
import os

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
from tornado.options import define, options

import database

define("port", default=8888, help="run on the given port", type=int)

BOOKMARKS_DB = database.Connection("bookmarks.db")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", RootHandler),
            (r"/bookmarks/([0-9]*)", BookmarkHandler),
            (r"/upload", UploadHandler),
        ]
        settings = dict(
            cookie_secret="32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=", # todo update cookie_secret
            login_url="/auth/login",
            template_path=  os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            ui_modules = {"Entry": EntryModule },
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        
class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        user_json = self.get_secure_cookie("user")
        if not user_json:
            return None
        return tornado.escape.json_decode(user_json)
        
class RootHandler(BaseHandler):
    def get(self):
        entries = []
        results = BOOKMARKS_DB.query('SELECT * FROM bookmarks')
        for record in results:
            entries.append((record.title, record.url, record.last_modified))
        self.render("view.html", entries = entries)
        
class UploadHandler(BaseHandler):
    def get(self):
        title = self.get_argument('title')
        url = self.get_argument('url')
        date = int(time.time())        
        record = BOOKMARKS_DB.get('SELECT * FROM bookmarks WHERE title=\"%s\" and url=\"%s\"' % (title, url))
        if record is None:
            BOOKMARKS_DB.execute('INSERT INTO bookmarks (title, url, last_modified) VALUES (\"%s\", \"%s\", \"%d\")' % (title, url, date))
            self.write("Updated")
        else:
            BOOKMARKS_DB.execute('UPDATE bookmarks SET last_modified=\"%d\" WHERE title=\"%s\" and url=\"%s\"' % (date, title, url))
            self.write("Saved")
        BOOKMARKS_DB.commit()
                            
class BookmarkHandler(BaseHandler):
    def get(self, bookmark_id):
        try:
            index = int(bookmark_id)
            record = BOOKMARKS_DB.get('SELECT * FROM bookmarks WHERE id=\"%d\"' % index)
            if record is None:
                raise Exception()
            # could add "auto-remove" function
            
            self.redirect(record.url)
        except ValueError:
            results = []
            records = BOOKMARKS_DB.query('SELECT * FROM bookmarks')
            for record in records:
                results.append((record.title, record.url, record.last_modified))
            self.write(json.dumps(results))
        except:
            self.write("Invalid bookmark_id")
            
    def put(self, bookmark_id):
        title, url = json.loads(self.request.body)
        date = int(time.time())
        try:
            index = int(bookmark_id)
            record = BOOKMARKS_DB.get('SELECT * FROM bookmarks WHERE id=\"%d\"' % index)
            if record is None:
                raise ValueError()
            BOOKMARKS_DB.execute('UPDATE bookmarks SET title=\"%s\", url=\"%s\", last_modified=\"%d\" WHERE id = \"%d\"' % (title, url, date, index))
        except ValueError:
            BOOKMARKS_DB.execute('INSERT INTO bookmarks (title, url, last_modified) VALUES (\"%s\", \"%s\", \"%d\")' % (title, url, date))
        finally:
            BOOKMARKS_DB.commit()
                    
    def delete(self, bookmark_id):
        try:
            index = int(bookmark_id)
            BOOKMARKS_DB.execute('DELETE FROM bookmarks WHERE id=\"%d\"' % index)
            BOOKMARKS_DB.commit()
        except ValueError:
            self.write("Invalid bookmark_id")
            
    def post(self, bookmark_id):
        self.write("Not support yet")
        
class EntryModule(tornado.web.UIModule):
    def render(self, entry, isAdmin=False):
        return self.render_string("modules/entry.html", entry=entry, isAdmin=isAdmin)
                        
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
    
if __name__ == "__main__":
    main()
    