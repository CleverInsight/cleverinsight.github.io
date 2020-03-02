from version import version as __version__
import re
import os
import csv
import sys
import json
import uuid
import bcrypt
import tornado
import subprocess
import pandas as pd
import numpy as np
import tornado.escape
# from cStringIO import StringIO
from io import StringIO
from tornado.template import Template
from tornado import gen
from textblob import TextBlob
from lib.litmus import *
from lib.data import DataStore
from lib.layout import *
from lib.neuron import *


__UPLOADS__  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage/')
__TWITTER__  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage/twitter/')
__DOWNLOADS__  = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage/downloads/')
__LAYOUT__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visuals/templates')
__TMPL__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visuals/_tmpl')
__VISUAL__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'visuals/')
__APPS__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'apps/')
__SYS_DB__ = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sys.db')



# Overall path object
PATH = {
    'upload' : __UPLOADS__,
    'download': __DOWNLOADS__,
    'twitter': __TWITTER__,
    'layout': __LAYOUT__,
    'visual': __VISUAL__,
}

# Instantiate all libraries
DB = DataStore()

preprocess = Preprocess()


def check_roles(handler, role):

    if role == 1:
        pass
    else:
        return handler.redirect('/login')


def hash_pwd(plain_text_password):
    # Hash a password for the first time
    #   (Using bcrypt, the salt is saved into the hash itself)
    return bcrypt.hashpw(plain_text_password, bcrypt.gensalt())


def check_password(plain_text_password, hashed_password):
    # Check hased password. Useing bcrypt, the salt is saved into the hash itself
    return bcrypt.checkpw(plain_text_password, hashed_password)


def replace_tab(s, tabstop = 4):
  result = str()
  for c in s:
    if c == '\t':
      while (len(result) % tabstop != 0):
        result += ' ';
    else:
      result += c    
  return result


def T(name, **kw):
    # Fetch the template script based on give name
    f = open(os.path.join(__LAYOUT__, name), 'rb')
    # Return the visual completely
    # return f.read()
    t = Template(f.read())
    return t.generate(**dict([('template_file', name)] + list(globals().items()) + list(kw.items())))

def SVG(name, **kw):
    # Wrap the T() string with SVG tag
    return 'svg string'


class BaseHandler(tornado.web.RequestHandler):

    def __init__(self,application, request,**kwargs):
            super(BaseHandler,self).__init__(application,request)

    def write_error(self, status_code, **kwargs):
        if status_code == 404:
            self.render('_errors/404.html',page=None, error=kwargs['exc_info'])
        elif status_code == 500:
            print(kwargs)
            self.render('_errors/500.html',page=None, error=kwargs['exc_info'])
        else:
            self.render('_errors/unknown.html',page=None)

    def set_default_headers(self):
        self.set_header('Server', 'Sparx/' + '.'.join(str(v) for v in __version__))
        self.set_header('Company', 'CleverInsight Labs')
        self.set_header('Author', 'Bastin Robins J')



    def get_current_user(self):
        return self.get_secure_cookie("user")

    def get_current_role(self):
        return self.get_secure_cookie("role")

    def get_current_email(self):
        return self.get_secure_cookie("email")



# Basic LimusBi server initialization
class MainHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('components.html', handler=self, pd=pd)
        # self.write('Sparx '+'.'.join(str(v) for v in __version__))
        self.redirect('/docs/apps.html')



class MainDocsHandler(BaseHandler):
    
    @tornado.web.authenticated
    def get(self):
        """
        Return the main document index page
        """
        self.render('index.html', handler=self, pd=pd)



class TemplateHandler(BaseHandler):
    """
        Global .html file handler
    """
    def get(self, filename):

        if '.html' in filename:
            self.render(filename, pd=pd, DB=DB, T=T)
        else:
            self.render(filename+'.html', pd=pd, DB=DB, T=T)


