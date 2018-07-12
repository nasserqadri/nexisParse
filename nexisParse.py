
from html.parser import HTMLParser
from bs4 import BeautifulSoup, Comment
import os, os.path
from os import path
import re
import gc
from datetime import datetime
import sys
import csv
import dateutil
from dateutil.relativedelta import relativedelta
import string
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords 
import pandas as pd
from pandas import *

sys.setrecursionlimit(10000) 


class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def next_element(elem):
    while elem is not None:
        elem = elem.next_sibling
        if hasattr(elem,"name"):
            return elem



def lexisParse(srcPath, destPath): 

    for dirpath, dirnames, filenames in os.walk(srcPath):
        for i, filename in enumerate([f for f in filenames if f.endswith(".HTML")]):
            docSource = 'NYT' if filename[0:3]=='The' else filename[0:3]
            subDir = dirpath.split('\\')[-1]
            print("processing", os.path.join(dirpath, filename))

            soup = BeautifulSoup(open(os.path.join(dirpath, filename)), "html.parser")

            # remove all comments
            comments = soup.findAll(text=lambda text:isinstance(text, Comment))
            for comment in comments:
                comment.extract()

            pages = []
            dates = []
            docType = []
            aTags = soup.find_all('a')

            for e in soup.findAll('br'):
                e.extract()

            for i, aTag in enumerate(aTags):
                
                keepThisArticle = True #added this for control over whether or not to include op-eds
                page = [str(aTag)]
                
                nextATag = aTag.find_next('a')
                
                elem =  next_element(aTag)
                j = 0;
                gotDate = False
                thisDocType = "REG"
                
                while elem and elem != nextATag:
                    
                    skipThisElement = False
                    j= j+1

                    if elem.name is not None:
                        
                        thisTagText = strip_tags(str(elem.contents))
                        
                        if re.search('We are sorry but there is an error', thisTagText):
                            keepThisArticle= False
                            break

                        # remove '# of # DOCUMENTS' meta 
                        if (re.search('\d of \d* DOCUMENTS',thisTagText)) or (
                            re.search('Copyright \d+ The New York Times',thisTagText)):
                            skipThisElement = True
                            #print('1')
                            

                        # remove article dates - only catches the meta data, not anything in body
                        elif (re.match('\[([a-zA-Z]+) \d*, \d+', thisTagText)) or (re.match('\[LOAD-DATE', thisTagText)) or (re.match('\[CORRECTION-DATE:', thisTagText)):
                            skipThisElement = True

                            #NEED THIS FOR TVNEWS...particularly fox news because fox news' load dates only start after 2003
                            if (re.match('\[([a-zA-Z]+) \d+, \d+', thisTagText)) and not gotDate:
                                dateMatch = re.findall('[a-zA-Z]+ \d*, \d+', thisTagText)
                                if (len(dateMatch) == 0):
                                    keepThisArticle = False
                                    break
                                dateFormatted = datetime.strptime(dateMatch[0], '%B %d, %Y').date()
                                dates.append(dateFormatted)
                                gotDate= True

                        
                        elif (re.match('\[BYLINE:', thisTagText)) or (
                            re.match('\[SECTION:', thisTagText)) or (
                            re.match('\[NEWS SUMMARY', thisTagText)) or (
                            re.match('\[LENGTH:', thisTagText)) or (
                            re.match('\[DATELINE:', thisTagText)) or (
                            re.match('\[URL:', thisTagText)) or (
                            re.match('\[LANGUAGE:', thisTagText)) or (
                            re.match('\[PUBLICATION-TYPE:', thisTagText)) or (
                            re.match('\[\s*The New York Times', thisTagText))  or (
                            re.match('\[\' \',\s*The New York Times', thisTagText)) or (
                            re.match('\[GRAPHIC:', thisTagText)) or (re.match(
                                '\[CORRECTION:', thisTagText)) or (re.match(
                                '\[ The Washington Post', thisTagText)) or (
                            re.match('\[DOCUMENT-TYPE:', thisTagText)) or (re.match(
                                '\[NEW YORK TIMES', thisTagText)) or (re.match(
                                '\[JOURNAL-CODE:', thisTagText)) : 
                            
                            skipThisElement = True
                            
                            if re.match('\[SECTION:', thisTagText):
                                if 'Editorial' in thisTagText:
                                    thisDocType = "OPED"

                        # 9-20-16 - CNN specific
                        elif (re.match('\[(\' \', )?CNN', thisTagText)) or (
                            re.match('\[SHOW:', thisTagText)) or (
                            re.match('\[(\' \', )?HIGHLIGHT:', thisTagText)) or (
                            re.match('\[Transcript #', thisTagText)) or (
                            re.match('\[TRANSCRIPT:', thisTagText)) or (
                            re.match('\[(\' \', )?Fox News', thisTagText))  or (
                            re.match('\[(\' \', )?MSNBC', thisTagText))  or (
                            re.match('\[TYPE:', thisTagText)) : 
                            skipThisElement = True
                            

                    else: #white space - get rid of it
                        skipThisElement = True	

                    if not skipThisElement:
                        page.append(str(elem))

                    elem = next_element(elem)

                if keepThisArticle and gotDate:
                    
                    pages.append('\n'.join(page))
                    docType.append(thisDocType)

            filelength = 0
            for dirpath2, dirnames2, filenames2 in os.walk(destPath):
                filelength = filelength + len([f for f in filenames2])

            for i, page in enumerate(pages):
                dateSuffix = str(dates[i])
                fileSuffix = (i+1)+filelength

                #for Python
                f=open("%(destinationDirectory)s/%(fileNumItem)06d_%(dateItem)s-DT-%(documentType)s-SRC-%(src)s.txt" % {"destinationDirectory":destPath, "fileNumItem":fileSuffix, "dateItem":dateSuffix, "documentType":docType[i], "src": docSource}, "w+", encoding='utf-8')

                f.write(strip_tags(page))
                f.close()
                



