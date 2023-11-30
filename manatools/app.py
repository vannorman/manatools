import sys
from datetime import datetime
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import zipfile
from io import BytesIO
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
maps_api_key = 'AIzaSyAgjoKgBaQghIlVps-ORsHYYl0GnIDyc0g'

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
    subject = "Construction Inquiry"
    text = str(data)
    server = 'manatools.com'
    mail.sendMail(to, fr, subject, text,server)
#     mail.sendMail(['charlie@vannorman.ai'],'charlie@manatools.com','test2','test3','manatools.com')
    return jsonify({'success':True})

@app.route('/analyzer/submit', methods=['POST'])
def analyze():
    data = request.get_json()
    text = str(data)
    addresses = text.split(';')
    responses = []
    for address in addresses:
        gps = address_to_gps(address)
        image_data = 'https://maps.googleapis.com/maps/api/streetview?size=600x400&location='+gps+'
&fov=80&heading=70&pitch=0&key='+maps_api_key 
        response = 
        responses.append(response)
    return jsonify({'success':True,'message':text})

def address_to_gps(address):
    # Define the API endpoint URL
    endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'

    # Make the API request
    params = {'address': address, 'key': maps_api_key}
    response = requests.get(endpoint, params=params)

    # Parse the response JSON to extract latitude and longitude
    if response.status_code == 200:
        data = response.json()
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            latitude = location['lat']
            longitude = location['lng']
            print(f'Latitude: {latitude}, Longitude: {longitude}')
            return str(latitude)+','+str(longitude)
        else:
            print(f'Geocoding failed. Status: {data["status"]}')
            return 'fail:'+data["status"]
    else:
        print(f'Failed to make the API request. Status code: {response.status_code}')
        return 'fail: '+response.status_code


@app.context_processor
def utility_processor():
    # Define the object you want to make accessible in all templates
    obj = {'slogan': 'Your Source For Real Estate Tools' }
    
    # Return the object as a dictionary
    return {'obj': obj}

@app.route('/cityscore')
def cityscore(): return render_template('cityscore.html')

@app.route('/analyzer')
def analyzer(): return render_template('analyzer.html',)

@app.route('/appraisal')
def appraisal(): return render_template('appraisal.html',)

@app.route('/dealsheet')
def dealsheet(): return render_template('dealsheet.html',)

@app.route('/')
def home():
    return render_template('index.html',)

if __name__ == '__main__':
    app.run()

