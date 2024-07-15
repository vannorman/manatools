import urllib.parse # for a hacky way to get the host domain to check if we're on local, since helpscout api calls from local dont work
import math 
import sys
import requests
import re # for extracting phone numbers from text
from datetime import datetime
import json
import os # for static dir ref
from os import environ as env
from urllib.parse import quote_plus, urlencode
import zipfile
from io import BytesIO, StringIO
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, jsonify, request
maps_api_key = 'AIzaSyAgjoKgBaQghIlVps-ORsHYYl0GnIDyc0g'
import base64
import sqlite3

import pandas as pd # for spreasheet <> CSV wrangling
from flask_basicauth import BasicAuth # for password protecting /helpscout

try: from settings_local import mail
except: pass

app = Flask(__name__)
load_dotenv() 
app.secret_key = env.get("APP_SECRET_KEY")

app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')
print('hi?:'+app.config['BASIC_AUTH_USERNAME'])
@app.route('/csv', methods=['GET','POST'])
def parse_customer_emails():
    # Input is the raw Xero XLS data, with relevant headers:
    # EDIT not "raw" xls data, as there was extra data in the top before headers. Had to remove that.
    # ContactName, EmailAddress, LineAmount (per record $paid), Description(product), InvoiceDate
    
    # Output is a normalized, de-duplicated, concatenated CSV of customers w headers:
    # customer_name, customer_email, products_bought(list), total_spent(dollar), date_last_purchased

    # to achieve this, upoad .xlsx, import it with pandas, create a db and table, migrate the xlsx into the db, 
    # then use sql queries to squash and normalize the data
    # USA sales thru Mar 2024: https://docs.google.com/spreadsheets/d/1pbg3JTqOxR3QP4iVH0bpOef2W9UcD-Q6n2XcjLHDlV4/edit#gid=2047459551
    # USA sales thru Mar 2024 file: /static/sheets/icreate_sales_full.csv

    Chat_GPT_prompt = """ 
        We have an csv file with columns "ContactName", "EmailAddress", "LineAmount", "Description", and "InvoiceDate".

        Using python and pandas, 
        1. read this csv into memory
        2. create a new database using sqlite, "temp_db_sales" 
        3. create a new table in this new db "all_sales"
        4. import all the data from the csv into this database
        5. Create an empty Dict, "all_sales_list" which will be the output of the overall function
        5. conduct a series of SQL queries to fill the all_sales_list with data from the database, as follows:
        5aa. The structure of the list will be [ { 'email': email_address, 'contact_name':contact_name, total_spent: total_spent, 'last_purchased':last_purchased, 'products_purchased':products_purchased}, { ... }]
        5a. Get a list of unique values from EmailAddress. There will be one unique item in all_sales_list per unique email.
        5b. For each unique item, find all records matching that email address and sum together the LineAmount from these, and place that value in the total_spent key of this item. Make sure to ignore rows with "Shipping" as the value in the "Description" column.
        5c. For each unique item, find all records in the db matching that email address and concatenate all unique phrases in the "Description" column. Make sure to ignore rows with "Shipping" as the value in the "Description" column.
        5d. For each unique item, find all rows in the db matching that email address, and take only the most recent InvoiceDate value from these rows, and place it in the date_last_purchased key value for this item.
        5e. For each unique item, make sure the contact_name key value is stored from the ContactName column for matching items in the db.

        Please do your best to generate a python function with this behavior. Do not offer any explanations, only code. Thanks
        """
    print(" @~~~~~~@ Root: "+str(root_dir()))

    # define sheet name (ensure file is located in /static/sheets/ folder)
    sheet_name = 'icreate_sales_full'; #2.5 mb no prob
    # sheet_name = 'ascent_sales_full' # 26 mb can't do it. 
    sheet_name_output = 'ascent_sales_full_result' # this will be the resulting file, created after combining emails and other data
    csv_file_path = os.path.join(root_dir(),'static/sheets/'+sheet_name+'.csv')
    print ("CSV:"+str(csv_file_path))
    
    # Pandas will use scientific notation unless we force number formats
    pd.options.display.float_format = '{:20,.2f}'.format

    all_sales_list = process_sales_data(csv_file_path) # returns a list
    print("got list:"+str(len(all_sales_list)))
    # convert that list to a CSV

    csv = list_of_dicts_to_csv_text(all_sales_list)

    with open(os.path.join(root_dir(),'static/output/'+sheet_name_output+'.csv'), 'w', encoding='utf-8') as file:
        file.write(csv)

    return render_template('sales_data.html',
        # csv=csv,
        table=csv_string_to_html_table(csv)
        )

