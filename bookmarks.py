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
import hashlib

import tornado.auth
import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.database
from tornado.options import define, options

import settings

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default = settings.default_mysql_host,
		help="blog database host")
define("mysql_database", default = settings.default_mysql_database,
		help="blog database name")
define("mysql_user", default = settings.default_mysql_user,
		help="blog database user")
define("mysql_password", default = settings.default_mysql_password,
		help="blog database password")

# TODO update the functions to use exception
class Application(tornado.web.Application):
    
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/(\w+)/bookmarks/([0-9]*)", BookmarkHandler),
            (r"/upload", UploadHandler),
            (r"/setting", SettingHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/auth/signup", AuthSignupHandler),
        ]
        settings = dict(
            # TODO update cookie secret
            cookie_secret="32oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url="/auth/login",
            template_path=  os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            ui_modules = {"Entry": EntryModule },
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.db = tornado.database.Connection(
            host = options.mysql_host, database=options.mysql_database,
            user = options.mysql_user, password=options.mysql_password)
        
class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db
    
    # TODO validate the user name from remote
    def is_valid_username(self, name):
        return True
        
    # TODO validate the email address from remote
    def is_valid_email(self, email):
        return True
        
    # TODO validate the password from remote
    def is_valid_password(self, password):
        return True
        
    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id:
            return None
        else:
            return self.db.get("SELECT * FROM users WHERE id = %d" % int(user_id))
            
    def get_user_from_alias(self, user_alias):
        return self.db.get("SELECT * FROM users WHERE alias=\"%s\"" % user_alias)
        
class AuthSignupHandler(BaseHandler):
    def _generate_alias(self, name, email):
        s = hashlib.sha1()
        s.update(name)
        s.update(email)
        s.update(str(time.time()))
        return s.hexdigest()[:6]
        
    def post(self):
        username = self.get_argument("username")
        email = self.get_argument("email")
        password = self.get_argument("password")
        
        if not self.is_valid_username(username) or \
            not self.is_valid_email(email) or \
            not self.is_valid_password(password):
            self.render("login_or_signup.html", error_message = "Invalid email or user name")
        else:
            user = self.db.get("SELECT * FROM users WHERE email=\"%s\"" %
                email)
            if not user:
                self.db.execute("INSERT INTO users (username, email, password, alias) \
                    VALUES (\"%s\", \"%s\", \"%s\", \"%s\")" % \
                        (username, email, password, \
                            self._generate_alias(username, email)))
                user = self.db.get("SELECT * FROM users WHERE email=\"%s\"" %
                    email)
                # self.db.commit()
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
            user = self.db.get("SELECT * FROM users WHERE email=\"%s\" and password=\"%s\"" %
                (username_or_email, password))
            if not user:
                user = self.db.get("SELECT * FROM users WHERE username=\"%s\" and password=\"%s\"" %
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
        print user
        if not user:
            self.render("login_or_signup.html")
        else:
            entries = []
            results = self.db.query("SELECT * FROM bookmarks WHERE user_id=\"%s\" ORDER BY modified_at DESC" % user.id)
            for record in results:
                entries.append((record.title, record.url, record.modified_at))
            # TODO update the main page (including logout link and setting link)
            self.render("main.html", user = user, entries = entries)

class SettingHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if not user:
            self.render("login_or_signup.html")
        else:
            # TODO Polish setting page
            self.render("setting.html", user = user)
            
    def post(self):
        user = self.get_current_user()
        if not user:
            self.render("login_or_signup.html")
        else:
            username = self.get_argument('username')
            password1 = self.get_argument('password1')
            password2 = self.get_argument('password2')
            if username != user.username or password1 != password2:
                raise Exception()
                return
            self.db.execute('UPDATE users SET password=\"%s\" WHERE id=\"%d\"' % (password1, user.id))
            # self.db.commit()
            self.redirect("/")
        
class UploadHandler(BaseHandler):
    def get(self):
        user = self.get_current_user()
        if not user:
            self.render("login_or_signup.html")
        else:
            # TODO need clean up the title from remote
            title = self.get_argument('title')
            url = self.get_argument('url')
            date = int(time.time())
            record = self.db.get('SELECT * FROM bookmarks WHERE user_id=\"%d\" AND title=\"%s\" AND url=\"%s\"' % (user.id, title, url))
            if record is None:
                self.db.execute('INSERT INTO bookmarks (title, url, modified_at, user_id, tag) VALUES (\"%s\", \"%s\", \"%d\", \"%d\", 0)' % (title, url, date, user.id))
            else:
                self.db.execute('UPDATE bookmarks SET modified_at=\"%d\" WHERE title=\"%s\" and url=\"%s\"' % (date, title, url))
            # self.db.commit()

# TODO test all the REST APIs
class BookmarkHandler(BaseHandler):
    
    def get(self, user_alias, bookmark_id):
        user = self.get_user_from_alias(user_alias)
        if not user:
            raise Exception()
            return
            
        try:
            index = int(bookmark_id)
            records = self.db.query('SELECT * FROM bookmarks WHERE user_id=\"%d\" ORDER BY modified_at DESC' % user.id)
            if records is None:
                raise Exception()
            if index >= len(records):
                return
            self.write(json.dumps((records[index].title, record[index].url, record[index].last_modified)))
        except ValueError:
            results = []
            records = self.db.query('SELECT * FROM bookmarks WHERE user_id=\"%d\" ORDER BY modified_at DESC' % user.id)
            for record in records:
                results.append((record.title, record.url, record.last_modified))
            self.write(json.dumps(results))
            
    def put(self, user_alias, bookmark_id):
        current_user_id = self.get_secure_cookie("user")
        if not current_user_id:
            self.render("login_or_signup.html")
        
        user = self.get_user_from_alias(user_alias)
        if not user or user.id != current_user_id:
            raise Exception()
            return
                    
        title, url = json.loads(self.request.body)
        date = int(time.time())
        try:
            index = int(bookmark_id)
            records = self.db.query('SELECT * FROM bookmarks WHERE user_id=\"%d\" ORDER BY modified_at DESC' % user.id)
            if records is None:
                raise Exception()
            if index >= len(records):
                raise ValueError()
                
            record = self.db.get('SELECT * FROM bookmarks WHERE id=\"%d\"' % records[index].id)
            if record is not None:
                self.db.execute('UPDATE bookmarks SET title=\"%s\", url=\"%s\", modified_at=\"%d\" WHERE id = \"%d\"' % (title, url, date, record.id))
        except ValueError:
            self.db.execute('INSERT INTO bookmarks (title, url, modified_at, tag, user_id) VALUES (\"%s\", \"%s\", \"%d\", 0, \"%d\")' % (title, url, date, user.id))
        finally:
            # self.db.commit()
            pass
        
    def delete(self, user_id, bookmark_id):
        current_user_id = self.get_secure_cookie("user")
        if not current_user_id:
            self.render("login_or_signup.html")
            
        user = self.get_user_from_alias(user_alias)
        if not user or user.id != current_user_id:
            raise Exception()
            return
        
        try:
            index = int(bookmark_id)
            records = self.db.query('SELECT * FROM bookmarks WHERE user_id=\"%d\" ORDER BY modified_at DESC' % user_id)
            if records is None:
                raise Exception()
            if index >= len(records):
                raise ValueError()
                
            self.db.execute('DELETE FROM bookmarks WHERE id=\"%d\"' % records[index].id)
            # self.db.commit()
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
    