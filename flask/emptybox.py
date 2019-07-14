import os
from flask import Flask, redirect

app = Flask(__name__)
MAIN_SITE = os.getenv('EMPTYBOX_SITE', 'http://localhost:3000/')


@app.route('/')
def handle_default():
    return redirect(MAIN_SITE)

@app.route('/stats')
def stats():
    data = {'fileCount': 0}
    return data
