import math 
import sys
import requests
import re # for extracting phone numbers from text
from datetime import datetime
import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import zipfile
from io import BytesIO, StringIO
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
maps_api_key = 'AIzaSyAgjoKgBaQghIlVps-ORsHYYl0GnIDyc0g'
import base64

import pandas as pd

try: from settings_local import mail
except: pass

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# import logging
#app.logger.setLevel(logging.DEBUG)  # Set log level to DEBUG for debugging
# logging.basicConfig(filename='/home/ubuntu/manatools.com/manatools/flask.log', level=logging.DEBUG)

@app.route('/helpscout', methods=['GET','POST'])
def helpscout():
    try: 
        pass
    except:
        pass
    # Use this URL as the starting point from your browser (authenticate per call?)
    # https://secure.helpscout.net/authentication/authorizeClientApplication?client_id=HyWuP6QL6SwHubt85iXmOCJO92zh0vTI&state=NmXm0gmKSmkszwolhdLExc7H6AVbETI1

    # from https://secure.helpscout.net/users/apps/777749/48fa3b1e-341b-47a5-a9a6-4bef748c482e
    # from https://developer.helpscout.com/mailbox-api/overview/authentication/
    # pass authurize bearer code https://stackoverflow.com/questions/70586468/how-to-pass-an-oauth-access-token-in-an-api-call
    code = request.args.get("code") 
   
    app_id = 'HyWuP6QL6SwHubt85iXmOCJO92zh0vTI' 
    app_secret = 'NmXm0gmKSmkszwolhdLExc7H6AVbETI1'
    data = {
        'code' : code,
        'client_id' : app_id,
        'client_secret' : app_secret,
        'grant_type' : 'authorization_code'
    }

    token_response = requests.post('https://api.helpscout.net/v2/oauth2/token',data=data)
    response_dict = json.loads(token_response.text)
    access_token = response_dict['access_token']

    response_str = "";
    for i in response_dict:
        response_str += "key: " + str(i) +  "val: " + str(response_dict[i]) + "<br/>"

    headers = {
        "Content-type": "application/json",
        "Authorization": "Bearer "+access_token
    }

    #example 2
#     customers_response = requests.get('https://api.helpscout.net/v2/customers?query=(firstName:"Jenny")',headers=headers)


    query_response = requests.get('https://api.helpscout.net/v2/customers?query=(barcus*)',headers=headers)

    emails = str(extract_emails(json.loads(query_response.text))) # this works

    # now that we've got a big API response payload (query response) we need to iterate thru each record to extract name, email, social media.
    csv = "Name, First Name, Last Name, Email, Combined Social Profiles, Keywords (Notes), Phone Numbers(Notes2), Phone\n"

    # Author's note: I constantly deal with multiple (usually empty) social profiles so i combine them into
    # a single value int he CSV.
    for customer_record in find_key_nonrecursive(json.loads(query_response.text),'customers'): 
        email = customer_record['_embedded']['emails'][0]['value']
        if customer_record['firstName'] == "":
            customer_record['firstName'] = email.split('@')[0].split('.')[0].capitalize()
            customer_record['lastName'] = email.split('@')[0].split('.')[1].capitalize()
        csv += customer_record['firstName'] + " "+ customer_record['lastName']
        csv += ","+customer_record['firstName']
        csv += ","+customer_record['lastName']
        csv += ","+email
    
        #check if social exists
        socials = customer_record['_embedded']['social_profiles']
        csv += ","
        if len(socials)>0:
            csv += '"'
            for social in socials:
                csv += social['type'] + ":" + social['value'] + ","
            csv += '"'

        #check which product bought, based on conversation
        conversation_response = requests.get('https://api.helpscout.net/v2/conversations?query=(email:'+email+')&status=all',headers=headers)
        all_convos_text = ""
        for convo in json.loads(conversation_response.text)['_embedded']['conversations']:
            convo_link = convo['_links']['threads']['href']
            convo_response = requests.get(convo_link,headers=headers)
            for thread in json.loads(convo_response.text)['_embedded']['threads']:
                if 'body' in thread: # some "threads" are "automated actions" without bodies.
                    all_convos_text += thread['body']
        
        # extract key words from convo
        keywords = ['has','pro','intuition','animation','site']
        keywords_found = ""
        for key in keywords:
            count = all_convos_text.count(key)
            if count > 0: 
                keywords_found += key + ": "+str(count) + ", "
        csv += ",\""+keywords_found+"\""

        re_us_phone = r'(\d{3}[-\.\s]??\d{3}[-\.\s]??\d{4}|\(\d{3}\)\s*\d{3}[-\.\s]??\d{4}|\d{3}[-\.\s]??\d{4})' # find us phone numbers
 
        phone_numbers_found = re.findall(re_us_phone,all_convos_text)
        phone_numbers_found = filter_and_format_numbers(phone_numbers_found) # remove non-phone numbers, and format them all correctly
        phone_numbers_found = list(set(phone_numbers_found)) # squash duplicates
            
        csv += ",\"" + ','.join(phone_numbers_found) + "\""
        if len(phone_numbers_found) > 0: csv += "," + phone_numbers_found[0] 
        else: csv += ","
        csv += "\n"


    return render_template('helpscout.html',
        token_response="status:"+str(token_response.status_code)+", response:"+token_response.text,
        response=response_str,
        token=access_token,
#        conversation_response="status:"+str(conversation_response.status_code)+", response:"+conversation_response.text[-200:],
#        customers_response="status:"+str(customers_response.status_code)+", response:"+ customers_response.text[-200:],
        query_response="status:"+str(query_response.status_code)+", response;"+query_response.text[-200:],
        all_convos_text=all_convos_text[-200:],
        emails=emails,
        # csv="csv:"+csv,
        table=csv_string_to_html_table(csv))
    #except:
     #   return render_template('helpscout.html',token_response="Failed - make sure to auth using https://secure.helpscout.net/authentication/authorizeClientApplication?client_id=HyWuP6QL6SwHubt85iXmOCJO92zh0vTI&state=NmXm0gmKSmkszwolhdLExc7H6AVbETI1")