@app.route('/helpscout/search_keyword', methods=['GET','POST'])
def search_keyword_helpscout():
    headers = get_headers_with_access_token(request)
    data = request.get_json()
    keyword = data['keyword']

    endpoint = 'https://api.helpscout.net/v2/customers?query=('+keyword+'*)'
    
    try: query_response = requests.get(endpoint,headers=headers)
    except: 
        return render_template('helpscout.html',
           token_response="Error in token response",
           response_str="Error in response str",
           )
        
    if query_response.status_code != 200:
        msg = "something2 went wrong, not sure what."
        if query_response.status_code == 401:
            # Oops, the access token we used wasn't valid.
            msg = "Token was bad. It's Charlie's fault.",
        return render_template('helpscout.html',
           token_response="Error in token response",
           response_str="Error in response str",
           token=msg,
        )
    
    return_data = json.loads(query_response.text) 
    return render_template('helpscout.html',
        query_response="status:"+str(query_response.status_code)+", response;"+query_response.text[-200:],
        csv="data:"+return_data,
        # table=csv_string_to_html_table(csv)
        )
 

@app.route('/helpscout/email_to_name', methods=['GET','POST'])
def match_email_to_name_helpscout():
    headers = get_headers_with_access_token(request)

    file_path = os.path.join(root_dir(),'static/sheets/emails.txt')

    email_list = []
    with open(file_path, 'r') as file:
        for line in file:
            email_list.append(line.strip())

    csv = ""
    for email in email_list:
        endpoint = 'https://api.helpscout.net/v2/customers?query=('+email+'*)'
        
        try: query_response = requests.get(endpoint,headers=headers)
        except: 
            return render_template('helpscout.html',
               token_response="Error in token response",
               response_str="Error in response str",
               )
            
        if query_response.status_code != 200:
            msg = "something2 went wrong, not sure what."
            if query_response.status_code == 401:
                # Oops, the access token we used wasn't valid.
                msg = "Token was bad. It's Charlie's fault.",
            return render_template('helpscout.html',
               token_response="Error in token response",
               response_str="Error in response str",
               token=msg,
            )
        else: # 200 ok
            csv += "," + json.loads(query_response.text)
            
    return render_template('helpscout.html',
        query_response="status:"+str(query_response.status_code)+", response;"+query_response.text[-200:],
        csv="csv:"+csv,
        # table=csv_string_to_html_table(csv)
        )
    
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
        query_response="status:"+str(query_response.status_code)+", response;"+query_response.text[-200:],
        all_convos_text=all_convos_text[-200:],
        emails=emails,
        # csv="csv:"+csv,
        table=csv_string_to_html_table(csv))
    #except:
     #   return render_template('helpscout.html',token_response="Failed - make sure to auth using https://secure.helpscout.net/authentication/authorizeClientApplication?client_id=HyWuP6QL6SwHubt85iXmOCJO92zh0vTI&state=NmXm0gmKSmkszwolhdLExc7H6AVbETI1")



def list_of_dicts_to_csv_text(data_list):
    # Convert list of dictionaries to a DataFrame
    df = pd.DataFrame(data_list)
   
    # Create a StringIO object to hold the CSV data
    csv_buffer = StringIO()
    
    # Convert DataFrame to CSV text and store in the StringIO object
    df.to_csv(csv_buffer, index=False)
    
    # Retrieve the CSV content as a string from the buffer
    csv_text = csv_buffer.getvalue()
    
    # Optional: Close the StringIO object if not needed anymore
    csv_buffer.close()
    
    return csv_text




