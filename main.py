# Author: Evan Dobbs
# Description: A web scraper that begins on the "new" page of the quantum physics arXiv, goes through the abstracts of
#   all new papers submitted, and finds keywords in them. In the future, this will be extended to actually accessing
#   the pdf versions of the papers and navigating reference sections to build a knowledge base of relevant papers for
#   various topics.

# Notes: While this currently parses only the abs pages, I would like to parse the pdfs of actual papers as well for
#   select papers which seem interesting based on the information extracted from their abstract pages. This is why there
#   is a great deal of unused code for reading/parsing pdfs.

# known issues:
#   1. Some abstracts have latex in them (to be expected). Such text retains its uncompiled form (and so is unintelligible
#       to the program at the moment). A possible solution is to compile all text as latex code before parsing it.

# Logic:
# 1. open chatbot
# 2. either ask for summary of the day's new papers, the week's new papers, information on a specific topic, or a specific paper.
# 3. if compiling a list of papers related to a specific topic or paper, compile until some stopping criterion is reached.
#   This criterion can be either length (unrealistic to read more than 5-10 papers), relevance (if papers stop being relevant),
#   or processing time (if things are slow).
# 4. Maybe keep a list of topics of interest for specific users, and when searching papers (either regular or specific)
#   always make a note of these papers and their related topics.


from urllib import request
from bs4 import BeautifulSoup
import requests
import re
#import pdfquery
import os
import PyPDF4 as pf
from nltk.tokenize import word_tokenize
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords

from os.path import exists

#bs4 is used for navigating arxiv, PyPDF4 for navigating the actual papers in pdf form. Maybe look for alternative to
#   PyPDF4? Try pdfquery.

def main():
    read_search('https://arxiv.org/list/quant-ph/new')
    kb = {}
    with open('urls.txt', 'r') as f:  # change to read/write from just read
        urls = f.read().splitlines()
        for doc in urls:
            # look for external urls in doc and add to urls.txt
            #print("doc url: ")
            #print(doc)  # dummy
#            read_pdf(doc)
            read_html(doc)
            with open(str(doc[27:] + '_clean.txt'), 'r', encoding="utf-8") as f:  # [27:] starts the url after all periods.
                text = f.read()
                kws = get_keywords(text)
                kb = build_kb(text, kws, kb)
                for kw in kb:
                    print("KEYWORD " + kw + ": ")
                    for sent in kb[kw]:
                        print(sent)

        print("done\n\n\n")

        important_terms = ['protection', 'determinism', 'photons', 'geometric', 'algorithm', 'envelope', 'metasurfaces', 'photonic', 'wva', 'memory']

        for key in important_terms:
            print("KEYWORD: " + key)
            for sent in kb[key]:
                print(sent)


#not used for the web-scraping project
def read_pdf(url):
    pdfurl = url[27:] + '.pdf'
    print(pdfurl)
    path = os.getcwd() + pdfurl

    if not exists(path):
        with open(pdfurl, 'wb') as f:
            f.write(requests.get(url).content)

    with open(pdfurl, 'rb') as f:

        readpdf = pf.PdfFileReader(f)
        for page in range(readpdf.numPages):
            curr_page = readpdf.getPage(page)
            text = curr_page.extractText()
            #find external links and useful info
            links = get_links(text)
            print("links: ")
            for link in links:
                print(link)
#            keywords = get_keywords(text)
#            print('keywords: ')
#            for kw in keywords:
#                print(kw)

# Store raw text from pages in one file and cleaned text in another.
def read_html(url):
    data = requests.get(url).text
    soup = BeautifulSoup(data)
    thisurl = url[27:]+'_raw.txt'
    cleanurl = url[27:]+'_clean.txt'

    with open(thisurl, 'w', encoding="utf-8") as f:
        counter = 0
        data = soup.findAll(text=True)
        result = filter(visible, data)
        temp_list = list(result)  # list from filter
        abs = False
        temp_str = ' '.join(temp_list)
        f.write(temp_str) #write raw text

        #I know exactly what each page will look like so I know what I want. No point doing this in another function
        #and parsing the raw text a second time.
        with open(cleanurl, 'w', encoding="utf-8") as f:
            for item in temp_list:
                if str(item).startswith('Abstract:'):
                    abs = True
                if str(item).startswith('\n'):
                    abs = False
                if abs:
                    #print(item)
                    f.write(item)

# Finds keywords by term-frequency. Because of the small size of abstracts, many of the top 25 terms have a frequency
#   of 1, leading to inconsistent output. Swap to tf-idf for chatbot project.
def get_keywords(text):
    words = word_tokenize(text)
    words = [w.lower() for w in words]
    words = [w for w in words if w.isalpha() and w not in stopwords.words('english')]
    num_words = len(words)
    words_set = set(words)
    num_unique_words = len(words_set)
    word_counts = [(w, words.count(w)) for w in words_set]
    word_counts.sort(reverse=True, key=lambda x: x[1])  # sort in descending order
    counter = 0
    kws = []
    for word, count in word_counts:
        print(word, count)
        kws.append(word)
        counter+=1
        if counter >= 25:
            break
    return kws

# Given a list of keywords and raw text, build a dictionary of keywords and related sentences. Requires an existing
#   kb to be passed in by reference so as to account for duplicated keywords between pages.
def build_kb(text, kws, kb):

    sents = sent_tokenize(text)
    for kw in kws:
        #print("KW: ")
        #print(kw)
        temp_list = []
        for s in sents:
            s = s.lower()
            if not s.find(kw) == -1:
                #print("sentence!!!")
                #print(s + "\n")
                #print(kw + "\n")
                temp_list.append(s)
            #else:
                #print("not found!")
        if kw in kb:
            kb[kw] = kb[kw] + temp_list
        else:
            kb[kw] = temp_list
    return kb

# Find URLs in a page. This is mostly used for finding links in pdfs, and is not used in the web-scraping project.
def get_links(text):
    rx = r"(https?://\S+)"
    url = re.findall(rx, text)
    return url

#    pdf = pdfquery.PDFQuery('tbr.pdf')
#    pdf.load()
#    xmlurl = url + '_xml.txt'
#    pdf.tree.write(xmlurl, pretty_print=True)

#    os.remove('tbr.pdf')

# Find URLs in an html page. This is step 1 of the web-scraping project.
def read_search(url):
#    with request.urlopen(url) as f:
#        raw = f.read().decode('utf8')
#    soup = BeautifulSoup(raw)

    data = requests.get(url).text
    soup = BeautifulSoup(data)

    with open('urls.txt', 'w') as f:
        counter = 0
        wanted = False
        for link in soup.find_all('a'):
            link_str = str(link.get('href'))
            #print(link_str)
            #if link_str.startswith("/pdf"):  # for now this section is hardcoded.
            if link_str.startswith("/abs"):
                #print("found something!")
                link_str = "https://arxiv.org" + link_str
                wanted = True

            if wanted:
                f.write(link_str + '\n')
            wanted = False

            counter+=1
            if counter > 100:
                break

    #for script in soup(['script', 'style']):
        #script.extract()
    #print(soup.get_text())


# Taken from the sample code on the Github:
# https://github.com/kjmazidi/NLP/blob/master/Xtra_Python_Material/Web_Scraping/3%20-%20Web%20crawler%20-%20almost.ipynb
def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element.encode('utf-8'))):
        return False
    return True

if __name__ == '__main__':
    main()


