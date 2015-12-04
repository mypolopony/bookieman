#!/usr/bin/env python
#
# title          : bookieman.py
# description    : Lets trend some books!
# author         : Selwyn-Lloyd McPherson
# date           : Fri Dec  4 02:00:54 PST 2015
# version        : 1.20
# python_version : 3.5.0 (it's the hot new thing)
# ==========================================================

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
    def __init__(self,isbn,author,title,description,url):
        self.isbn = isbn
        self.title = title
        self.url = url
        self.author = author
        self.description = description


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
    uri = 'http://api.nytimes.com/svc/books/v3/lists/names.json?api-key={key}'.format(key=credentials.NYT_API_KEY)
    response = json.loads(requests.get(uri).text)
    names = [r['list_name_encoded'] for r in response['results']]
    for idx,n in enumerate(names):
        logging.info('Available lists:')
        logging.info('{i}\t{name}'.format(i=idx,name=names[idx]))


    # Choose a list!
    list_name = 'combined-print-fiction'
    logging.info('Working with:\t{list}'.format(list=list_name))

    # Pick a date range
    start_date = [2011,1,1]                 # example for the year 2011
    end_date = [2011,12,31]
    weeks = get_weeks(start_date, end_date) # get evenly spaced weeks

    # Set up the library of books, indexable by ISBN
    bookshelf = dict()
    timeline = dict()

    for week in weeks:
        week = week.strftime('%Y-%m-%d')      # string formatting
        timeline[week] = list()
        
        uri = 'http://api.nytimes.com/svc/books/v3/lists/{name}.json?date-{date}&api-key={key}'.format(date=week,name=list_name,key=credentials.NYT_API_KEY)
        response = json.loads(requests.get(uri).text)
        
        if len(response['results']):
            # Odd initialization, but I like it!
            num_books = len(response['results']['books'])
            timeline[week] = [None] * num_books
            
            for book in enumerate(response['results']['books']):
                book = book[1]      # Response is a weird tuple with rank as the first element
                
                # Check ISBN first for efficiency
                isbn = book['primary_isbn13']
                logging.info('ISBN: {i}'.format(i=isbn))
                
                if isbn in bookshelf.keys():
                    b = bookshelf[isbn]
                    print('Found')
                    
                else:
                    print('New')
                    # This is the kind of serialization that is really gross, but easy to pull off
                    rank = book['rank']
                    logging.info('Ranking: {r}'.format(r=rank))
    
                    title = book['title']
                    logging.info('Title: {t}'.format(t=title))
                    
                    author = book['author']
                    logging.info('Author: {a}'.format(a=author))
                    
                    description = book['description'][:-1]  # weird marks at the end
    
                    amazon_url = book['amazon_product_url']
                    logging.info('Amazon URL: {a}'.format(a=amazon_url))
                    
                    b = Book(isbn,author,title,description,uri)
                    bookshelf[isbn] = b
                    
                
                # The -1 is necessary, because 1 != 0
                timeline[week][rank-1] = b
                
                logging.info('-------')
                print('-----------')
                
                # Depending on the time period, this should be fine in menory,
                # but of course we can write to a file if necessary. . .
                
                # Courtesy
                time.sleep(.2)
                    
    # Now we have a dictionary, keyed by week, and books on the best seller list 
    # on that week
    #
    # We were given the Amazon link
    # 
    # There are some different solutions here. The first is to use the
    # requests module and manipulate the H/XTML response for each URI. That's a 
    # bit messy, but certainly reliable in the short term.
    #
    # One might think, use the Amazon API! But most people have learned the 
    # hard way that it is clunky and a bit too much.
    #
    # I prefer Google. Enable the Books API at [console.developers.google.com]
    
    
    
    
    
    
    

  
if __name__ == '__main__':
    run()