class DocsHandler(BaseHandler):
    """
        Global .html file handler
    """
    @tornado.web.authenticated
    def get(self, filename):

        # Instantiate db
        l = Litmus()

        path = os.path.join('_docs', filename)

        query = ''' SELECT * FROM apps ORDER BY id DESC'''
        apps = l._execute(query)    

        if '.html' in filename:

            self.render(path, pd=pd, DB=DB, T=T, PATH=PATH, Apps=apps)
        else:
            # self.render(path+'.html', pd=pd, DB=DB, T=T, PATH=PATH, Apps=apps)
            id = self.get_argument('id')
            query = ''' SELECT * FROM apps WHERE id = %d''' %(int(id))
            app = l._get(query)

            versions_sql = ''' SELECT * FROM version WHERE apps_id = %d ORDER BY created_at DESC''' %(int(id))
            versions = l._execute(versions_sql)

            datasources_sql = ''' SELECT * FROM datastore WHERE apps_id = %d ORDER BY id DESC''' %(int(id))
            datasources = l._execute(datasources_sql)

            self.render(os.path.join('_docs', 'edit.html'), pd=pd, DB=DB, T=T, PATH=PATH,\
             App=app, versions=versions, datasources=datasources)
            

class AppHandler(BaseHandler):
    """
        Global .html file handler
    """
    def get(self, filename):

        path = os.path.join(__APPS__, filename)

        l = Litmus()
        query = ''' SELECT * FROM apps ORDER BY id DESC'''
        apps = l._execute(query)
        
        if '.html' in filename:
            self.render(path, pd=pd, DB=DB, T=T, PATH=PATH, Apps=apps)
        else:
            self.render(path+'.html', pd=pd, DB=DB, T=T, PATH=PATH, Apps=apps)


class ApiHandler(BaseHandler):

    def get(self):

        if 'id' in self.request.arguments and 'fname' in self.request.arguments\
         and 'response' in self.request.arguments:
            ''' 
                Return a list of algorithms
            '''
            l = Litmus()
            id = self.get_argument('id')
            app_sql = ''' SELECT * FROM apps WHERE id = %d''' %(int(id))
            app = l._get(app_sql)

            df = pd.read_csv(os.path.join(__APPS__, app['filename'].split('.')[0], 'data', self.get_argument('fname')))

            # Get types of algorithms


            response = {
                'models': preprocess.get_response_model_names(df[self.get_argument('response')]),
                'type': preprocess.get_response_type(df[self.get_argument('response')])
            }

            return self.write(json.dumps(response))


        self.write('hi')




class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass
 
    def on_message(self, message):

        msg = json.loads(message)
        print(msg)
        import time
        self.write_message(u"Your message was: 0" + message)
        time.sleep(5)
        self.write_message(u"Your message was: 1" + message)
        time.sleep(5)
        self.write_message(u"Your message was: 2" + message)
        time.sleep(5)
        self.write_message(u"Your message was: 3" + message)

 
    def on_close(self):
        pass
 

