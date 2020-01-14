# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 15:41:05 2019

@author: Pierre
"""

import pandas as pd  #for dataframes
import os
import xlrd

#Define your database
...
# Database initialization
if os.environ.get('DATABASE_URL') is None:
    basedir = os.path.abspath(os.path.dirname(__file__))
    myDatabaseURI = 'sqlite:///' + os.path.join(basedir, 'database.db')
else:
    myDatabaseURI  = os.environ['DATABASE_URL']

#define the default upload/download parent directory
UPLOAD_SUBDIRECTORY = "/uploads"

#define an admin and a guest
#change if needed.
myAdminLogin = "admin" 
myAdminPwd = "adminpwd"
myAdminEmail = "admin@example.com"
myGuestLogin = "guest" 
myGuestPwd = "guestpwd"
myGuestEmail = "guest@example.com"


#define Google TLD and languages and stopWords
#see https://developers.google.com/custom-search/docs/xml_results_appendices
#https://www.metamodpro.com/browser-language-codes

#Languages  
dfTLDLanguages  = pd.read_excel('configdata/tldLang.xlsx')
dfTLDLanguages.fillna('',inplace=True)
if len(dfTLDLanguages) == 0 :
#if 1==1 :
    data =  [['google.com', 'United States', 'com', 'en', 'lang_en', 'countryUS',  'en-us', 'english',  'United States', 'en - English'],
             ['google.co.uk',  'United Kingdom', 'co.uk', 'en',  'lang_en', 'countryUK',   'en-uk', 'english',  'United Kingdom', 'en - English'], 
             ['google.de', 'Germany', 'de','de',  'lang_de',  'countryDE',  'de-de', 'german', 'Germany', 'de - German'], 
             ['google.fr',  'France', 'fr', 'fr',  'lang_fr',  'countryFR', 'fr-fr',  'french',  'France', 'fr - French']]
    dfTLDLanguages =  pd.DataFrame(data, columns = ['tldLang', 'description', 'tld', 'hl', 'lr', 'cr', 'userAgentLanguage', 'stopWords', 'countryName', 'ISOLanguage' ]) 
    
myTLDLang = [tuple(r) for r in dfTLDLanguages[['tldLang', 'description']].values]
#print(myTLDLang)
dfTLDLanguages = dfTLDLanguages.drop_duplicates()
dfTLDLanguages.set_index('tldLang', inplace=True)
dfTLDLanguages.info()
#dfTLDLanguages['userAgentLanguage']
#USER AGENTS 
with open('configdata/user_agents-taglang.txt') as f:
  userAgentsList = f.read().splitlines() 

#pauses to scrap Google 
myLowPause=2
myHighPause=6
#define max pages to scrap on Google (30 is enough 100 max) 
myMaxPagesToScrap=30
#define refresh delay (usually 30 days)
myRefreshDelay = 30
myMaxFeatures = 10000  #to calculate tf-idf
#Name of account type 
myAccountTypeName=['Admin', 'Gold',  'Silver','Bronze', 'Guest',]
#max number of results to keep in TF-IDF depending on role
myMaxResults=[10000, 10000,  5000, 1000, 100]
#max searches by day depending on role
myMaxSearchesByDay=[10000, 10000,  1000, 100, 10]
#min ngram
myMinNGram=1  #Not a good idea to change this for the moment
#max ngram
myMaxNGram=6 ##Not a good idea to change this for the moment
#CSV separator
myCsvSep = ","