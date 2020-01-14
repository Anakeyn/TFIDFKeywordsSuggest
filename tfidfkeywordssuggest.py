# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 15:41:05 2019

@author: Pierre
"""
#############################################################
# Anakeyn TF-IDF Keywords Suggest Windows  Version   Alpha 0.1
# Anakeyn TF-IDF Keywords Suggest is a keywords suggestion tool.
# This tool searches in the first pages responding to a given keyword in Google. Next the 
# system will get the content of the pages  in order to find popular and original  keywords 
# in the subject area. The system works  with a TF-IDF  algorithm.
#############################################################
#Copyright 2019-2020 Pierre Rouarch 
# License GPL V3
#############################################################

#see also
#https://github.com/PrettyPrinted/building_user_login_system
#https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
#https://doc.lagout.org/programmation/python/Flask%20Web%20Development_%20Developing%20Web%20Applications%20with%20Python%20%5BGrinberg%202014-05-18%5D.pdf
#https://blog.appseed.us/flask-dashboard-light-learn-flask-by-coding-dashboards/
#https://github.com/MarioVilas/googlesearch   #googlesearch serp scraper
#https://pypi.org/project/SerpScrap/  #other serp scraper

###############   FOR FLASK ############################### 
#conda install -c anaconda flask
from flask import Flask, render_template, redirect, url_for,  Response, send_file
#pip install flask-bootstrap  #if not installed in a console
from flask_bootstrap import Bootstrap #to have a responsive design with fmask
from flask_wtf import FlaskForm #forms
from wtforms import StringField, PasswordField, BooleanField, SelectField #field types
from wtforms.validators import InputRequired, Email, Length #field validators
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import time
from datetime import datetime, date      #, timedelta

##############  For other Functionalities
import numpy as np #for vectors and arrays
import pandas as pd  #for dataframes
#pip install google  #to install Google Searchlibrary by Mario Vilas
#https://python-googlesearch.readthedocs.io/en/latest/
import googlesearch  #Scrap serps
#to randomize pause
import random
#
import nltk # for text mining
from nltk.corpus import stopwords
nltk.download('stopwords')
#print (stopwords.fileids())
from sklearn.feature_extraction.text import TfidfVectorizer

import requests #to read urls contents
from bs4 import BeautifulSoup
from bs4.element import Comment
import re  #for regex
import unicodedata  #to decode accents
import os #for directories 
import sys #for sys variables


##### Flask Environment
# Returns the directory the current script (or interpreter) is running in
def get_script_directory():
    path = os.path.realpath(sys.argv[0])
    if os.path.isdir(path):
        return path
    else:
        return os.path.dirname(path)
    
myScriptDirectory = get_script_directory()
#############################################################
#  In a myconfig.py  file, think to define the database server name
#############################################################
import myconfig  #my configuration : edit this if needed 
#print(myconfig.myDatabaseURI )

myDirectory =myScriptDirectory+myconfig.UPLOAD_SUBDIRECTORY
if not os.path.exists(myDirectory ):
    os.makedirs(myDirectory )

app = Flask(__name__)   #flask  application
app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'   #what you want
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  #avoid a warning
app.config['SQLALCHEMY_DATABASE_URI'] =myconfig.myDatabaseURI    #database choice

bootstrap = Bootstrap(app)  #for bootstrap compatiblity


############# #########################
#  Database  and Tables 
#######################################

db = SQLAlchemy(app)  #the current database attached to the app.


#users
class User(UserMixin, db.Model):
    __tablename__="user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    role = db.Column(db.Integer)
    
    def __init__(self, username, email, password, role):
        self.username = username
        self.email = email
        self.password = password
        self.role = role


#Global Queries  / Expressions / Keywords  searches 
class Keyword(db.Model):
    __tablename__="keyword"
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200))
    tldLang = db.Column(db.String(50))  #google tld + lang
    data_date = db.Column(db.Date, nullable=False, default=datetime.date)  #date of the last data update
    search_date = db.Column(db.Date, nullable=False, default=datetime.date)  #date of the last search asks
    
    def __init__(self, keyword , tldLang,  data_date, search_date):
        self.keyword = keyword
        self.tldLang = tldLang
        self.data_date = data_date
        self.search_date = search_date

#Queries  / Expressions / Keywords  searches by username
class KeywordUser(db.Model):
    __tablename__="keyworduser"
    id = db.Column(db.Integer, primary_key=True)
    keywordId = db.Column(db.Integer)   #id in the keyword Table
    keyword = db.Column(db.String(200))
    tldLang = db.Column(db.String(50))  #google tld + lang
    username  = db.Column(db.String(15))  #
    data_date = db.Column(db.Date, nullable=False, default=datetime.date)  #date of the last data update
    search_date = db.Column(db.Date, nullable=False, default=datetime.date)  #date of the last search asks
    
    def __init__(self, keywordId, keyword , tldLang, username, data_date ,  search_date):
        self.keywordId = keywordId
        self.keyword = keyword
        self.tldLang = tldLang
        self.username = username
        self.data_date = data_date  
        self.search_date = search_date
      
 #Positions 
class Position(db.Model):
    __tablename__="position"
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(200))
    tldLang = db.Column(db.String(50))  #google tld + lang
    page = db.Column(db.String(300))
    position = db.Column(db.Integer)
    source= db.Column(db.String(20))
    search_date = db.Column(db.Date, nullable=False, default=datetime.date)
    
    def __init__(self, keyword , tldLang, page, position, source, search_date):
        self.keyword = keyword
        self.tldLang = tldLang
        self.page = page
        self.position = position
        self.source = source
        self.search_date = search_date
        
        
 #Page content 
class Page(db.Model):
    __tablename__="page"
    id = db.Column(db.Integer, primary_key=True)
    page = db.Column(db.String(300))
    statusCode= db.Column(db.Integer)
    html= db.Column(db.Text)
    encoding = db.Column(db.String(20))
    elapsedTime =  db.Column(db.Float)  #could be interesting for future purpose.
    body= db.Column(db.Text)
    search_date = db.Column(db.Date, nullable=False, default=datetime.date)
    
    def __init__(self, page , statusCode, html, encoding, elapsedTime, body, search_date):
        self.page = page
        self.statusCode = statusCode
        self.html = html
        self.encoding =  encoding
        self.elapsedTime =  elapsedTime
        self.body =  body
        self.search_date = search_date
    
##############
db.create_all()  #create database and tables if not exist
db.session.commit() #execute previous instruction

#Create an admin if not exists
exists = db.session.query(
    db.session.query(User).filter_by(username=myconfig.myAdminLogin).exists()
).scalar()

if  not exists :
    hashed_password = generate_password_hash(myconfig.myAdminPwd, method='sha256')
    administrator = User(myconfig.myAdminLogin, myconfig.myAdminEmail, hashed_password, 0)
    db.session.add(administrator)
    db.session.commit()  #execute
#####   
#create upload/dowload directory for admin
myDirectory = myScriptDirectory+myconfig.UPLOAD_SUBDIRECTORY+"/"+myconfig.myAdminLogin
if not os.path.exists(myDirectory):
    os.makedirs(myDirectory)
    
#Create a guest if not exists
exists = db.session.query(
    db.session.query(User).filter_by(username=myconfig.myGuestLogin).exists()
).scalar()


if  not exists :
    hashed_password = generate_password_hash(myconfig.myGuestPwd, method='sha256')
    guest = User(myconfig.myGuestLogin, myconfig.myGuestEmail, hashed_password, 4)
    db.session.add(guest)
    db.session.commit() #execute
#####   

#create upload/dowload directory for guest
myDirectory = myScriptDirectory+myconfig.UPLOAD_SUBDIRECTORY+"/"+myconfig.myGuestLogin
if not os.path.exists(myDirectory):
    os.makedirs(myDirectory)

#init login_manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

#######################################################
#Save session data in a global DataFrame depending on user_id
global dfSession
dfSession = pd.DataFrame(columns=['user_id', 'userName', 'role', 'keyword', 'tldLang', 'keywordId',  'keywordUserId'])
dfSession.set_index('user_id', inplace=True)
dfSession.info()

#for tfidf counts
def top_tfidf_feats(row, features, top_n=25):
    ''' Get top n tfidf values in row and return them with their corresponding feature names.'''
    topn_ids = np.argsort(row)[::-1][:top_n]
    top_feats = [(features[i], row[i]) for i in topn_ids]
    df = pd.DataFrame(top_feats)
    df.columns = ['feature', 'value']
    return df

def top_mean_feats(Xtr, features, grp_ids=None,  top_n=25):
    ''' Return the top n features that on average are most important amongst documents in rows
        indentified by indices in grp_ids. '''
    if grp_ids:
        D = Xtr[grp_ids].toarray()
    else:
        D = Xtr.toarray()

    #D[D < min_tfidf] = 0 #keep all values
    tfidf_means = np.mean(D, axis=0)
    return top_tfidf_feats(tfidf_means, features, top_n)


#Best for original Keywords
def top_nonzero_mean_feats(Xtr, features, grp_ids=None, top_n=25):
    ''' Return the top n features that on nonzero average are most important amongst documents in rows
        indentified by indices in grp_ids. '''
    if grp_ids:
        D = Xtr[grp_ids].toarray()
    else:
        D = Xtr.toarray()

    #D[D < min_tfidf] = 0
    tfidf_nonzero_means = np.nanmean(np.where(D!=0,D,np.nan), axis=0)  #change 0 in NaN
    return top_tfidf_feats(tfidf_nonzero_means, features, top_n)



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#Forms
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

#we don't use this for the moment
class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    role = 4
   
#search keywords by keyword
class SearchForm(FlaskForm):
    myTLDLang = myconfig.myTLDLang
    keyword = StringField('keyword / Expression', validators=[InputRequired(), Length(max=200)])
    tldLang = SelectField('Country - Language', choices=myTLDLang,  validators=[InputRequired()]) 

############### other functions
#####Get strings from tags
def getStringfromTag(tag="h1", soup="") :
    theTag = soup.find_all(tag)
    myTag = ""
    for x in theTag:
        myTag= myTag + " " + x.text.strip()
    return myTag.strip()   

#remove comments and non visible tags
def tag_visible(element):
    if element.parent.name in ['style', 'script', 'head', 'title', 'meta', '[document]']:
        return False
    if isinstance(element, Comment):
        return False
    return True

 

def strip_accents(text, encoding='utf-8'):
    """
    Strip accents from input String.

    :param text: The input string.
    :type text: String.

    :returns: The processed String.
    :rtype: String.
    """
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode(encoding)
    return str(text)


# Get a random user agent.
def getRandomUserAgent(userAgentsList, userAgentLanguage):
    theUserAgent = random.choice(userAgentsList)
    if len(userAgentLanguage) > 0 :
        theUserAgent = theUserAgent.replace("{{tagLang}}","; "+str(userAgentLanguage))
    else :
         theUserAgent = theUserAgent.replace("{{tagLang}}",""+str(userAgentLanguage))
    return theUserAgent



#ngrams in list
def words_to_ngrams(words, n, sep=" "):
    return [sep.join(words[i:i+n]) for i in range(len(words)-n+1)]

#one-gram tokenizer
tokenizer = nltk.RegexpTokenizer(r'\w+')  


####################  WebSite ##################################
#Routes 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('tfidfkeywordssuggest'))  #go to the keywords Suggest page
            return '<h1>Invalid password</h1>'
        return '<h1>Invalid username</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('login.html', form=form)

#Not used here.
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return '<h1>New user has been created!</h1>'
       #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'
    return render_template('signup.html', form=form)

#Not used here.
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.username)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))



#Route tfidfkeywordssuggest
@app.route('/tfidfkeywordssuggest',methods=['GET', 'POST'])
@login_required
def tfidfkeywordssuggest():
    print("tfidfkeywordssuggest")
    #print("g.userId="+str(g.userId))
    if current_user.is_authenticated:   #always because  @login_required
        print("UserId= "+str(current_user.get_id()))
        myUserId = current_user.get_id()
        print("UserName = "+current_user.username)
        dfSession.loc[ myUserId, 'userName'] = current_user.username #Save Username for userId

        
    #make sure we have a good Role
    if current_user.role is None or current_user.role > 4 or  current_user.role <0  :
        dfSession.loc[ myUserId,'role'] =  4  #4 is for guest 
    else :
       dfSession.loc[ myUserId,'role'] = current_user.role
    myRole = dfSession.loc[ myUserId,'role']
    
    #count searches in a day
    myLimitReached = False
    mySearchesCount = db.session.query(KeywordUser).filter_by(username=current_user.username, search_date=date.today()).count()
    print("mySearchesCount="+str(mySearchesCount))
    print(" myconfig.myMaxSearchesByDay[myRole]="+str(myconfig.myMaxSearchesByDay[myRole]))
    if (mySearchesCount >= myconfig.myMaxSearchesByDay[myRole]):
        myLimitReached=True
    
    #raz value
    dfSession.loc[myUserId,'keyword'] = ""
    dfSession.loc[myUserId,'tldLang'] ="" 
    
   
    form = SearchForm()
    if form.validate_on_submit():
        dfSession.loc[myUserId,'keyword']  = form.keyword.data  #save in session variable
        dfSession.loc[myUserId,'tldLang'] =  form.tldLang.data   #save in session variable
       

    dfSession.head()
    return render_template('tfidfkeywordssuggest.html', name=current_user.username,  form=form,
                            keyword = form.keyword.data , tldLang =  form.tldLang.data, 
                            role =myRole, MaxResults=myconfig.myMaxResults[myRole],  limitReached=myLimitReached)

                           

@app.route('/progress')
def progress():
    print("progress")
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
    dfScrap = pd.DataFrame(columns=['keyword', 'tldLang',  'page', 'position', 'source', 'search_date'])
    def generate(dfScrap, myUserId ):
        myUserName=dfSession.loc[ myUserId,'userName']
        myRole = dfSession.loc[ myUserId,'role']
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        print("myUserId : "+myUserId)
        print("myUserName : "+myUserName)
        print("myRole : "+str(myRole))
        print("myKeyword : "+myKeyword)
        print("myTLDLang : "+myTLDLang)
        print("myKeywordId : "+str(myKeywordId))
        
        mySearchesCount = db.session.query(KeywordUser).filter_by(username=myUserName, search_date=date.today()).count()
        print("mySearchesCount="+str(mySearchesCount))
        print(" myconfig.myMaxSearchesByDay[myRole]="+str(myconfig.myMaxSearchesByDay[myRole]))
        if (mySearchesCount >= myconfig.myMaxSearchesByDay[myRole] ):
            
            myKeyword=""
            myTLDLang=""
            myShow=-1   #Error 
            yield "data:" + str(myShow) + "\n\n"   #to show error

        ##############################
        #run 
        ###############################
        if ( len(myKeyword) > 0 and len(myTLDLang) >0)  :
            myDate=date.today()
            print('myDate='+str(myDate))
            goSearch=False  #do we made a new search in Google ?
            #did anybody already made this search during the last x days ????
            firstKWC = db.session.query(Keyword).filter_by(keyword=myKeyword, tldLang=myTLDLang).first()
            #lastSearchDate = Keyword.query.filter(keyword==myKeyword, tldLang==myTLDLang ).first().format('search_date')
            if firstKWC is None:
                goSearch=True
            else:
                myKeywordId=firstKWC.id
                dfSession.loc[ myUserId,'keywordId']=myKeywordId   #Save in the dfSession
                print("last Search Date="+ str(firstKWC.search_date))
                Delta =  myDate - firstKWC.search_date
                print(" Delta  in days="+str(Delta.days))
                if Delta.days > myconfig.myRefreshDelay :  #30 by defaukt
                    goSearch=True
                 
            ###############################################
            #  Search in Google  and scrap Urls 
            ###############################################
            
            if ( len(myKeyword) > 0 and len(myTLDLang) >0 and goSearch) :
                
                #get  default language for tld  
                myTLD = myconfig.dfTLDLanguages.loc[myTLDLang, 'tld']
                #myTLD=myTLD.strip()
                print("myTLD="+myTLD+"!")
                myHl = str(myconfig.dfTLDLanguages.loc[myTLDLang, 'hl'])
               #myHl=myHl.strip()
                print("myHl="+myHl+"!")
                myLanguageResults = str(myconfig.dfTLDLanguages.loc[myTLDLang, 'lr'])
                #myLanguageResults=myLanguageResults.strip()
                print("myLanguageResults="+myLanguageResults+"!")
                myCountryResults = str(myconfig.dfTLDLanguages.loc[myTLDLang, 'cr'])
                #myCountryResults=myCountryResults.strip()
                print("myCountryResults="+myCountryResults+"!")
                myUserAgentLanguage = str(myconfig.dfTLDLanguages.loc[myTLDLang, 'userAgentLanguage'])
                #myCountryResults=myCountryResults.strip()
                print("myUserAgentLanguage="+myUserAgentLanguage+"!")                              
                
                ###############################
                # Google Scrap 
                ###############################
                myNum=10
                myStart=0
                myStop=10 #get by ten 
                myMaxStart=myconfig.myMaxPagesToScrap  #only 3 for test 10 in production
                #myTbs= "qdr:m"   #rsearch only last month not used
                #tbs=myTbs,
                #pause may be long to avoir blocking from Google
                myLowPause=myconfig.myLowPause
                myHighPause=myconfig.myHighPause
                nbTrials = 0
                #this may be long 

                while myStart <  myMaxStart:
                    myShow= int(round(((myStart*50)/myMaxStart)+1)) #for the progress bar
                    yield "data:" + str(myShow) + "\n\n" 
                    print("PASSAGE NUMBER :"+str(myStart))
                    print("Query:"+myKeyword)
                    #change user-agent and pause to avoid blocking by Google
                    myPause = random.randint(myLowPause,myHighPause)  #long pause
                    print("Pause:"+str(myPause))
                    #change user_agent  and provide local language in the User Agent
                    myUserAgent =  getRandomUserAgent(myconfig.userAgentsList, myUserAgentLanguage) 
                    #myUserAgent = googlesearch.get_random_user_agent()
                    print("UserAgent:"+str(myUserAgent))
                    df = pd.DataFrame(columns=['query', 'page', 'position', 'source']) #working dataframe
                    #myPause=myPause*(nbTrials+1)  #up the pause if trial get nothing
                    #print("Pause:"+str(myPause))
                    try  :
                        urls = googlesearch.search(query=myKeyword, tld=myTLD, lang=myHl, safe='off', 
                                                   num=myNum, start=myStart, stop=myStop, domains=None, pause=myPause, 
                                                   country=myCountryResults, extra_params={'lr':  myLanguageResults}, tpe='',  user_agent=myUserAgent) 
         
                        df = pd.DataFrame(columns=['keyword', 'tldLang',  'page', 'position', 'source', 'search_date'])
                        for url in urls :
                            print("URL:"+url)
                            df.loc[df.shape[0],'page'] = url
                        df['keyword'] = myKeyword  #fill with current keyword
                        df['tldLang'] = myTLDLang  #fill with current country / tld lang
                        df['position'] = df.index.values + 1 + myStart #position = index +1 + myStart
                        df['source'] = "Scrap"  #fill with source origin  here scraping Google 
                        #other potentials options : Semrush, Yooda Insight...
                        df['search_date'] = myDate
                        dfScrap = pd.concat([dfScrap, df], ignore_index=True) #concat scraps
                        # time.sleep(myPause) #add another  pause
                        if (df.shape[0] > 0):
                            nbTrials = 0
                            myStart += 10
                        else :
                            nbTrials +=1
                            if (nbTrials > 3) :
                                nbTrials = 0
                                myStart += 10
                            #myStop += 10
                    except :
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        print("ERROR")
                        print(exc_type.__name__)
                        print(exc_value)
                        print(exc_traceback)
                       # time.sleep(600) #add a big pause if you get an error.
                #/while myStart <  myMaxStart:
            
                #dfScrap.info()
                dfScrapUnique=dfScrap.drop_duplicates()  #remove duplicates
                #dfScrapUnique.info()
                #Save in csv an json  if needed
                #dfScrapUnique.to_csv("dfScrapUnique.csv", sep=myconfig.myCsvSep, encoding='utf-8', index=False)  
                #dfScrapUnique.to_json("dfScrapUnique.json")     
                
                #Bulk save in position table
                #save dataframe in table Position
                dfScrapUnique.to_sql('position', con=db.engine, if_exists='append', index=False)

        
                myShow=50
                yield "data:" + str(myShow) + "\n\n"   #to show 50 %
        
                #/end search in Google 
        
                ###############################
                #  Go to get data from urls
                ###############################
                #read urls to crawl in Position table
                dfUrls =   pd.read_sql_query(db.session.query(Position).filter_by(keyword= myKeyword, tldLang= myTLDLang).statement, con=db.engine)
                dfUrls.info()  
        
       
                ###### filter extensions
                extensionsToCheck = ('.7z','.aac','.au','.avi','.bmp','.bzip','.css','.doc',
                                     '.docx','.flv','.gif','.gz','.gzip','.ico','.jpg','.jpeg',
                                     '.js','.mov','.mp3','.mp4','.mpeg','.mpg','.odb','.odf',
                                     '.odg','.odp','.ods','.odt','.pdf','.png','.ppt','.pptx',
                                     '.psd','.rar','.swf','.tar','.tgz','.txt','.wav','.wmv',
                                     '.xls','.xlsx','.xml','.z','.zip')

                indexGoodFile= dfUrls ['page'].apply(lambda x : not x.endswith(extensionsToCheck) )
                dfUrls2=dfUrls.iloc[indexGoodFile.values]
                dfUrls2.reset_index(inplace=True, drop=True)
                dfUrls2.info()
                
                #######################################################
                # Scrap Urls only one time
                ########################################################
                myPagesToScrap = dfUrls2['page'].unique()
                dfPagesToScrap= pd.DataFrame(myPagesToScrap, columns=["page"])
                #dfPagesToScrap.size #9

                #add new variables
                dfPagesToScrap['statusCode'] = np.nan
                dfPagesToScrap['html'] = ''  #
                dfPagesToScrap['encoding'] = ''  #
                dfPagesToScrap['elapsedTime'] = np.nan

                myShow=60
                yield "data:" + str(myShow) + "\n\n"   #to show 60%

                stepShow = 10/len(dfPagesToScrap)
                print("stepShow scrap urls="+str(stepShow ))
                for i in range(0,len(dfPagesToScrap)) :
                    url = dfPagesToScrap.loc[i, 'page']
                    print("Page i = "+url+" "+str(i))
                    startTime = time.time()
                    try:
                       #html = urllib.request.urlopen(url).read()$
                       r = requests.get(url,timeout=(5, 14))  #request
                       dfPagesToScrap.loc[i,'statusCode'] = r.status_code
                       print('Status_code '+str(dfPagesToScrap.loc[i,'statusCode']))
                       if r.status_code == 200. :   #can't decode utf-7
                           print("Encoding="+str(r.encoding))
                           dfPagesToScrap.loc[i,'encoding'] = r.encoding
                           if   r.encoding == 'UTF-7' :  #don't get utf-7 content pb with db
                               dfPagesToScrap.loc[i, 'html'] =""
                               print("UTF-7 ok page ") 
                           else :
                               dfPagesToScrap.loc[i, 'html'] = r.text
                               #au format texte r.text - pas bytes : r.content
                               print("ok page ") 
                           #print(dfPagesToScrap.loc[i, 'html'] )
                    except:
                       print("Error page requests ") 
                
                    endTime= time.time()   
                    dfPagesToScrap.loc[i, 'elapsedTime'] =  endTime - startTime
                    print('pas scrap URL='+str(round((stepShow*i))))
                    myShow=60+round((stepShow*i))
                    yield "data:" + str(myShow) + "\n\n"   #to show 60%
                #/
    
                dfPagesToScrap.info()
        
                #merge dfUrls2, dfPagesToScrap  -> dfUrls3
                dfUrls3 = pd.merge(dfUrls2, dfPagesToScrap, on='page', how='left') 
                #keep only  status code = 200   
                dfUrls3 = dfUrls3.loc[dfUrls3['statusCode'] == 200]  
                #dfUrls3 = dfUrls3.loc[dfUrls3['encoding'] != 'UTF-7']   #can't save utf-7  content in db ????
                dfUrls3 = dfUrls3.loc[dfUrls3['html'] != ""] #don't get empty html
                dfUrls3.reset_index(inplace=True, drop=True)    
                dfUrls3.info() # 
                dfUrls3 = dfUrls3.dropna()  #remove rows with at least one na
                dfUrls3.reset_index(inplace=True, drop=True) 
                
                dfUrls3.info() #
        
                myShow=70
                yield "data:" + str(myShow) + "\n\n"   #to show 70%
        
        
                #Get Body contents from html
                dfUrls3['body'] = ""  #Empty String
                stepShow = 10/len(dfUrls3)
                for i in range(0,len(dfUrls3)) :
                    print("Page keyword tldLang  i = "+ dfUrls3.loc[i, 'page']+" "+ dfUrls3.loc[i, 'keyword']+" "+ dfUrls3.loc[i, 'tldLang']+" "+str(i))
                    encoding =  dfUrls3.loc[i, 'encoding'] #get previously
                    print("get body content encoding"+encoding)
                    try:
                        soup = BeautifulSoup( dfUrls3.loc[i, 'html'], 'html.parser')
                    except :
                        soup="" 
               
                    if len(soup) != 0 :
                        #TBody Content
                        texts = soup.findAll(text=True)
                        visible_texts = filter(tag_visible, texts)  
                        myBody = " ".join(t.strip() for t in visible_texts)
                        myBody=myBody.strip()
                        #myBody = strip_accents(myBody, encoding).lower()  #think  to do a global clean instead
                        myBody=" ".join(myBody.split(" "))  #remove multiple spaces
                        #print(myBody)
                        dfUrls3.loc[i, 'body'] = myBody
                 
                    print('pas body content='+str(round((stepShow*i))))
                    myShow=70+round((stepShow*i))
                    yield "data:" + str(myShow) + "\n\n"   #to show 70% ++
            
                ################################   
                #save pages in database table page
                dfPages= dfUrls3[['page', 'statusCode', 'html', 'encoding', 'elapsedTime', 'body', 'search_date']]
                dfPagesUnique = dfPages.drop_duplicates(subset='page')  #remove duplicate's pages
                dfPagesUnique = dfPagesUnique.dropna()  #remove na
                dfPagesUnique.reset_index(inplace=True, drop=True) #reset index
                #dfPagesUnique.to_sql('page', con=db.engine, if_exists='append', index=False)  #duplicate risks !!
        
                #save to see what we get 
                #dfPagesUnique.to_csv("dfPagesUnique.csv", sep=myconfig.myCsvSep , encoding='utf-8', index=False)       
                #dfPagesUnique.to_json("dfPagesUnique.json")   
                myShow=80
                yield "data:" + str(myShow) + "\n\n"   #to show 90%  
        
                #insert or update in Page table
                print("len df="+str( len(dfPagesUnique)))
                
                
                stepShow = 10/len(dfPagesUnique)
                for i in range(0, len(dfPagesUnique)) :
                    print("i="+str(i))
                    print("page = "+dfPagesUnique.loc[i, 'page'])

                    dbPage = db.session.query(Page).filter_by(page=dfPagesUnique.loc[i, 'page']).first()
                    if dbPage is None :
                        print("nothing insert index = "+str(i))
                        newPage = Page(page=dfPagesUnique.loc[i, 'page'],
                                       statusCode=dfPagesUnique.loc[i, 'statusCode'],
                                       html=dfPagesUnique.loc[i, 'html'],
                                       encoding=dfPagesUnique.loc[i, 'encoding'],
                                       elapsedTime=dfPagesUnique.loc[i, 'elapsedTime'],
                                       body=dfPagesUnique.loc[i, 'body'],
                                       search_date=dfPagesUnique.loc[i, 'search_date'])
                        db.session.add(newPage)
                        db.session.commit()
                            
                    else :
                        print("exists update  id = "+str(dbPage.id))
                        #update values
                        dbPage.page=dfPagesUnique.loc[i, 'page']
                        dbPage.statusCode=dfPagesUnique.loc[i, 'statusCode']
                        dbPage.html=dfPagesUnique.loc[i, 'html']
                        dbPage.encoding=dfPagesUnique.loc[i, 'encoding']
                        dbPage.elapsedTime=dfPagesUnique.loc[i, 'elapsedTime']
                        dbPage.body=dfPagesUnique.loc[i, 'body'],
                        dbPage.search_date=dfPagesUnique.loc[i, 'search_date']
                        db.session.commit()
                        
                    myShow=80+round((stepShow*i))
                    yield "data:" + str(myShow) + "\n\n"   #to show 80% ++
           
           
                ###End Google search and scrap content page
          
            
            
            myShow=90
            yield "data:" + str(myShow) + "\n\n"   #to show 90%    
            
            
            ###################################    
            #update keyword and keyworduser
            ###################################
            #need to get firtsKWC in keyword table before
            firstKWC = db.session.query(Keyword).filter_by(keyword=myKeyword, tldLang=myTLDLang).first()
            #Do we just process a new Google Scrap and  Page Scrap ?
            if goSearch :
                myDataDate = myDate #Today
            else :
                if  firstKWC is None :
                    myDataDate = myDate  #Today
                else :
                    myDataDate = firstKWC.data_date  #old data date 
            
            #do somebody already process a research before ?
            if  firstKWC is None :
                #insert
                newKeyword = Keyword(keyword= myKeyword, tldLang=myTLDLang ,  data_date=myDataDate, search_date=myDate)
                db.session.add(newKeyword)
                db.session.commit()
                db.session.refresh(newKeyword)
                db.session.commit()
                myKeywordId = newKeyword.id   #
            else :
                myKeywordId = firstKWC.id
               #update
                firstKWC.data_date=myDataDate  
                firstKWC.search_date=myDate  
                db.session.commit()   
                
            myShow=91
            yield "data:" + str(myShow) + "\n\n"   #to show 91%    
            
            #for KeywordUSer
            #Did this user  already process this search ?
            print(" myKeywordId="+str(myKeywordId))
            dfSession.loc[ myUserId,'keywordId']=myKeywordId 
            
            dbKeywordUser = db.session.query(KeywordUser).filter_by(keyword= myKeyword, tldLang=myTLDLang, username=myUserName).first()
            if dbKeywordUser is None :
               print("insert index  new Keyword for = "+ myUserName)
               newKeywordUser = KeywordUser(keywordId= myKeywordId, keyword= myKeyword, 
                                            tldLang=myTLDLang , username= myUserName, data_date=myDataDate, search_date=myDate)
               db.session.add(newKeywordUser)
               db.session.commit()
               myKeywordUserId=newKeywordUser.id
            else :
                myKeywordUserId=dbKeywordUser.id   #for the name
                print("exists update only myDataDate" )
                #update values for the current user
                dbKeywordUser.data_date=myDataDate
                dbKeywordUser.search_date=myDate
                db.session.commit()        
        
            ######################################################
            #######################  tf-idf files generation
            dfSession.loc[ myUserId,'keywordUserId']=myKeywordUserId 
            #Make sure download directory exists
            myDirectory =  myScriptDirectory+myconfig.UPLOAD_SUBDIRECTORY+"/"+myUserName
            if not os.path.exists(myDirectory):
                os.makedirs(myDirectory)
            
           
            myKeywordFileNameString=strip_accents(myKeyword).lower()
            myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
            myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
            myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
            myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
            print("myKeywordFileNameString = "+myKeywordFileNameString)
            
            myShow=92
            yield "data:" + str(myShow) + "\n\n"   #to show 92%    
        
            #Read in position  table to get  the pages list in dataframe
        
            dfPagesUnique =   pd.read_sql_query(db.session.query(Position, Page).filter_by(keyword= myKeyword, tldLang= myTLDLang).filter(Position.page==Page.page).statement, con=db.engine)
            dfPagesUnique.info()  
        
            #Remove apostrophes and quotes
            print("Remove apostrophes and quotes")  
            stopQBody = dfPagesUnique['body'].apply(lambda x: x.replace("\"", " ")) 
            stopAQBody =stopQBody.apply(lambda x: x.replace("'", " "))    

            
            #tolower
            stopTolowerBody =stopAQBody.apply(lambda x: x.lower())



            #Remove english stopwords 
            print("Remove English stopwords")      
            stopEnglish =  stopwords.words('english')
            #print(stopEnglish)
            stopEnglishBody =   stopTolowerBody.apply(lambda x: ' '.join([word for word in str(x).split() if word not in stopEnglish]))
            #print(stopEnglishBody)
         			
        
            #Get the good local stopwords
            stopLocalLanguage = myconfig.dfTLDLanguages.loc[myTLDLang, 'stopWords']
            if   (stopLocalLanguage in stopwords.fileids()) :
                 print(" stopLocalLanguage="+ stopLocalLanguage)
                 stopLocal =  stopwords.words(stopLocalLanguage)    
                 print("Remove local Stop Words")     
                 stopLocalBody =    stopEnglishBody.apply(lambda x: ' '.join([word for word in x.split() if word not in (stopLocal)]))
            else :
                stopLocalBody = stopEnglishBody
                
        
            print("Remove Special Characters")              
            stopSCBody =  stopLocalBody.apply(lambda x: re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", " ", x))
        
            print("Remove Numbers")       
            #remove numbers 
            stopNumbersBody =    stopSCBody.apply(lambda x: ''.join(i for i in x if not i.isdigit()))     
       
            print("Remove Multiple Spaces")    
            stopSpacesBody = stopNumbersBody.apply(lambda x: re.sub(" +", " ", x))
            
            #print("Encode in UTF-8")
            #stopEncodeBody = stopSpacesBody.apply(lambda x: x.encode('utf-8', 'ignore'))
            stopEncodeBody= stopSpacesBody #already in utf-8
            #create "clean" Corpus
            corpus =  stopEncodeBody.tolist()
            print('corpus Size='+str(len(corpus)))
            myMaxFeatures = myconfig.myMaxFeatures
            myMaxResults = myconfig.myMaxResults
         
            print("Popular Expressions")
            print("Mean for min to max words")
            tf_idf_vectMinMax = TfidfVectorizer(ngram_range=(myconfig.myMinNGram,myconfig.myMaxNGram), max_features=myMaxFeatures) # , norm=None
            XtrMinMax = tf_idf_vectMinMax.fit_transform(corpus)
            featuresMinMax = tf_idf_vectMinMax.get_feature_names()
            myTopNMinMax=min(len(featuresMinMax), myMaxResults[myRole])
            dfTopMinMax =  top_mean_feats(Xtr=XtrMinMax, features=featuresMinMax, grp_ids=None, top_n= myTopNMinMax)
            dfTopMinMax.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-min-max.csv", sep=myconfig.myCsvSep , encoding='utf-8', index=False) 
      
        
        
            myShow=93
            yield "data:" + str(myShow) + "\n\n"   #to show 93%    
            
            print("for 1 word")   
            #Keywords suggestion
            #    for 1 word
            tf_idf_vect1 = TfidfVectorizer(ngram_range=(1,1), max_features=myMaxFeatures) # , norm=None
            Xtr1 = tf_idf_vect1.fit_transform(corpus)
            features1 = tf_idf_vect1.get_feature_names()
            myTopN1=min(len(features1), myMaxResults[myRole])
            dfTop1 =  top_mean_feats(Xtr=Xtr1, features=features1, grp_ids=None, top_n=myTopN1)
            dfTop1.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-1.csv", sep=myconfig.myCsvSep , encoding='utf-8', index=False) 

            #for 2
            print("for 2 words")   
            tf_idf_vect2 = TfidfVectorizer(ngram_range=(2,2), max_features=myMaxFeatures) # , norm=None
            Xtr2 = tf_idf_vect2.fit_transform(corpus)
            features2 = tf_idf_vect2.get_feature_names()
            myTopN2=min(len(features2), myMaxResults[myRole])
            dfTop2 =  top_mean_feats(Xtr=Xtr2, features=features2, grp_ids=None, top_n=myTopN2)
            dfTop2.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-2.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 

            #for 3
            print("for 3 words")   
            tf_idf_vect3 = TfidfVectorizer(ngram_range=(3,3), max_features=myMaxFeatures) # , norm=None
            Xtr3 = tf_idf_vect3.fit_transform(corpus)
            features3 = tf_idf_vect3.get_feature_names()
            myTopN3=min(len(features3), myMaxResults[myRole])
            dfTop3 =  top_mean_feats(Xtr=Xtr3, features=features3, grp_ids=None, top_n=myTopN3)
            dfTop3.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-3.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 

            myShow=94
            yield "data:" + str(myShow) + "\n\n"   #to show 94%   

            #for 4
            print("for 4 words")   
            tf_idf_vect4 = TfidfVectorizer(ngram_range=(4,4), max_features=myMaxFeatures) # , norm=None
            Xtr4 = tf_idf_vect4.fit_transform(corpus)
            features4 = tf_idf_vect4.get_feature_names()
            myTopN4=min(len(features4), myMaxResults[myRole])
            dfTop4 =  top_mean_feats(Xtr=Xtr4, features=features4, grp_ids=None, top_n=myTopN4)
            dfTop4.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-4.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 

            #for 5
            print("for 5 words")   
            tf_idf_vect5 = TfidfVectorizer(ngram_range=(5,5), max_features=myMaxFeatures) # , norm=None
            Xtr5 = tf_idf_vect5.fit_transform(corpus)
            features5 = tf_idf_vect5.get_feature_names()
            myTopN5=min(len(features5), myMaxResults[myRole])
            dfTop5 =  top_mean_feats(Xtr=Xtr5, features=features5, grp_ids=None, top_n=myTopN5)
            dfTop5.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-5.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False)
        
            #for 6
            print("for 6 words")   
            tf_idf_vect6 = TfidfVectorizer(ngram_range=(6,6), max_features=myMaxFeatures) # , norm=None
            Xtr6 = tf_idf_vect6.fit_transform(corpus)
            features6 = tf_idf_vect6.get_feature_names()
            myTopN6=min(len(features6), myMaxResults[myRole])
            dfTop6 =  top_mean_feats(Xtr=Xtr6, features=features6, grp_ids=None, top_n=myTopN6)
            dfTop6.to_csv(myDirectory+"/pop-"+myKeywordFileNameString+"-6.csv", sep=myconfig.myCsvSep, encoding='utf-8', index=False)
       
            myShow=95
            yield "data:" + str(myShow) + "\n\n"   #to show 95%   
        
        
            print("Original Expressions")
            print("NZ Mean for min to max words")
            dfTopNZMinMax =  top_nonzero_mean_feats(Xtr=XtrMinMax, features=featuresMinMax, grp_ids=None, top_n=myTopNMinMax)
            dfTopNZMinMax.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-min-max.csv", sep=myconfig.myCsvSep, encoding='utf-8', index=False)  

            myShow=96
            yield "data:" + str(myShow) + "\n\n"   #to show 96%   

        
            #for 1
            print("NZ for 1 word")  
            dfTopNZ1 =  top_nonzero_mean_feats(Xtr=Xtr1, features=features1, grp_ids=None, top_n=myTopN1)
            dfTopNZ1.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-1.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 
        
            #for 2
            print("NZ for 2 words")  
            dfTopNZ2 =  top_nonzero_mean_feats(Xtr=Xtr2, features=features2, grp_ids=None, top_n=myTopN2)
            dfTopNZ2.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-2.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 

            myShow=97
            yield "data:" + str(myShow) + "\n\n"   #to show 97%   
        
            #for 3
            print("NZ for 3 words")  
            dfTopNZ3 =  top_nonzero_mean_feats(Xtr=Xtr3, features=features3, grp_ids=None, top_n=myTopN3)
            dfTopNZ3.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-3.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 
        
            #   for 4
            print("NZ for 4 words")  
            dfTopNZ4 =  top_nonzero_mean_feats(Xtr=Xtr4, features=features4, grp_ids=None, top_n=myTopN4)
            dfTopNZ4.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-4.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 
        
            #for 5
            print("NZ for 5 words")  
            dfTopNZ5 =  top_nonzero_mean_feats(Xtr=Xtr5, features=features5, grp_ids=None, top_n=myTopN5)
            dfTopNZ5.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-5.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 


            myShow=99
            yield "data:" + str(myShow) + "\n\n"   #to show 99%   

        
            #for 6
            print("NZ for 6 words")  
            dfTopNZ6 =  top_nonzero_mean_feats(Xtr=Xtr6, features=features6, grp_ids=None, top_n=myTopN6)
            dfTopNZ6.to_csv(myDirectory+"/ori-"+myKeywordFileNameString+"-6.csv",  sep=myconfig.myCsvSep, encoding='utf-8', index=False) 
        
 
        
        
            #Finish
     
            myShow=100
            yield "data:" + str(myShow) + "\n\n"   #to show 100%  and close 
            

            #/run
    #loop  generate  
    return Response(generate(dfScrap, myUserId), mimetype='text/event-stream') 
            
#download keywords File filename
@app.route('/downloadKWF/<path:filename>',  methods=['GET', 'POST'] ) # this is a job for GET, not POST
def downloadKWF(filename):
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myUserName=dfSession.loc[ myUserId,'userName']
    
    print("myUserId="+str(myUserId))
    myScriptDirectory = get_script_directory()
    myDirectory =  myScriptDirectory+myconfig.UPLOAD_SUBDIRECTORY+"/"+myUserName
    myFileName=filename
    print("myFileName="+myFileName)
    return send_file(myDirectory+"/"+myFileName,
                     mimetype='text/csv',
                     attachment_filename=myFileName,
                     as_attachment=True)     
    



#download Popular Keywords  All Keywords
@app.route('/popAllCSV') 
def popAllCSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-min-max.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))   

    
    
    
#download Popular Keywords  1 gram Keywords
@app.route('/pop1CSV') 
def pop1CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-1.csv"
    return redirect(url_for('downloadKWF', filename=myFileName)) 
 
 #download Popular Keywords  2 gram Keywords
@app.route('/pop2CSV') 
def pop2CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-2.csv"
    return redirect(url_for('downloadKWF', filename=myFileName)) 
    
 #download Popular Keywords  3 gram Keywords
@app.route('/pop3CSV') 
def pop3CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-3.csv"
    return redirect(url_for('downloadKWF', filename=myFileName)) 
    
    
 #download Popular Keywords  4 gram Keywords
@app.route('/pop4CSV') 
def pop4CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-4.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))    



 #download Popular Keywords  5 gram Keywords
@app.route('/pop5CSV') 
def pop5CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-5.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))       
    
    
 #download Popular Keywords  5 gram Keywords
@app.route('/pop6CSV') 
def pop6CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="pop-"+myKeywordFileNameString+"-6.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))       
    
########################################################
#  Original Keywords
########################################################
    
 #Dowload Original Keywords    All Keywords
@app.route('/oriAllCSV') 
def oriAllCSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
     

    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-min-max.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))    
            
#download original Keywords  1 gram Keywords
@app.route('/ori1CSV') 
def ori1CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-1.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))      
 
 #download original Keywords  2 gram Keywords
@app.route('/ori2CSV') 
def ori2CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-2.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))  
    
 #download original Keywords  3 gram Keywords
@app.route('/ori3CSV') 
def ori3CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-3.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))  
    
    
 #download original Keywords  4 gram Keywords
@app.route('/ori4CSV') 
def ori4CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-4.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))   



 #download original Keywords  5 gram Keywords
@app.route('/ori5CSV')
def ori5CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-5.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))   
    
 #download original Keywords  5 gram Keywords
@app.route('/ori6CSV') 
def ori6CSV():
    #get Session Variables
    if current_user.is_authenticated:
        myUserId = current_user.get_id()
        print("myUserId="+str(myUserId))
        myKeyword = dfSession.loc[ myUserId,'keyword']
        myTLDLang =  dfSession.loc[myUserId,'tldLang']
        myKeywordId = dfSession.loc[ myUserId,'keywordId']
        myKeywordUserId = dfSession.loc[ myUserId,'keywordUserId']
    
    print("myUserId="+str(myUserId))
    myKeywordFileNameString=strip_accents(myKeyword).lower()
    myKeywordFileNameString =  re.sub(r"[-()\"#/@;:<>{}`+=~|.!?,]", "",myKeywordFileNameString)
    myKeywordFileNameString = "-".join(myKeywordFileNameString.split(" "))  
    myKeywordFileNameString = myKeywordFileNameString+"_"+myTLDLang
    myKeywordFileNameString = str(myKeywordId)+"-"+str(myKeywordUserId)+"_"+myKeywordFileNameString
    print("myKeywordFileNameString = "+myKeywordFileNameString)
    myFileName="ori-"+myKeywordFileNameString+"-6.csv"
    return redirect(url_for('downloadKWF', filename=myFileName))   




if __name__ == '__main__':
    app.run(threaded=True)
   # app.run(debug=True, use_reloader=True)