class DBHandler(BaseHandler):

    def get(self):

        l = Litmus()
        operation = self.get_argument('operation')
        table = self.get_argument('table')
        if operation == 'select':
            query = ''' SELECT * FROM %s ORDER BY id DESC''' %(table)

        if operation == 'update':

            # return self.write(json.dumps(self.request.arguments))

            key = self.get_argument('key')
            value = self.get_argument('value')
            id = self.get_argument('id')
            value_type = self.get_argument('type')

            if value_type == 'str':
                query = ''' UPDATE %s SET %s='%s' WHERE id=%d ''' %(table, key, value, int(id))

            if value_type == 'int':
                query = ''' UPDATE %s SET %s=%d WHERE id=%d ''' %(table, key, int(value), int(id))

            self.set_secure_cookie("message", 'Updated!')


        if operation == 'delete':
            key = self.get_argument('key')
            value = self.get_argument('value')
            value_type = self.get_argument('type')

            if value_type == 'str':
                query = ''' DELETE FROM %s WHERE %s='%s' ''' %(table, key, value)

            if value_type == 'int':
                query = ''' DELETE FROM %s WHERE %s=%d ''' %(table, key, int(value))

            self.set_secure_cookie("message", 'Deleted dataset!')



        result = l._execute(query)
        self.redirect(self.get_argument('callback'))

    def post(self):

        l = Litmus()
        # Insert user into user table
        add_user_sql = "INSERT INTO users (email, password, role) VALUES (?,?,?)"
        add_user_val = [self.get_argument('email'), hash_pwd(self.get_argument('password')), self.get_argument('role')]
        user_id = l._set(add_user_sql, add_user_val)

        # Insert the role of user into usertable
        add_role_sql = "INSERT INTO user_roles (user_id, role_id) VALUES (?,?)"
        add_role_val = [user_id, self.get_argument('role')]
        l._set(add_role_sql, add_role_val)

        self.set_secure_cookie("message", 'User added!')
        return self.redirect('/settings')


class SettingHandler(BaseHandler):
    
    @tornado.web.authenticated    
    def get(self):

        # check_roles(self, self.get_current_role())

        l = Litmus()
        user_query = ''' SELECT * FROM users ORDER BY id DESC'''
        users = l._execute(user_query)  
        return self.render('settings.html', users=users)


class AuthLoginHandler(BaseHandler):

    def get(self):
        self.render('login.html', handler=self)

    def post(self):
        
        email = tornado.escape.xhtml_escape(self.get_argument("email"))
        password = tornado.escape.xhtml_escape(self.get_argument("password"))

        l = Litmus()
        query = "SELECT * FROM users WHERE email='"+ str(email) + "'"
        user = l._get(query)
        
        if 'email' in user:

            if check_password(password.encode("utf-8"), user['password'].encode("utf-8")):

                if user['status'] == 1:
                    self.set_secure_cookie("user", str(user['id']))
                    self.set_secure_cookie("email", str(user['email']))
                    self.set_secure_cookie("role", str(user['role']))
                    self.redirect(self.get_argument("next", u"/"))
                else:
                    self.write('<center>Your Account is Disabled. Kindly contact administrator <a href="/">Go Home</a></center>')

            else:
                self.write('<center>Your Password does not match. Kindly contact administrator <a href="/">Go Home</a></center>')

        else:
            self.write('<center>Something Wrong With Your Login credentials <a href="/">Go Home</a></center>')


class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("email")
        self.clear_cookie("role")
        self.redirect(self.get_argument("next", "/"))


class TextHandler(BaseHandler):
    def get(self):

        if 'filename' in self.request.arguments:
            # check if file exist
            if os.path.exists(os.path.join(__TMPL__, self.get_argument('filename'))):
                lines = open(os.path.join(__TMPL__, self.get_argument('filename')), 'r')
                self.write(replace_tab(lines.read()))
            else:
                self.write('Nothing found!!')


    def post(self):

        if 'code' in self.request.arguments:

            if os.path.exists(os.path.join(__VISUAL__, self.get_argument('filename'))):
                self.write('Already exists')
            else:
                f = open(os.path.join(__VISUAL__, self.get_argument('filename')), 'w')
                f.write(replace_tab(self.get_argument('code')))
                f.close()
                filename = self.get_argument('filename')
                self.write(filename)
        else:
            self.write('Code is empty')



