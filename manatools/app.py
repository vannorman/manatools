import math 
import sys
import requests
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
import base64



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
        loc = address_to_gps(address)
        gps = loc['gps']
        images = []
        resolution = '300x200'
        for i in range(len(loc['headings'])):
            heading = loc['headings'][i]
            image_url = 'https://maps.googleapis.com/maps/api/streetview?size='+resolution+'&location='+gps+'&fov=80&heading='+str(round(heading))+'&pitch=0&key='+maps_api_key 
            response = requests.get(image_url, stream = True)
            if response.status_code == 200:
                image_binary = response.content
                image_base64 = base64.b64encode(image_binary).decode('utf-8')
                images.append(image_base64)
            else:
                print('no: '+response.status_code)
        response = {'images':images}
        responses.append(response)
    return jsonify({'success':True,'responses':responses})

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
            boundsNE =  data['results'][0]['geometry']['bounds']['northeast']
            boundsSW =  data['results'][0]['geometry']['bounds']['southwest']
            boundsMid = {'lat':(boundsNE['lat'] + boundsSW['lat']) / 2, 'lng' : (boundsNE['lng'] + boundsSW['lng'] ) / 2 }
            vec2 = {
                'x':boundsMid['lng'] - location['lng'],
                'y':boundsMid['lat'] - location['lat']
            }
            vec2_normalized = normalize_vec2(vec2)
            headings = []

            for i in range(6):
                heading = math.degrees(math.atan2(float(vec2_normalized['y']),float(vec2_normalized['x']))) + (i * 60)
                headings.append(heading)

            latitude = location['lat']
            longitude = location['lng']
            print(f'Latitude: {latitude}, Longitude: {longitude}, Headaings:{headings}')
            return {'gps':str(latitude)+','+str(longitude),'headings':headings}
        else:
            print(f'Geocoding failed. Status: {data["status"]}')
            return 'fail:'+data["status"]
    else:
        print(f'Failed to make the API request. Status code: {response.status_code}')
        return 'fail: '+response.status_code

def normalize_vec2(vec):
    # Calculate the magnitude of the vector
    magnitude = math.sqrt(vec['x']**2 + vec['y']**2)

    # Check for division by zero to avoid errors
    if magnitude != 0:
        normalized_vec = {'x':vec['x'] / magnitude, 'y':vec['y'] / magnitude}
    else:
        normalized_vec = {'x':0, 'y':0}  # Handle the case of a zero-length vector

    return normalized_vec

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

