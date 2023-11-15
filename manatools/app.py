import sys
from datetime import datetime
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode

from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request

try: from settings_local import mail
except: pass

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# import logging
#app.logger.setLevel(logging.DEBUG)  # Set log level to DEBUG for debugging
# logging.basicConfig(filename='/home/ubuntu/manatools.com/manatools/flask.log', level=logging.DEBUG)


@app.route('/contact/submit', methods=['POST'])
def contact():
    data = request.get_json()
#    app[data]
    to = ['team@manatools.com','charlie@vannorman.ai']
    fr = 'team@manatools.com'
    subject = "Construction Inquiry";
    text = str(data);
    server = 'manatools.com'
    mail.sendMail(to, fr, subject, text,server)
#     mail.sendMail(['charlie@vannorman.ai'],'charlie@manatools.com','test2','test3','manatools.com')
    return jsonify({'success':True});

@app.context_processor
def utility_processor():
    # Define the object you want to make accessible in all templates
    obj = {'slogan': 'Your Source For Real Estate Tools' }
    
    # Return the object as a dictionary
    return {'obj': obj}

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

@app.route('/about')
def about():
    return render_template('about.html',)

@app.route('/realtors')
def realtors():
    return render_template('realtors.html',)

@app.route('/contact')
def internship():
    return render_template('contact.html',)

@app.route('/')
def home():
    return render_template('index.html',)

if __name__ == '__main__':
    app.run()

