# File: main.py
import firebase_admin
from firebase_admin import db
import flask 
import os
from google.cloud import Client

firebase_admin.initialize_app(options={
    'databaseURL': 'https://realchat-sillylife.firebaseio.com/',
})

SUPERHEROES = db.reference('messages')

def mainMethod(request):
    if request.path == '/' or request.path == '':
        if request.method == 'POST':
            return create_hero(request)
        else:
            return 'Method not supported', 405
    if request.path.startswith('/'):
        id = request.path.lstrip('/')
        if request.method == 'GET':
            return read_hero(id)
        elif request.method == 'DELETE':
            return delete_hero(id)
        elif request.method == 'PUT':
            return update_hero(id, request)
        else:
            return 'Method not supported', 405
    return 'URL not found', 404

def create_hero(request):
    req = request.json
    hero = SUPERHEROES.push(req)
    return flask.jsonify({'id': hero.key}), 201

def read_hero(id):
    hero = SUPERHEROES.child(id).get()
    if not hero:
        return 'Resource not found', 404
    return flask.jsonify(hero)

def read_all():
    hero = SUPERHEROES.get()
    if not hero:
        return 'Resource not found', 404
    return flask.jsonify(hero)

def update_hero(id, request):
    hero = SUPERHEROES.child(id).get()
    if not hero:
        return 'Resource not found', 404
    req = request.json
    SUPERHEROES.child(id).update(req)
    return flask.jsonify({'success': True})

def delete_hero(id):
    hero = SUPERHEROES.child(id).get()
    if not hero:
        return 'Resource not found', 404
    SUPERHEROES.child(id).delete()
    return flask.jsonify({'success': True})

def get_ebooks_by_author(request):
    """ HTTP Cloud Function
    Prints available ebooks by "author" (optional: "lang")
    Arg: request (flask.Request)
    """
    author = request.args.get('author', 'JRR Tolkien')
    lang = request.args.get('lang', 'en')
    author_books = print_author_books(author, lang)
    headers = {'Content-Type': 'text/plain; charset=utf-8'}
    return author_books, headers


def print_author_books(author, lang):
    """ Returns book data in plain text table """
    def sort_by_page_count(book):
        return book['volumeInfo'].get('pageCount', 0)
    books = get_google_books_data(author, lang)
    books.sort(key=sort_by_page_count, reverse=True)

    line_fmt = '{:>4} | {:>5} | {:.65}\n'
    lines = [
        '{sep}{h1}{sep}{h2}'.format(
            h1='{:^80}\n'.format('"%s" ebooks (lang=%s)' % (author, lang)),
            h2=line_fmt.format('#', 'Pages', 'Title'),
            sep='{:=<80}\n'.format('')
        )]
    for idx, book in enumerate(books, 1):
        accessInfo = book['accessInfo']
        if not accessInfo['epub']['isAvailable']:
            continue
        volumeInfo = book['volumeInfo']
        title = volumeInfo['title']
        subtitle = volumeInfo.get('subtitle')
        if subtitle is not None:
            title += ' / ' + subtitle
        count = volumeInfo.get('pageCount')
        pages = '{:,}'.format(count) if count is not None else ''
        lines.append(line_fmt.format(idx, pages, title))

    return ''.join(lines)


def get_google_books_data(author, lang):
    """ Fetches data from Google Books API """
    from requests import get

    books = []
    url = 'https://www.googleapis.com/books/v1/volumes'
    book_fields = (
        'items('
        'id'
        ',accessInfo(epub/isAvailable)'
        ',volumeInfo(title,subtitle,language,pageCount)'
        ')'
    )
    req_item_idx = 0  # Response is paginated
    req_item_cnt = 40  # Default=10, Max=40

    while True:
        params = {
            'q': 'inauthor:%s' % author,
            'startIndex': req_item_idx,
            'maxResults': req_item_cnt,
            'langRestrict': lang,
            'download': 'epub',
            'printType': 'books',
            'showPreorders': 'true',
            'fields': book_fields,
        }
        response = get(url, params=params)
        response.raise_for_status()
        book_items = response.json().get('items', None)
        if book_items is None:
            break
        books += book_items
        if len(book_items) != req_item_cnt:
            break  # Last response page
        req_item_idx += req_item_cnt

    return books