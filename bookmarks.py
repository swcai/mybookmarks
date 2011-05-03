#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2011 Stanley Cai
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

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
            (r"/", MainHandler),
            (r"/bookmarks/([0-9]*)", BookmarkHandler),
            (r"/upload", UploadHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/auth/signup", AuthSignupHandler),
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
    def is_valid_username(self, name):
        return True
        
    def is_valid_email(self, email):
        return True
        
    def is_valid_password(self, password):
        return True
        
    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        else:
            return BOOKMARKS_DB.get("SELECT * FROM users WHERE id = %d" % int(user_id))
            
class AuthSignupHandler(BaseHandler):
    def post(self):
        username = self.get_argument("username")
        email = self.get_argument("email")
        password = self.get_argument("password")
        
        if not self.is_valid_username(username) or \
            not self.is_valid_email(email) or \
            not self.is_valid_password(password):
            self.render("login_or_signup.html", error_message = "Invalid email or user name")
        else:    
            user = BOOKMARKS_DB.get("SELECT * FROM users WHERE email=\"%s\"" %
                email)
            if not user:
                BOOKMARKS_DB.execute( "INSERT INTO users (username, email, password) \
                    VALUES (\"%s\", \"%s\", \"%s\")" % (username, email, password))
                user = BOOKMARKS_DB.get("SELECT * FROM users WHERE email=\"%s\"" %
                    email)
                BOOKMARKS_DB.commit()
                self.set_secure_cookie("user", str(user.id))
                self.redirect("/")
            else:
                self.render("login_or_signup.html", error_message = "This email is registered.")
            
    def get(self):
        user = self.get_current_user()
        if user:
            self.clear_secure_cookie("user")
        self.render("login_or_signup.html")
        
class AuthLoginHandler(BaseHandler):
    def post(self):
        username_or_email = self.get_argument("username_or_email")
        password = self.get_argument("password")
        if not self.is_valid_username(username_or_email) and \
            not self.is_valid_email(username_or_email):
            self.render("login_or_signup.html", error_message = "Invalid email or username")
        else:
            user = BOOKMARKS_DB.get("SELECT * FROM users WHERE email=\"%s\" and password=\"%s\"" %
                (username_or_email, password))
            if not user:
                user = BOOKMARKS_DB.get("SELECT * FROM users WHERE username=\"%s\" and password=\"%s\"" %
                    (username_or_email, password))
                if not user:
                    self.render("login_or_signup.html", error_message = "No such user")
                    return
            self.set_secure_cookie("user", str(user.id))
            self.redirect("/")
        
    def get(self):
        user = self.get_current_user()
        if user:
            self.clear_secure_cookie("user")
        self.render("login_or_signup.html") # need render this page?
        
class AuthLogoutHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if user:
            self.clear_cookie("user")
        self.redirect("/")
        
class MainHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if not user:
            self.render("login_or_signup.html")
        else:
            entries = []
            results = BOOKMARKS_DB.query("SELECT * FROM bookmarks where user_id=\"%s\"" % user.id)
            for record in results:
                entries.append((record.title, record.url, record.last_modified))
            self.render("main.html", entries = entries)
        
class UploadHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if not user:
            self.render("login_or_signup.html")
        else:
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
    ''' REST style API...No test at all.'''
    def get(self, user_id, bookmark_id):
        try:
            index = int(bookmark_id)
            record = BOOKMARKS_DB.get('SELECT * FROM bookmarks WHERE id=\"%d\"' % index)
            if record is None:
                raise Exception()
            self.write(json.dumps((record.title, record.url, record.last_modified)))
        except ValueError:
            results = []
            records = BOOKMARKS_DB.query('SELECT * FROM bookmarks')
            for record in records:
                results.append((record.title, record.url, record.last_modified))
            self.write(json.dumps(results))
            
    def put(self, user_id, bookmark_id):
        title, url = json.loads(self.request.body)
        date = int(time.time())
        try:
            index = int(bookmark_id)
            record = BOOKMARKS_DB.get('SELECT * FROM bookmarks WHERE id=\"%d\"' % index)
            if record is not None:
                BOOKMARKS_DB.execute('UPDATE bookmarks SET title=\"%s\", url=\"%s\", last_modified=\"%d\" WHERE id = \"%d\"' % (title, url, date, index))
        except ValueError:
            BOOKMARKS_DB.execute('INSERT INTO bookmarks (title, url, last_modified) VALUES (\"%s\", \"%s\", \"%d\")' % (title, url, date))
        finally:
            BOOKMARKS_DB.commit()
        
    def delete(self, user_id, bookmark_id):
        try:
            index = int(bookmark_id)
            BOOKMARKS_DB.execute('DELETE FROM bookmarks WHERE id=\"%d\"' % index)
            BOOKMARKS_DB.commit()
        except ValueError:
            self.write("Invalid bookmark_id")
            
            
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
    