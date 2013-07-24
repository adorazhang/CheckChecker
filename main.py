#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.api import users
from google.appengine.ext import db
import webapp2
import cgi
import re
import check_ap

MAIN_PAGE_HTML = """
<html>
<head>
    <!--<link href='http://fonts.googleapis.com/css?family=Lato' rel='stylesheet' type='text/css'>-->
    <style type="text/css">
    <!--
    body{
        text-align:center;
    }
    input{
        font-size:20px;
        border-color:#000;
    }
    -->
    </style>    
</head>
<body style="margin:50px; color:#000; font-family:'Lato', Arial; font-size:14px;">
    <form action="/sign" method="post">
      <div align="center">
      <div style="padding: 180 0 0 0; font-size:47px;">CHECK CHECKER</div>
        <div style="margin:50px; color:#bbb;">
        Check Checker will retrieve your Administrative Processing status from CEAC website every 5 minutes.</br>
        You are going to receive an e-mail notification whenever an update has been made to your case.</br>
        Your case will be automatically ruled out from the database when the status turns to "issued".</div>
        <div>Your Application ID or Case Number (e.g., AA0020AKAX):</br></br><input type="text" name="casenum"></input><input type="submit" value="SIGN UP"></div>
      </div>
    </form>
</body>
</html>
"""

class MainPage(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.headers['Description'] = 'An automatic tool used for checking VISA administrative processing status'
        self.response.headers['Keywords'] = 'VISA, Administrative Processing, Check, Auto Tool'
        self.response.headers['Author'] = 'Adora Zhang (www.iadorau.com)'
        # User Login
        currentUser = users.get_current_user()
        if currentUser:
            self.response.write('<h3>Hello user '+currentUser.email()+'!</h3>')
            records = Record.all()
            thisRecord = records.filter("user =", users.get_current_user())
            if users.is_current_user_admin():
                self.response.write("<a href=\"/admin\">Admin</a></br>")
            logout = ("<a href=\"%s\">Sign Out</a></br></br>" %users.create_logout_url("/"))
            self.response.write('%s' %logout)
            if thisRecord.get():
                result = thisRecord.get()
                self.response.write('Your case number '+result.caseNumber+' has been successfully signed up.</br>')
                self.response.write('Status Last Updated Date:'+result.updateDate)
        else:
            self.redirect(users.create_login_url(self.request.uri))
        # HTML Load
        self.response.write(MAIN_PAGE_HTML)

class Record(db.Model):
    # A Record is a triple of (Case Number, User, Update Date)
    caseNumber = db.StringProperty()
    user = db.UserProperty()
    updateDate = db.StringProperty(indexed=False)

class CaseNumInput(webapp2.RequestHandler):
    def post(self):
        if self.request.get('casenum'):
            # Case Number Validation
            pattern = re.compile(r'(aa|AA)\d{4}[a-zA-Z]{4}')
            casenum = cgi.escape(self.request.get('casenum'))
            if re.match(pattern, casenum):
                # Check AP Function Call
                if_ap, updatedate = check_ap.retrieve(casenum)
                if if_ap: # AP
                    currentUser = users.get_current_user()
                    # Log to DB
                    newCase = Record(caseNumber=casenum, user=currentUser, updateDate=updatedate)
                    newCase.put()
                    self.redirect('/')
                else: self.response.write('Your case has already closed.')                
            else: self.response.write('Your case number is invalid. Try again.')              
        else: self.response.write('Input must not be empty. Try again.')

class Admin(webapp2.RequestHandler):
    def get(self):
        self.response.write('All Records:</br>')
        records = Record.all().get()
        self.response.write(records.caseNumber)
        self.response.write(records.user.email())

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/sign',CaseNumInput),
    ('/admin',Admin),
], debug=True)
