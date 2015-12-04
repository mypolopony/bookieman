#!/usr/bin/env python
#
# Title          : bookieman.py
# description    : Lets investigate some books!
# author         : Selwyn-Lloyd McPherson
# date           : 20151111
# version        : 1.20
# python_version : 3.5.0
# ================================================================

# "Under popular culture's obsession with a naive inclusion, 
# everything is O.K."
#
# -Stanley Crouch

from datetime import date, timedelta   # standard date module
import time             # standard time interface
import requests         # standard web interface
import json             # standard json interface
import logging          # basic logging
import credentials      # loads your API_KEY. This is for security,
                        # so you should create a file, credentials.py,
                        # with the line API_KEY = '###...'
                        #
                        #
                        # or, for simplicity, you can just do:
# API_KEY = '###...'    # (uncomment this line)

# Setup and wayward home for global variables
logging.basicConfig(filename='bookieman.log',level=logging.INFO)

# Hello, I'm a book! 
class Book():
    def __init__(self,isbn,title,url):
        self.isbn = isbn
        self.title = title
        self.url = url

        self.words = set()

# Hello, I'm a NYT list!
class List():
    def __init__(self,name):
        self.dates = dict()

    def add_instance(self,date,book,ranking):
        if date not in self.instances.keys():
            self.instances[date] = book
        else:
            self.instances[date].append(book)

    def get_list(self,date):
        return self['date']


# Let's grab some books. At least, all the books that're 
# fit to print.
#
# The New York Times API is freely available and the rate 
# limits on the number of calls is reasonable if you're not 
# up to something crazy.
# 
# developer.nytimes.com offers the free api key, so sign up!

# Generate all days spaced seven apart from start to end 
def get_weeks(start_date, end_date):
    start_date = date(start_date[0],start_date[1],start_date[2])    # this is poor python
    end_date = date(end_date[0],end_date[1],end_date[2])            # style :(
    
    weeks = list()
    for n in range(int ((end_date - start_date).days)):
        weeks.append(start_date + timedelta(n))

    return weeks[0::7]              # return every seventh day

def run():
    # Grab the list of list names
    uri = 'http://api.nytimes.com/svc/books/v3/lists/names.json?api-key={key}'.format(key=credentials.API_KEY)
    response = json.loads(requests.get(uri).text)
    names = [r['list_name_encoded'] for r in response['results']]
    for idx,n in enumerate(names):
        logging.info('Available lists:')
        logging.info('{i}\t{name}'.format(i=idx,name=names[idx]))


    # Choose a list, or several
    # Yeah, there are a lot of lists
    # Hmmm. NOT SURW!!! ['list_name']['date'] = [books]
    # lists = {'listname':[]}
    
    # Select a list or two here
    list_names = ['combined-print-fiction','paperback-business-books']
    lists = dict()
    for ln in list_names:
        logging.info('Working with:\t{list}'.format(list=ln))
        lists[ln] = list()

    # Pick a date range
    start_date = [2011,1,1]     # example for the year 2011
    end_date = [2011,12,31]
    weeks = get_weeks(start_date, end_date) # get evenly spaced weeks

    # Set up lists
    lists = list()      # isn't it ironic?}

    for n in list_names:
        for w in weeks:
            w = w.strftime('%Y-%m-%d')      # string formatting
            uri = 'http://api.nytimes.com/svc/books/v3/lists/{name}.json?date-{date}&api-key={key}'.format(date=w,name=n,key=credentials.API_KEY)
            response = json.loads(requests.get(uri).text)
            if len(response['results']):
                for book in enumerate(response['results']['books']):
                    book = book[1]      # Response is a weird tuple with rank as the first element
                    
                    rank = book['rank']
                    logging.info('Ranking: {r}'.format(r=rank))

                    title = book['title']
                    logging.info('Title: {t}'.format(t=title))

                    isbn = book['primary_isbn13']
                    logging.info('ISBN: {i}'.format(i=isbn))

                    amazon_url = book['amazon_product_url']
                    logging.info('Amazon URL: {a}'.format(a=amazon_url))

                    b = Book(isbn,title,uri)
                    logging.info('-------')
                    time.sleep(.2)
                    print('{}: {}'.format(w,title))


if __name__ == '__main__':
    run()


