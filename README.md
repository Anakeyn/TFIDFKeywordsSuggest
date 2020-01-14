# TF-IDF KeywordsSuggest - Version Alpha 0.1 Licence GPL 3
Version 0.1 : change keywordsuggest.py due to change in googlesearch library . Minor bug fixed.

<p align="center">
   <img src="https://user-images.githubusercontent.com/26166630/63529711-703c0200-c505-11e9-94b8-f56cc3a92727.jpg">
</p>

Anakeyn TF-IDF Keywords Suggest is a keywords suggestion tool for SEO and Web Maketing purpose.
This tool searches and stores the first x pages responding to a given keyword in Google. 

Next the system will get the content of the pages in order to find popular and original  keywords/Expressions 
in the subject area. The system works  with a TF-IDF  algorithm.

TF-IDF means term frequency–inverse document frequency. TF-IDF is a numerical statistic that is intended to reflect 
how important a word is to a document in a collection or corpus.

In order to calculate a "global" TF-IDF value we calculate a mean of TF-IDF for each term from all documents to 
find popular expressions and a non-zero mean of each term from all documents for original expressions.

The program is developed in Python in a Web format using Flask (web framework), Jinja2 (web template engine), 
SQLALchemy (Object-relational mapping for SQL databases),Bootstrap (front-end framework) ...

#### STRUCTURE :

<pre>KeywordsSuggest
|   database.db
|   favicon.ico
|   tfidfkeywordssuggest.py
|   license.txt
|   myconfig.py
|   requirements.txt
|   __init__.py
|   
+---configdata
|       tldLang.xlsx
|       user_agents-taglang.txt
|       
+---static
|       Anakeyn_Rectangle.jpg
|       tfidfkeywordssuggest.css
|       Oeil_Anakeyn.jpg
|       signin.css
|       starter-template.css
|              
+---templates
|       index.html
|       tfidfkeywordssuggest.html
|       login.html
|       signup.html
|       
+---uploads</pre>


By default the system works with a SQLite database called database.db which is created the first time you use the program.
The main program is "tfidfkeywordssuggest.py".

Default config variables are in the myconfig.py file including the 2 default users : admin (pwd "adminpwd") 
and guest (pwd "guestpwd")

Other configuration data is available in the configdata subdiretory in 2 files :
tldlang.xlsx : parameters for Google Top Level domains and Search Engines Results Pages languages (358 combinations)
user_agents-taglang.txt :  a list of valid user agents to provide to Google randomly to avoid blocking. (4281)

Static directory contains images and .css files

Templates directory contains .html templates.

Uploads directory is dedicated to create/save all keywords files to download.

The system creates 7 "popular" keywords/expressions files : 1 file with all sizes expression in words, 
and one file for respectively 1, 2, 3, 4, 5 or 6 words expressions.
The same for "original"  keywords/expressions files. 
If available, the system provides a maximum of 10.000 expressions for each file. This could be enough to get ideas :-) 


## How to test the program on your computer :
  
Download the .zip file of this application https://github.com/Anakeyn/TFIDFKeywordsSuggest/archive/master.zip and unzip it in a directory on your computer.

Download and Install Anaconda https://www.anaconda.com/distribution/#download-section

Anaconda will install tools on your computer :

![Anaconda-Tools](https://user-images.githubusercontent.com/26166630/63531569-150c0e80-c509-11e9-94b8-b62a01a490dd.jpg)


Open Anaconda Prompt and go to the directory where you installed the application previously (for example for Windows : cd c:\Users\myname\document\...\...\ 

Make sure you have the file "requirements.txt" in your directory : dir (Windows) or ls (Linux)

To install Library dependencies for the python code.  You need to install these with the command :

For Linux :
while read requirement; do conda install --yes $requirement || pip install $requirement; done < requirements.txt

For Windows :
FOR /F "delims=~" %f in (requirements.txt) DO conda install --yes "%f" || pip install "%f"

![AnacondaPrompt](https://user-images.githubusercontent.com/26166630/63533591-64543e00-c50d-11e9-9942-92a0301b4e0b.jpg)


Next launch Spyder and open the main Python file keywordssuggest.py

![spyder-keywordssuggest](https://user-images.githubusercontent.com/26166630/63534394-5e5f5c80-c50f-11e9-8ffa-34b7dbe76897.jpg)

make sure that you are in the good directory then click on the green arrow to run the Python File.

Next,  open a browser an go to the address http://127.0.0.1:5000 :

![AKS-Home](https://user-images.githubusercontent.com/26166630/63535070-dda16000-c510-11e9-803d-2232a99dabf1.jpg)


Click on "Keywords Suggest" : the system is protected; Provide the defaults admin credentials : admin, adminpwd or the default guest credentials : guest, guestpwd

Next Choose an expression and a Country/Language targeted.

![AKS-Search](https://user-images.githubusercontent.com/26166630/63536173-56a1b700-c513-11e9-8f54-511a6475aa9d.jpg)


The system will search in Google pages responding to the Keyword, save the pages, get the content and calculate a TF-IDF for each term founded in pages. Next it will provides 14 files with up to 10.000 popular or original expressions.


![AKS-Results](https://user-images.githubusercontent.com/26166630/63536838-b5b3fb80-c514-11e9-9582-21aac39c9950.jpg)


As you can, see not all languages are filtered by Google (see here "lr" parameter to get the list : https://developers.google.com/custom-search/docs/xml_results_appendices#lrsp). However, with the country filter and the language specified in the user agent, the results are often exploitable.

Here you will see results of original 2 words expression for "SEO" in Swahili in Democratic Republic of Congo 

![SEO-Swahili-RDC](https://user-images.githubusercontent.com/26166630/63537757-d0876f80-c516-11e9-885b-47dbc7e70f04.jpg)



