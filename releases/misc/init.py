'''
`Sparx-Lite` is the visualization data cleaner and crunching engine which is capable of generating the user
requested content from the data sources uploaded

__author__ = 'Bastin Robin'
__email__  = robin@cleverinsight.co
'''
from __future__ import print_function
from version import version as __version__
import re
import os
import sys
import rsa
import os.path
import stat
import json
import uuid
import logging
import datetime
import pandas as pd
import numpy as np
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import tornado.auth
from tornado.options import define, options
from tornado.escape import json_encode
from tornado import template
from handlers import *

define(
    "port",
    default=int(
        os.environ.get(
            "PORT",
            5000)),
    help="run on the given port",
    type=int)
define('nobrowser', default=True, help='Do not start webbrowser', type=bool)

SOURCE = os.path.dirname(os.path.abspath(__file__))
_PATH = os.path.join(SOURCE, 'lib')


class Application(tornado.web.Application):
    def __init__(self):

        handlers = [
            (r"/", MainHandler),
            (r"/db", DBHandler),
            (r"/login", AuthLoginHandler),
            (r"/logout", AuthLogoutHandler),
            (r"/fetch", FetchHandler),
            (r"/ajax", AjaxHandler),
            (r"/api", ApiHandler),
            (r"/settings", SettingHandler),
            (r"/text", TextHandler),
            (r"/app", CreateHandler),
            (r"/apps/(.*)", AppHandler),
            (r"/docs/", MainDocsHandler),
            (r"/docs/(.*)", DocsHandler),
            (r'/websocket', WebSocketHandler),
            (r"/(.*)", TemplateHandler)
        ]

        settings = dict(
            cookie_secret="43oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
            template_path=os.path.join(os.path.dirname(__file__), "visuals"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
            autoreload=True,
            gzip=True,
            debug=True,
            login_url='/login',
            autoescape=None
        )

        tornado.web.Application.__init__(self, handlers, **settings)


def expiry_on(path):
    try:
        license_file = os.path.join(path, 'LICENSE')
        license_lines = open(license_file).readlines()
    except IOError:
        die('This machine does not have a license yet.')

    (license_uname, license_date, sign,) = (l.strip()
                                            for l in license_lines[:3])

    (from_date, to_date,) = (datetime.datetime.strptime(d, '%Y-%m-%d')
                             for d in license_date.split(' '))
    now = datetime.datetime.now()

    return to_date.strftime("%d %b, %Y")


def _vol(path):
    import base64
    import platform
    import socket

    uname = ' '.join(platform.uname())
    # uname = hex(uuid.getnode())+' '+platform.uname().version+' '+platform.uname().machine

    def run():
        path = os.path.join(os.path.dirname(__file__), "visuals")
        static = os.path.join(os.path.dirname(__file__), "static")



        class LicenseHandler(tornado.web.RequestHandler):
            def get(self):
                self.render('license.html', version='version')

        app = tornado.web.Application([('/', LicenseHandler)],
                                      static_path=static,
                                      template_path=path
                                      )

        port = 8888
        while port < 9000:
            try:
                app.listen(port, xheaders=True)
                break
            except socket.error:
                port += 1

        print(sys.stderr)

        url = 'http://127.0.0.1:%d' % port
        try:
            import webbrowser
            print('Visit ' + url + ' for a license ')
            webbrowser.open(url)
        except ImportError:
            pass

        tornado.ioloop.IOLoop.instance().start()

    def die(msg):
        sys.stderr.write(msg)
        sys.stderr.write(
            '\n\nYou should email license@cleverinsight.co and get a new license. Mention this code:\n%s\n\n' %
            uname)
        sys.stderr.write(
            '... and save the LICENSE file you get at:\n%s\n\n' %
            path)
        input('After noting these, press ENTER to close this window. ')
        # sys.exit(-1)
        run()

    try:
        license_file = os.path.join(path, 'LICENSE')
        license_lines = open(license_file).readlines()
    except IOError:
        die('This machine does not have a license yet.')

    (license_uname, license_date, sign,) = (l.strip()
                                            for l in license_lines[:3])

    if uname != license_uname:
        die("This machine has another machine's license:\n" + license_uname)

    (from_date, to_date,) = (datetime.datetime.strptime(d, '%Y-%m-%d')
                             for d in license_date.split(' '))
    now = datetime.datetime.now()

    if from_date > now or now > to_date:
        die('This license has expired.')

    public_key = rsa.PublicKey(7536031843268116359080816550116996395850668765953362202458977259126858121692866095588080612658209610356308429486462330553891865314861527172133866282508997,65537)

    try:
        rsa.verify(
            (uname + license_date).encode("utf-8"),
            base64.b64decode(sign),
            public_key)
    except rsa.pkcs1.VerificationError:

        die('The license appears invalid.')


# Litmus Server Initialization
def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    if not options.nobrowser:
        try:
            import webbrowser
            webbrowser.open('http://127.0.0.1:%d' % options.port)
        except ImportError:
            pass
    logging.info('Sparx - version ' +
                 str(__version__) +
                 '. started at: http://localhost:%d/ -> %s' %
                 (options.port, SOURCE))
    logging.info('License Valid till : ' + str(expiry_on(_PATH)))
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
