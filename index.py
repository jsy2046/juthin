#!/usr/bin/env python
# encoding=utf-8

import os.path
import re
import sys,os
import tornado.web
import tornado.wsgi
from tornado.escape import *
from tornado.options import define, options
import wsgiref.handlers
from juthin.core import Entry, Tags, Author
from google.appengine.ext import db
from django.utils import simplejson

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: 
            return None
        else:
            return True

class MainHandler(BaseHandler):
    def get(self):
        rs = db.GqlQuery('SELECT * FROM Entry ORDER BY created DESC')
        entries = rs.fetch(10)
        clouds = Tags().cloud()
        mapping = Tags().mapping()
        self.render('index.html', entries=entries, clouds=clouds)

class ViewHandler(BaseHandler):
    def get(self, id):
        id = int(id)
        rs = db.GqlQuery('SELECT * FROM Entry WHERE id = :1', id)
        mapping = Tags().mapping()
        entry = rs.get()
        ids = []
        for tags in entry.tags:
            if tags in mapping:
                for tag in mapping[tags]:
                    if tag not in ids and tag != id:
                        ids.append(tag)
        if ids:
            rs = db.GqlQuery('SELECT * FROM Entry WHERE id IN :1', ids)
            related = rs.fetch(10)
        else:
            related = []
        clouds = Tags().cloud()
        self.render('view.html', entry=entry, clouds=clouds, mapping=mapping, related=related)

class TagsHandler(BaseHandler):
    def get(self, tag):
        mapping = Tags().mapping()
        tag = url_unescape(tag)
        if tag in mapping and mapping[tag]:
            rs = db.GqlQuery('SELECT * FROM Entry WHERE id IN :1  ORDER BY created DESC', mapping[tag])
            entries = rs.fetch(10)
            clouds = Tags().cloud()
            self.render('index.html', entries=entries, clouds=clouds, mapping=mapping)
        else:
            self.redirect('/')

class Application(tornado.wsgi.WSGIApplication):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/view/([0-9]+).html", ViewHandler),
            (r"/tags/([^/]+)?", TagsHandler),
        ]
        author = Author.all().get()
        settings = dict(
            blog_title = author.blog_title,
            blog_domain = author.blog_domain,
            blog_timezone = author.blog_timezone,
            blog_author = author.nickname,
            template_path = os.path.join(os.path.dirname(__file__), "template/"+author.blog_theme+'/'),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            #ui_modules = {"Entry": EntryModule},
            #xsrf_cookies = True,
            cookie_secret = "11oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            login_url = "/writer/signin",
        )
        tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)

def main():
    wsgiref.handlers.CGIHandler().run(Application())

if __name__ == "__main__":
    main()
