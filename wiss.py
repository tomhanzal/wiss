import os
from flask import Flask
from flask import render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template('layout.html')


if __name__ == '__main__':
    app.run()
