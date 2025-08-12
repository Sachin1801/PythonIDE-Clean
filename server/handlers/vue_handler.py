#!/usr/bin/env python3

from tornado import web


class VueHandler(web.RequestHandler):
    def get(self):
        self.render("index.html")