def process_sales_data(csv_file_path):
    # Step 5: Create an empty dictionary to hold the data
    all_sales_list = []
    print("start process sales data.")
    dbname = 'temp_db_sales.db'
    if os.path.exists(dbname): 
        os.remove(dbname)
        print("Successfully! The File has been removed")


    # Read CSV into memory. 3 MB no issue, 25 MB can't do it so we chunk it.
    chunksize = 10 ** 6
    with pd.read_csv(csv_file_path, usecols=["ContactName", "Country", "PORegion", "EmailAddress", "LineAmount", "Description", "InvoiceDate"], chunksize=chunksize) as reader:
        print("reader chunk 1.")
        for df in reader:
    
            # Make sure dates are correct format
            try: df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], format='%m/%d/%Y').dt.strftime('%Y-%m-%d') # US Version (MM/DD/YYYY)
            except: df['InvoiceDate'] = '1979-01-01'


            print("got df"+str(df))
            # Step 2: Create a new SQLite DB
            conn = sqlite3.connect(dbname)
            cursor = conn.cursor()
            
            # Step 3: Create a new table 'all_sales'
            cursor.execute('''
            CREATE TABLE all_sales (
                ContactName TEXT,
                EmailAddress TEXT,
                Country TEXT,
                PORegion TEXT,
                LineAmount REAL,
                Description TEXT,
                InvoiceDate DATE
            )
            ''')
            
            # Step 4: Import data from CSV to the database
            df.to_sql('all_sales', conn, if_exists='append', index=False)
            
            
            # Step 5a: Get a list of unique email addresses
            cursor.execute('SELECT DISTINCT EmailAddress FROM all_sales')
            unique_emails = cursor.fetchall()
            index = 0 
            # Step 5b-e: Process each unique email address
            for email in unique_emails:
                email = email[0]

                # skip hue emails.
                if 'huehd' in str(email): continue # print('HUE:'+email)

                # Get PORegion and Region.
                cursor.execute('''
                SELECT PORegion FROM all_sales
                WHERE EmailAddress = ? 
                ''', (email,))
                try: po_region = cursor.fetchone()[0]
                except: po_region = "Unknown"
                 # Get PORegion and Region.
                cursor.execute('''
                SELECT Country FROM all_sales
                WHERE EmailAddress = ? 
                ''', (email,))
                try: country = cursor.fetchone()[0]
                except: country = "Unknown"
         

                # 5b: Calculate total spent
                cursor.execute('''
                SELECT SUM(LineAmount) FROM all_sales
                WHERE EmailAddress = ? 
                ''', (email,))
                total_spent = cursor.fetchone()[0]
                
                # 5c: Concatenate all unique descriptions
                cursor.execute('''
                SELECT DISTINCT Description FROM all_sales
                WHERE EmailAddress = ?
                ''', (email,))
                descriptions = cursor.fetchall()
                products_purchased = ""
                excludes = ['ship','delivery', 'frieght', 'freight', 'cancel','payment','tel','@','support',]

                for desc in descriptions:
                    if not any(ex in desc[0].lower() for ex in excludes):
                        products_purchased += desc[0] +"; "
                        # print("EM:"+str(email)+", desc: "+str(desc[0]))
                    # else:
                        # print("EM, not:"+str(email)+", desc: "+str(desc[0]))
                            

                
                # 5d: Find the most recent purchase date
                cursor.execute('''
                SELECT MAX(InvoiceDate) FROM all_sales
                WHERE EmailAddress = ?
                ''', (email,))
                last_purchased = cursor.fetchone()[0]
                
                # 5e: Get the contact name (assuming it's the same for all entries per email)
                cursor.execute('''
                SELECT ContactName FROM all_sales
                WHERE EmailAddress = ? LIMIT 1
                ''', (email,))
                try: contact_name = cursor.fetchone()[0]
                except: contact_name = "NoContact"
                
                # Append the information to the all_sales_list list
                all_sales_list.append({
                    'index' :index,
                    'email' : email,
                    'contact_name' : contact_name,
                    'total_spent' : total_spent,
                    'last_purchased' : last_purchased,
                    'products_purchased' : products_purchased,
                    'po_region' : po_region,
                    'country' : country

                })

                index += 1
            
            # Close the database connection
            conn.close()
        
    return all_sales_list

