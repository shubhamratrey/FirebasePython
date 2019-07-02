from flask import Flask
from flask import request
app = Flask(__name__)

@app.route("/user")
def hello():
    return "hello"


# 'http://preprod.kukufm.com/api/v1.5/home/'

@app.route('/api/v<api_version>/<username>')
def init(api_version, username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        return 'do_the_login()'
    else:
        return 'show_the_login_form()'