class CreateHandler(BaseHandler):
    ''' App creation and datasource creation api '''
    def post(self):

        if 'app_name' in self.request.arguments:
            app_name = self.get_argument('app_name')
            layout = self.get_argument('layout')
            code = self.get_argument('code')
            fname = app_name.replace(' ', '-').lower()
            user_id = 1

            if '.html' not in fname:
                filename = fname+'.html'


            if not os.path.exists(os.path.join(__APPS__, fname)):

                # Inititate Litmus connection
                l = Litmus()

                # Insert query
                # query = "INSERT INTO apps (name, layout, code, filename, user_id) VALUES ({0}, {1}, {2}, {3}, {4}) ".format(app_name, layout, code, filename, int(user_id))

                sql = "INSERT INTO apps (name, layout, code, filename, user_id) VALUES (?,?,?,?,?)"
                sql_val = [app_name, layout, code, filename, user_id]

                # Execute the insert query  
                l._set(sql, sql_val)

                # create directory inside apps folder
                os.makedirs(os.path.join(__APPS__, fname))
                os.makedirs(os.path.join(__APPS__, fname, 'data'))
                os.makedirs(os.path.join(__APPS__, fname, 'models'))


                try:
                    with open(os.path.join(__APPS__, fname, '__init__.py'), "w+") as f:
                        # Do whatever with f
                        pass
                except:
                    pass

                try:
                    with open(os.path.join(__APPS__, fname, 'model.py'), "w+") as f:
                        # Do whatever with f
                        pass
                except:
                    pass

                f = open(os.path.join(__APPS__, fname, 'index.html'), 'w')
                f.write(code)
                f.close()

            self.redirect('/docs/apps.html')

        elif 'app_path' in self.request.arguments:
            fileinfo = self.request.files['filearg'][0]

            fname = fileinfo['filename']

            # Actual filename
            extn = os.path.splitext(fname)[1]

            # # New filename
            cname = str(uuid.uuid4()) + extn
            fh = open(os.path.join(__APPS__, self.get_argument('app_path'), 'data', cname), 'w') 
            fh.write(fileinfo['body'])

            # Insert statement
            l = Litmus()
            sql = "INSERT INTO datastore (name, filename, type, apps_id) VALUES (?,?,?,?)"
            sql_val = [self.get_argument('name'), cname, extn, self.get_argument('app_id')]
            app = l._set(sql, sql_val)

            self.set_secure_cookie("message", 'Dataset added!')
            self.redirect('/docs/edit?id='+ self.get_argument('app_id'))

        else: 
            self.write('Code is empty')

    def put(self):

        if 'id' in self.request.arguments:

            l = Litmus()
            id = self.get_argument('id')
            query = ''' SELECT * FROM apps WHERE id = %d''' %(int(id))
            app = l._get(query)

            app_name = app['filename'].split('.')[0]

            if os.path.exists(os.path.join(__APPS__, app_name, 'index.html')):
                f = open(os.path.join(__APPS__, app_name, 'index.html'), 'w')
                f.write(self.get_argument('code'))
                f.close()

                # Update statement
                update_sql = "UPDATE apps SET name=(?), code=(?) WHERE id = (?)"
                sql_val = [self.get_argument('app_name'), self.get_argument('code'), int(self.get_argument('id'))]
                app = l._set(update_sql, sql_val)


                # Insert statement
                sql = "INSERT INTO version (apps_id, code, user_id) VALUES (?,?,?)"
                sql_val = [int(id), self.get_argument('code'), 1]

                app = l._set(sql, sql_val)


                self.write('True')


        else:
            self.write('Code is empty')