basic_auth = BasicAuth(app)
@app.route('/helpscout', methods=['GET','POST'])
@basic_auth.required
def helpscout():
    host=str(urllib.parse.urlparse(request.base_url).hostname)
    localhost = False
    if host == '127.0.0.1': 
        localhost = True
        localmessage = "Localhost detected. You need to get auth headers from the server to make Helpscout api calls. Fill it in here."
    headers = get_headers_with_access_token(request)
    print("headers:"+str(headers))
    if localhost == False and (headers['Access_Token'] is None):
        return redirect("https://secure.helpscout.net/authentication/authorizeClientApplication?client_id=HyWuP6QL6SwHubt85iXmOCJO92zh0vTI&state=NmXm0gmKSmkszwolhdLExc7H6AVbETI1#")
    else: 
        return render_template('helpscout.html',headers=str(headers),localmessage=localmessage)


@app.route('/upload', methods=['POST'])
def upload():
    print ('upload')
    if 'file' not in request.files:
        print ('no file upload')
        return "No file part"

    file = request.files['file']


    if file.filename == '':
        print ('no sel')
        return "No selected file"

    if file:
        df = pd.read_csv(file)
        print('df: ~~~~ ~~~~ ')
        emails = []
        for index, row in df.iterrows():
            emails.append(row.values[0])
        return jsonify({ 'emails' : emails, 'count' : df.shape[0] })
        # return df.to_html()  # Display parsed CSV as HTML table

@app.route('/convertEmails', methods=['POST'])
def convertEmails():
    data = request.get_json()
    
    # print('rq args:'+str(data))
    names = []

    headers = {
        "Content-type": "application/json",
        "Authorization": data['authorization'],
    }

    items = []
    for email in data['emails']:
        query_response = requests.get('https://api.helpscout.net/v2/customers?query=('+email+'*)',headers=headers)
        print("Q: !!!!! ~~~~~`  "+ query_response.text)
        r = json.loads(query_response.text)
        try: 
            item = [email,
                r['_embedded']['customers'][0]['firstName'],
                r['_embedded']['customers'][0]['lastName'], ]
        except:
            item = [email,'None','None']
        items.append(item)
    auth_token = request.args.get("authorization")
    print (auth_token)
    return jsonify({'items':items})

@app.route('/helpscout2', methods=['GET','POST'])
def helpscout2():
    headers = get_headers_with_access_token(request)

    query_response = requests.get('https://api.helpscout.net/v2/customers?query=(barcus*)',headers=headers)
    if query_response.status_code != 200:
        msg = "something went wrong, not sure what."
        if query_response.status_code == 401:
            # Oops, the access token we used wasn't valid.
            msg = "Token was bad. It's Charlie's fault.",
        return render_template('helpscout2.html',
           token_response="Error in token response",
           response_str="Error in response str",
           token=msg,
        )

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


    return render_template('helpscout2.html',
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

# UTILITY FNS
def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))

def get_headers_with_access_token(request):
    # need to use "https://secure.helpscout.net/authentication/authorizeClientApplication?client_id=HyWuP6QL6SwHubt85iXmOCJO92zh0vTI&state=NmXm0gmKSmkszwolhdLExc7H6AVbETI1#"

    access_token = request.args.get("access_token")

    if access_token is None:
        
        
        print ('get headers access token, currently None')
        # If we do not, we must try to get an access token by getting the "code" from the can continue with the access token below. 
        # pass authurize bearer code https://stackoverflow.com/questions/70586468/how-to-pass-an-oauth-access-token-in-an-api-call
        code = request.args.get("code") 
        
        app_id = os.getenv('APP_ID')
        app_secret = os.getenv('APP_SECRET')

        data = {
            'code' : code,
            'client_id' : app_id,
            'client_secret' : app_secret,
            'grant_type' : 'authorization_code'
        }

        token_response = requests.post('https://api.helpscout.net/v2/oauth2/token',data=data)
        response_dict = json.loads(token_response.text)
        print ('get response from request access token? : '+token_response.text)
        if 'access_token' in response_dict:
            access_token = response_dict['access_token']
        else: 
            print('NO access token')
            response_str = ""
            for i in response_dict:
                response_str += "key: " + str(i) +  "val: " + str(response_dict[i]) + "<br/>"
                print (response_str)

    # Now, either way, we should have an access token. If we do not, it is because
    # A) No access token was passed as /helpscout?access_token=9999999
    # B) No "code" was passed as /helpscout?code=777777 (which is generated when clicking the Approve Application via the HelpScout website)


    headers = {
        "Content-type": "application/json",
        "Authorization": "Bearer "+str(access_token),
        "Access_Token" : access_token,
    }
    print('got tokens:'+str(headers))
    return headers

