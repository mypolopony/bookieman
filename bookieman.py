#!/usr/bin/env python
#
# title          : bookieman.py
# description    : Lets trend some books!
# author         : Selwyn-Lloyd McPherson
# date           : Fri Dec  11 02:00:54 PST 2015
# version        : 1.3
# python_version : 3.5.0 (it's the hot new thing)
# ==========================================================

# "Under popular culture's obsession with a naive inclusion, 
# everything is O.K."
#
# -Stanley Crouch


from datetime import date, timedelta   # standard date module
import pickle           # for binarizing results
import ftfy             # great ascii / unicode fixer
import redis            # redis is used to store our library of books
import time             # standard time interface
import requests         # standard web interface
import logging          # basic logging
import credentials      # loads your API_KEY. This is for security,
                        # so you should create a file, credentials.py,
                        # with the line API_KEY = '###...'
                        

# Setup
logging.basicConfig(filename='bookieman.log',level=logging.INFO)
bookshelf = redis.StrictRedis(host='localhost', port=6379, db=0)

# Hello, I'm a book! 
class Book():
    def __init__(self,isbn,author,title,snippet,description,url):
        self.isbn = isbn
        self.title = title
        self.url = url
        self.author = author
        self.description = description
        self.snippet = snippet
    
    def serialize(self):
        return {'isbn': self.isbn, 'title': self.title, 'url': self.url, 'author': self.author, 'description': self.description, 'snippet': self.snippet}
    

# Generate all days spaced seven apart from start to end 
def get_weeks(start_date, end_date):
    start_date = date(start_date[0],start_date[1],start_date[2]) 
    end_date = date(end_date[0],end_date[1],end_date[2])
    
    weeks = list()
    for n in range(int ((end_date - start_date).days)):
        weeks.append(start_date + timedelta(n))

    return weeks[0::7]              # return every seventh day

def get_list_names():
    '''
    Retrieves the various NYT Best Seller Lists
    '''
    uri = 'http://api.nytimes.com/svc/books/v3/lists/names.json?api-key={key}'.format(key=credentials.NYT_API_KEY)
    response = requests.get(uri).json()
    names = [r['list_name_encoded'] for r in response['results']]
    for idx,n in enumerate(names):
        logging.info('Available lists:')
        logging.info('{i}\t{name}'.format(i=idx,name=n))
    return names

def cleanse():
    '''
    Simple word cleaner
    '''
    

    
def get_timeline(list_name,weeks):
    # This timeline will hold the lists for a given week
    timeline = dict()

    for week in weeks:
        week = week.strftime('%Y-%m-%d')      # string formatting
        timeline[week] = list()
        logging.info('Working on week: {w}'.format(w=week))
        
        uri = 'http://api.nytimes.com/svc/books/v3/lists/{w}/{name}.json?api-key={k}'.format(name=list_name, w=week,k=credentials.NYT_API_KEY)
        response = requests.get(uri).json()
        
        if len(response['results']):
            # Odd initialization, but I like it!
            num_books = len(response['results']['books'])
            timeline[week] = [None] * num_books
            
            for book in enumerate(response['results']['books']):
                book = book[1]      # Response is a weird tuple with rank as the first element
                
                # One theme concerning ISBNs, or similarly UPCs, is that they
                # are actually not entirely static, nor universal. ISBN-10 was
                # phased out in 2007 in favor of ISBN=13. Unfortunately, both are
                # used for various purposes. I'll use the new, preferred id
                isbn10 = book['primary_isbn10']
                isbn13 = book['primary_isbn13']                
                rank = book['rank']
                                
                if not bookshelf.get(isbn13):
                    title = ftfy.fix_text(book['title'])                  
                    author = ftfy.fix_text(book['author'])                 
                    snippet = ftfy.fix_text(book['description'][:-1])  # weird marks at the end
                    amazon_url = book['amazon_product_url']
                    
                    # The descriptions from the New York Times are abbreviated.
                    # 
                    # The Amazon product link can be used to grab a fuller 
                    # description but that's messy. Amazon does have an API, 
                    # but most people have found out the hard way that it is 
                    # unnecessarily clunky.
                    # 
                    # The Google Books API works well [developers.google.com/books]
                    
                    description = None
                    uri = 'https://www.googleapis.com/books/v1/volumes?'
                    # Try ISBN-13
                    params = {'q':'isbn:{isbn}'.format(isbn=isbn13), 'key':credentials.GB_API_KEY}
                    response = requests.get(uri,params=params)
                    response = response.json()
                    try:
                        description = ftfy.fix_text(response['items'][0]['volumeInfo']['description'])
                    except:
                        pass
                    # Try ISBN-10
                    if not description:
                        params = {'q':'isbn:{isbn}'.format(isbn=isbn10), 'key':credentials.GB_API_KEY}
                        response = requests.get(uri,params=params)
                        response = response.json()
                        try:
                            description = ftfy.fix_text(response['items'][0]['volumeInfo']['description'])
                        except:
                            pass
                    # Try the title, as a last resort
                    if not description:
                        params = {'q':'title:{title}'.format(title=title), 'key':credentials.GB_API_KEY} 
                        response = requests.get(uri,params=params)
                        response = response.json()
                        try:
                            description = ftfy.fix_text(response['items'][0]['volumeInfo']['description'])
                        except:
                            logging.warning('Cannot find description for: {isbn}'.format(isbn=isbn10))
                        
                    b = Book(isbn13,author,title,snippet,description,amazon_url)
                    bookshelf.set(isbn13,b.serialize())
                    logging.debug(description)
                    logging.info('New Book Added to Bookshelf: {t}'.format(t=b.title))
                
                # Depending on the time period, this should be fine in memory
                # The -1 is necessary, because 1 != 0
                timeline[week][rank-1] = isbn13
                
                # Courtesy
                time.sleep(.2)

# Let's grab some books. At least, all the books that're 
# fit to print.
#
# The New York Times API is freely available and the rate 
# limits on the number of calls is reasonable if you're not 
# up to something crazy.
# 
# developer.nytimes.com offers the free api key, so sign up!   
def run():
    filename = 'paperback-nonfiction_[2011, 1, 1]_[2015, 11, 30]'
    
    # The New York Times actually has many lists for different genres
    nyt_lists = get_list_names()
    
    # We'll choose just one
    list_name = 'paperback-nonfiction'
    logging.info('Working with:\t{list}'.format(list=list_name))
    
    # Pick a date range
    start_date = [2011,1,1]                 # for example, 2011-2015
    end_date = [2015,11,30]
    weeks = get_weeks(start_date, end_date) # get evenly spaced weeks
    
    # Now to obtain the timeline
    timeline = get_timeline(list_name,weeks)
    pickle.dump(timeline,open('{ln}_{sd}_{ed}.dat'.format(ln=list_name,sd=start_date,ed=end_date),'wb'))

    # Let's build a lexicon of words used in book descriptions. We'll save it
    # since lexicons are always useful
    lexicon = set()
    isbns = bookshelf.keys('*')
    for isbn in isbns:
        description = eval(bookshelf.get(isbn))['description']
        for word in description.split():
            lexicon.add(cleanse(word.lower()))
    logging.debug('Sorted lexicon:\n--------') # in debug, this can help know 
    lexicon = set(sorted(lexicon))
    # There is a tendency to use NLTK just for stop words. That's really not necessary 
    with open('stopwords.txt','r') as sw:
        stopwords = set(sw.read().splitlines())
        lexicon = lexicon.difference(stopwords)
    for word in lexicon:                       # what to filter out
        logging.debug(word)
    
    
        

    
                

if __name__ == '__main__':
    run()


