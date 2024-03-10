import os
import requests
import logging

from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_cors import CORS

from id_fy.log import log_data
from id_fy.utils import generate_id

load_dotenv()

app = Flask(__name__)
CORS(app)


# Credentials by IDfy
API_KEY = os.environ.get("API_KEY")
ACCOUNT_ID = os.environ.get("ACCOUNT_ID")
KEY_ID = os.environ.get("KEY_ID")
SECRET_BASE64 = os.environ.get("SECRET_BASE64")
OU_ID = os.environ.get("OU_ID")
CALLBACK_URL = "https://loanuat.filending.in/application-form"


# Index
@app.route('/', methods=['GET'])
def index():

    return "hello world  this IDfy DigiLocker verify"


# IDfy the document-fetching Pan Card 
@app.route('/pancard', methods=['POST'])
def pancard_document():

    pan_number = request.json.get('pan_number')

    if not pan_number:

        return jsonify({"error": "PAN card number is required"}), 400

    task_id = generate_id()
    group_id = generate_id()

    headers = {
        'account-id': ACCOUNT_ID,
        'api-key': API_KEY,
        'Content-Type': 'application/json',

    }

    data = {
        "task_id": task_id,
        "group_id": group_id,
        "data": {
            "id_number": pan_number
        }
    }     

    try:
        # Make the first request to initiate document fetching
        response = requests.post('https://eve.idfy.com/v3/tasks/async/verify_with_source/ind_pan_plus',
                                 headers = headers, json = data)
        
        response.raise_for_status()  # Raise an HTTPError for bad responses

        response_data = response.json()

        request_id = response_data.get('request_id')

        if request_id:
            # Make the second request to check the status and get the data
            response_received = requests.get(
                'https://eve.idfy.com/v3/tasks',
                params={'request_id': request_id},
                headers=headers
            )

            if response_received.status_code == 200:
                pancard_data = response_received.json()

                if pancard_data:
                    task = pancard_data[0]

                    # Check if the task is completed
                    if task.get('status') == 'completed':
                        result = task.get('result', {})
                        source_output = result.get('source_output', {})

                        aadhaar_linked = source_output.get('aadhaar_linked')
                        full_name = source_output.get('full_name')
                        dob = source_output.get('dob')
                        gender = source_output.get('gender')
                        pan_number = source_output.get('pan_number')
                        masked_aadhaar = source_output.get('masked_aadhaar')

                        log_data(message="Pan card fetching success", event_type='/pancard', 
                                log_level=logging.INFO, additional_context={'Received-Pan-Data': task})

                        return jsonify({
                            "aadhaar_linked": aadhaar_linked,
                            "full_name": full_name,
                            "dob": dob,
                            "gender": gender,
                            "pan_number": pan_number,
                            "masked_aadhaar": masked_aadhaar
                        }), 200
                    
                    elif task.get('status') == "in_progress":
                            error_message = task.get('message', 'Unknown error')

                            log_data(message=f"Pan card fetching in_progress{error_message}", event_type='/pancard', 
                                    log_level=logging.ERROR, additional_context={'Received-Pan-Data': task})
                            
                            return jsonify({"error": f"Failed to fetch document - {error_message}", "Received-Data from IDfy": pancard_data}), 500
            
                    
                    # Check if the task failed
                    elif task.get('status') == 'failed':
                            error_message = task.get('message', 'Unknown error')

                            log_data(message=f"Pan card fetching failed {error_message}", event_type='/pancard', 
                                    log_level=logging.ERROR, additional_context={'Received-Pan-Data': task})
                            
                            return jsonify({"error": f"Failed to fetch document - {error_message}", "Received-Data from IDfy": pancard_data}), 500
                    
                return jsonify({"error": "No data received from the server", "data": pancard_data}), 500
            
            return jsonify({"error": f"Failed to fetch document - Server response code: {response_received.status_code}", "data": pancard_data}), 500

        return jsonify({"error": "Request ID not received for your PAN card", "data": response_data}), 500

    except requests.exceptions.RequestException as e:
        
        return jsonify({"error": f"Failed to fetch document - {str(e)}"}), 500


# AADHAR
# IDfy aadhar card document-fetching
@app.route('/aadharcard', methods=['POST'])
def aadhar_document():

    doc_type = request.json.get('document_type')

    if not doc_type:

        return jsonify({"error": "PAN card number is required"}), 400

    
    # Generate all id share to IDfy server
    task_id = generate_id()
    group_id = generate_id()
    reference_id = generate_id() 

    headers = {
        'account-id': ACCOUNT_ID,
        'api-key': API_KEY,
        'Content-Type': 'application/json',

    }

    data = {
        "task_id": task_id,
        "group_id": group_id,
        "data": {
            "reference_id": reference_id ,
            "key_id": KEY_ID ,
            "ou_id": OU_ID ,
            "secret": SECRET_BASE64,
            "callback_url": CALLBACK_URL,
            "doc_type": doc_type,
            "file_format": "xml",
            "extra_fields": {}

        }
    }

    try:
        # Make the first request to initiate document fetching
        response = requests.post('https://eve.idfy.com/v3/tasks/async/verify_with_source/ind_digilocker_fetch_documents',
                                 headers = headers, json = data)
        
        response.raise_for_status()  # Raise an HTTPError for bad responses

        response_data = response.json()

        request_id = response_data.get('request_id')
        
        if request_id:
            # Make the second request to check the status and get the data
            response_received = requests.get(
                'https://eve.idfy.com/v3/tasks',
                params={'request_id': request_id},
                headers=headers
            )

            if response_received.status_code == 200:
                received_aadhar = response_received.json()

                if received_aadhar:
                    task = received_aadhar[0]

                    # Check if the task is completed
                    if task.get('status') == 'completed':


                        result = task.get('result', {})
                        source_output = result.get('source_output', {})

                        redirect_url = source_output.get('redirect_url')

                        log_data(message=f"Aadhar redirect_url recevied success", event_type='/aadharcard', 
                                    log_level=logging.INFO, additional_context={'Received-Aadhar-Data': task})

                
                        return jsonify({ "redirect_url": redirect_url}), 200
                    
                    # Check if the task failed
                    elif task.get('status') == 'failed':
                            error_message = task.get('message', 'Unknown error')

                            log_data(message=f"Aadhar not recevied redirect_url {error_message}", event_type='/aadharcard', 
                                    log_level=logging.ERROR, additional_context={'Received-Aadhar-Data': task})

                            return jsonify({"error": f"Failed to fetch document - {error_message}", "data": received_aadhar}), 500
                    
                return jsonify({"error": "No data received from the server", "data": received_aadhar}), 500
            
            return jsonify({"error": f"Failed to fetch document - Server response code: {response_received.status_code}"}), 500

        return jsonify({"error": "Request ID not received for your PAN card", "data": response_data}), 500

    except requests.exceptions.RequestException as e:
        
        return jsonify({"error": f"Failed to fetch document - {str(e)}"}), 500

'''
# IDfy aadhar card callback
@app.route('/callback', methods=['GET', 'POST'])
def callback():
        json_data = request.json
        para_data = request.args
        return {"json_data--------": json_data, "parameter_data+++++++++": para_data}

The user, after signing in successfully, gets the url path response.    Please Wait..
                                   This page will close automatically in some time
 https://capture.kyc.idfy.com/document-fetcher/digilocker/callback/?code=936b9b1492cadaff913edca3b532db672519e788&state=d14199be-21fe-4bee-8578-a210976e9c91&hmac=95ae8a41681f52861a38b1148b8b376c1b7d46967c72c7ab4cd03a36e4bd6834

'''