class AjaxHandler(BaseHandler):

    def get(self):
        
        if 'id' in self.request.arguments and 'fname' in self.request.arguments\
         and 'response' in self.request.arguments:
            ''' 
                Return a list of all columns in dataset
            '''
            l = Litmus()
            id = self.get_argument('id')
            app_sql = ''' SELECT * FROM apps WHERE id = %d''' %(int(id))
            app = l._get(app_sql)

            df = pd.read_csv(os.path.join(__APPS__, app['filename'].split('.')[0], 'data', self.get_argument('fname')))
            return self.finish(json.dumps({'columns': list(df.columns), 'summary': df.describe().to_html(classes='table table-striped') }))


        if 'id' in self.request.arguments and 'fname' in self.request.arguments:

            l = Litmus()
            id = self.get_argument('id')
            app_sql = ''' SELECT * FROM apps WHERE id = %d''' %(int(id))
            app = l._get(app_sql)

            df = pd.read_csv(os.path.join(__APPS__, app['filename'].split('.')[0], 'data', self.get_argument('fname')))
            columns = df.columns

            if 'json' in self.request.arguments:

                return self.write(df.head(100).to_json(orient='index'))

            else:  
                response = []
                for i in columns:
                    d = df[i].describe()
                    response.append({
                        'Column': i,
                        'Type': 'Categorical' if df[i].dtypes != float else 'Numerical',
                        'Instances': list(df[i].head(3)),
                        'Count': '{0:.2f}'.format(d['count']) if 'count' in d else 'NIL',
                        'Unique': '{0:.2f}'.format(d['unique']) if 'unique' in d else 'NIL',
                        'Freq': '{0:.2f}'.format(d['freq']) if 'freq' in d else 'NIL',
                        'Missing': df[i].isnull().sum(),
                        'Median': '{0:.2f}'.format(df[i].median()) if df[i].dtypes == float else 'NIL',
                        'Min': '{0:.2f}'.format(d['min']) if 'min' in d else 'NIL', 
                        'Max': '{0:.2f}'.format(d['max']) if 'max' in d else 'NIL',
                        'Mean': '{0:.2f}'.format(d['mean']) if 'mean' in d else 'NIL',
                        'Std': '{0:.2f}'.format(d['std']) if 'std' in d else 'NIL',
                        '25%': '{0:.2f}'.format(d['25%']) if '25%' in d else 'NIL',
                        '50%': '{0:.2f}'.format(d['50%']) if '50%' in d else 'NIL',
                        '75%': '{0:.2f}'.format(d['75%']) if '75%' in d else 'NIL'
                    })

                self.render('describe.html', data=response)            
        else:
            self.write('Out of selection')



    def post(self):
        pass


class FetchHandler(BaseHandler):

    ''' Twitter API Fetcher '''
    def get(self):
        self.write('How to make')

    # def post(self):
    #     hashtag = self.get_argument('hashtag')

    #     reload(sys)
    #     sys.setdefaultencoding('utf8')
    #     from twitter import *

    #     config = {}
    #     execfile("api_config.py", config)

    #     twitter = Twitter(
    #                 auth = OAuth(config["access_key"], config["access_secret"],\
    #                 config["consumer_key"], config["consumer_secret"]))


    #     __TWITTER__ = os.path.join(__UPLOADS__, 'twitter', (hashtag + '.csv'))

    #     make_list = csv.writer(open(__TWITTER__, 'wb'))
    #     make_list.writerow(['id', 'username', 'profile_pic',\
    #         'location', 'friends_count', 'description', 'followers_count',\
    #         'statuses_count', 'tweet', 'polarity', 'subjectivity', 'sentiment', 'created'])

    #     query = twitter.search.tweets(q = hashtag)

    #     for tweet in query["statuses"]:
    #         text = (tweet['text']).encode('utf-8', errors = 'ignore')
    #         tweet_sentiment = TextBlob(text)

    #         # determine if sentiment is positive, negative, or neutral
    #         if tweet_sentiment.sentiment.polarity < 0:
    #             sentiment = "negative"
    #         elif tweet_sentiment.sentiment.polarity == 0:
    #             sentiment = "neutral"
    #         else:
    #             sentiment = "positive"

    #         make_list.writerow([tweet['id'], tweet['user']['screen_name'],\
    #             tweet['user']['profile_image_url'], tweet['user']['location'],\
    #             tweet['user']['friends_count'], tweet['user']['description'],\
    #             tweet['user']['followers_count'], tweet['user']['statuses_count'],\
    #             text, tweet_sentiment.sentiment.polarity, tweet_sentiment.sentiment.subjectivity,\
    #             sentiment, tweet['created_at']])

    #     self.redirect('/docs/sentiment.html?tag=' + hashtag.replace('#', ''))

