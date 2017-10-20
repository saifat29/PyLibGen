import argparse
import urllib.request as req
from bs4 import BeautifulSoup
import re
import os
from tabulate import tabulate
from settings import *

# Settings as global variables
global DOWNLOAD_PATH
global MAX_CHARS_AUTHORS
global MAX_CHARS_PUBLISHER
global MAX_CHARS_TITLE
global N_AUTHORS

def replaceSymbols(term):
    replace_dic = {' ': '%20', '$': '%24', '&': '%26', '`': '%60',
                   ':': '%3A', '<': '%3C', '>': '%3E', '[': '%5B',
                   ']': '%5D', '{': '%7B', '}': '%7D', '"': '%22', 
                   '+': '%2B', '#': '%23', '%': '%25', '@': '%40',
                   '/': '%2F', ';': '%3B', '=': '%3D', '?': '%3F',
                   '\\': '%5C', '^': '%5E', '|': '%7C', '~': '%7E', 
                   "'": '%27', ',': '%2C'}

    for symbol, escape in replace_dic.items():
        term = term.replace(symbol, escape)

    return(term)

def getSearchResults(term, page, column='def'):
    if not term.isalpha():
        term = replaceSymbols(term)

    url = 'http://libgen.io/search.php?&req={}&column={}&page={}'.format(
        term, column, str(page))

    source = req.urlopen(url)
    soup = BeautifulSoup(source, 'lxml')
    if page == 1:
        books_found = re.search(r'(\d+) books found', str(soup))
        print(books_found.group().upper())
        if int(books_found.groups()[0]) == 0:
            return(False)
        
    page_books = soup.find_all('tr')
    page_books = page_books[3:-1]  # Ignore 3 first and the last <tr> label.
    books = page_books
    return(books)


def formatBooks(books, page):
    # TODO: Add support for multiple choices
    fmt_books = []
    books_mirrors = [] # List of dics with complete titles and mirrors

    for i, rawbook in enumerate(books):
        i += (page - 1) * 25

        book_attrs = rawbook.find_all('td')

        authors = book_attrs[1].find_all('a')
        authors = [a.text for a in authors]
        author = ', '.join(authors[:N_AUTHORS])
        author = author[:MAX_CHARS_AUTHORS]

        title = book_attrs[2].find(title=True).text
        tinytitle = title[:MAX_CHARS_TITLE]

        publisher = book_attrs[3].text[:MAX_CHARS_PUBLISHER]
        year = book_attrs[4].text
        lang = book_attrs[6].text[:2]  # Show only 2 first characters
        size = book_attrs[7].text
        ext = book_attrs[8].text
        io_mirror = book_attrs[9].a.attrs['href']

        book = [str(i + 1), author, tinytitle, publisher,
                year, lang, ext, size]  # Start at 1

        book_mirrors = {'title': title, 'io': io_mirror}
        books_mirrors.append(book_mirrors)

        fmt_books.append(book)

    return(fmt_books, books_mirrors)


def selectBook(books, mirrors, page, end=False):
    headers = ['#', 'Author', 'Title', 'Publisher',
               'Year', 'Lang', 'Ext', 'Size']

    if not end:
        print(tabulate(books[(page - 1) * 25:page * 25], headers))
    else:
        print('Sorry, no more matches.')

    while True:
        elec = input(
            '\n Type # of book to download, q to quit or just press Enter to see more matches: ')

        if elec.isnumeric():
            choice = int(elec) - 1
            if choice < len(books):  # Selection
                title = '{}.{}'.format(mirrors[choice]['title'], books[choice][-2])
                downloadBook(mirrors[choice]['io'], title)
                return(False)
            else:
                print("Too big of a number.")
                continue

        elif elec == 'q' or elec == 'Q':  # Quit
            return(False)

        elif not elec:  # See more matches
            return(True)


def downloadBook(link, filename):
    source = req.urlopen(link)
    soup = BeautifulSoup(source, 'lxml')

    for a in soup.find_all('a'):
        if a.text == 'GET':
            download_url = a.attrs['href']
            break

    if os.path.exists(DOWNLOAD_PATH) and os.path.isdir(DOWNLOAD_PATH):
        print('Downloading...')
        path = '{}/{}'.format(DOWNLOAD_PATH, filename)
        req.urlretrieve(download_url, filename=path)
        print('Book downloaded to {}'.format(path))
    elif os.path.isfile(DOWNLOAD_PATH):
        print('The download path is not a directory. Change it in settings.py')
    else:
        print('The download path does not exist. Change it in settings.py')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--search', required=True, dest='search_term')
    args = parser.parse_args()

    books = []
    mirrors = []
    page = 1
    get_next_page = True

    while get_next_page:
        raw_books = getSearchResults(args.search_term, page)
        if raw_books:
            new_books, new_mirrors = formatBooks(raw_books, page)
            books += new_books
            mirrors += new_mirrors
            get_next_page = selectBook(books, mirrors, page)
            page += 1
        elif raw_books == []: # 0 matches in the last page 
            get_next_page = selectBook(books, mirrors, page - 1, end=True)
        else: # 0 matches total
            get_next_page = False