def find_key_nonrecursive(adict, key):
    stack = [adict]
    while stack:
        d = stack.pop()
        if key in d:
            return d[key]
        for v in d.values():
            if isinstance(v, dict):
                stack.append(v)
            if isinstance(v, list):
                stack += v

def filter_and_format_numbers(numbers):
    filtered_numbers = []
    for num in numbers:
        # Remove any non-digit characters
        cleaned_num = ''.join(filter(str.isdigit, num))
        
        # Apply filtering criteria
        if cleaned_num.startswith('0'):
            continue
        if cleaned_num.startswith('1') and len(cleaned_num) != 11:
            continue
        
        # Add formatted number to the list
        if len(cleaned_num) == 10:
            # Format as (234) 567-8910
            formatted_num = f"({cleaned_num[0:3]}) {cleaned_num[3:6]}-{cleaned_num[6:]}"
            filtered_numbers.append(formatted_num)
        elif len(cleaned_num) == 11:
            # Format as (234) 567-8910, assuming the first number is '1' and should be dropped
            formatted_num = f"({cleaned_num[1:4]}) {cleaned_num[4:7]}-{cleaned_num[7:]}"
            filtered_numbers.append(formatted_num)
        
    return filtered_numbers

def csv_string_to_html_table(csv_data):
    """
    Converts a CSV string to an HTML table.

    Parameters:
        csv_data (str): The CSV data as a string.

    Returns:
        str: HTML string containing a table representation of the CSV data.
    """
    # Use StringIO to simulate a file object for the CSV string
    csv_file_like_object = StringIO(csv_data)
    
    # Read the CSV data into a DataFrame
    df = pd.read_csv(csv_file_like_object)
    
    # Convert the DataFrame to HTML table code
    html_table = df.to_html(index=False)  # `index=False` to not include row indices in the table
    
    return html_table

def extract_emails(data):
    """
    Extracts email addresses from a nested JSON structure.

    :param data: dict, the JSON data with a nested structure
    :return: list, extracted email addresses
    """
    email_list = []
    customers = data.get("customers", [])
    
    for customer in customers:
        emails = customer.get("_embedded", {}).get("emails", [])
        for email in emails:
            email_value = email.get("value")
            if email_value:
                email_list.append(email_value)
                
    return email_list


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
        resolution = '600x400'
        fov = '180'
        for i in range(len(loc['headings'])):
            heading = loc['headings'][i]
            image_url = 'https://maps.googleapis.com/maps/api/streetview?size='+resolution+'&location='+gps+'&fov='+fov+'&heading='+str(round(heading))+'&pitch=0&key='+maps_api_key 
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

            ct = 4
            for i in range(ct):
                heading = math.degrees(math.atan2(float(vec2_normalized['y']),float(vec2_normalized['x']))) + (i * (360/ct))
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