def extractContent(sourceDir, doStopWords=False, doLemm=False): 
    
    files = [f for f in os.listdir(sourceDir) if os.path.isfile(os.path.join(sourceDir, f))]

    fullText = pd.DataFrame(columns=['ID','Y','M','D','Src','DocType','Sentence','LemmSentence'])

    lemmatizer = WordNetLemmatizer()
    cachedStopWords = stopwords.words("english")

    for i, file in enumerate(files):
        pathToFile = sourceDir + "/" + file
        
        with open(pathToFile,'r',  encoding='utf-8') as f:
            text = f.read()
            
            text = re.sub('\n', ' ', text)
            text = re.sub(r'(m\w{1,2})\.', r'\1', text)

            thisId = re.split('(\d{6})', file)[1]

            dateAndDocType = re.split('\d{6}_',file)[1]
            thisDate = re.split(r'-DT',dateAndDocType)[0]                

            #Doctype and Source if source specified
            thisDocType = re.split('-SRC', re.split(r'.txt',re.split(r'-DT-',dateAndDocType)[1])[0])[0]
            thisDocSrc = re.split(r'.txt',re.split(r'-SRC-',dateAndDocType)[1])[0]

            dateObject = datetime.strptime(thisDate, "%Y-%m-%d")

            if doStopWords: 
                words = word_tokenize(text)
                filtered_words = [word for word in words if word not in cachedStopWords]
                #print(filtered_words)
                newText = ' '.join(word for word in filtered_words)
            else:
                newText = text


            #Lemmatize sentences
            if doLemm: 
                LemmedSentence = []
                words=word_tokenize(newText)
                for w in words:
                    LemmedSentence.append((lemmatizer.lemmatize(w)))
                    #print(w)
                lemmText = ' '.join(word for word in LemmedSentence)
            else: 
                lemmText=''

            fullText.loc[i]= [thisId,dateObject.year,dateObject.month,dateObject.day,thisDocSrc,thisDocType, newText, lemmText]
            f.close()
    fullText.drop_duplicates(subset=['Sentence','Y','M','D'], keep='first', inplace=True)

    return fullText