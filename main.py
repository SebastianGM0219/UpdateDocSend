from flask import Flask, Response, request, jsonify
from bson.objectid import ObjectId
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from flask_cors import CORS
from flask import Response, stream_with_context
from bson.json_util import dumps
from bson import ObjectId
import time
import boto3
from selenium.webdriver.common.by import By
from threading import Thread
from selenium.common.exceptions import NoSuchElementException
import os
import requests
from selenium.webdriver.common.action_chains import ActionChains

with open('config.env', 'r') as file:
    lines = file.readlines()

# Extract the values
values = {}
for line in lines:
    key, value = line.strip().split(' = ')
    # Remove the surrounding quotes
    value = value.strip('"')
    values[key] = value

os.environ['AWS_ACCESS_KEY_ID'] = values.get('first')
os.environ['AWS_SECRET_ACCESS_KEY'] = values.get('second')
os.environ['AWS_DEFAULT_REGION'] = values.get('third')  # e.g., 'us-west-2'

app = Flask(__name__)
CORS(app)
mongo_client = MongoClient("mongodb+srv://mbrown87:a-X4JoZ-JspDLpo@cluster0.stgvned.mongodb.net/?retryWrites=true&w=majority")
db = mongo_client["DocSendDataBase"]
collection = db["pdf"]

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--ignore-certificate-errors")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

@app.route('/test/', methods= ['POST'])
# @cross_origin()
def hello_world():
  return "#hello world#!!!!"

@app.route('/')
# @cross_origin()
def hello_world1():
  return "#hello world without url#!!!!"
        

     
def test_db_connection():
    print("test_db_connection")
    try:
        client = MongoClient("mongodb+srv://mbrown87:a-X4JoZ-JspDLpo@cluster0.stgvned.mongodb.net/?retryWrites=true&w=majority")
        db1 = client.DocSendDataBase  # Access the pdfdatabase  
        # Check if the connection is successful by accessing a collection
        pdf_collection = db1.pdf
        print( "Successfully connected to database!")
        return pdf_collection
    
    except Exception as e:
        return f"Failed to connect to the database: {e}"
    
@app.route('/download/<pdf_id>', methods=['POST'])
def download_pdf(pdf_id):
    pdf_collection = test_db_connection()
    try:
        pdf_data = pdf_collection.find_one({"_id": ObjectId(pdf_id)})
        s3_client = boto3.client('s3')
        bucket_name = 'docsendpdf'
        print(pdf_data['content'])
        file = s3_client.get_object(Bucket=bucket_name, Key=pdf_data['content'])        
        if not pdf_data:
            return jsonify({'error': 'File not found'}), 404

        def generate(content):
            chunk_size = 1024  # You could change this to another size
            for start in range(0, len(content), chunk_size):
                yield content[start:start + chunk_size]

        response = Response(
            stream_with_context(generate(file['Body'].read())),
            mimetype='application/pdf',
            headers={'Content-Disposition': 'attachment;filename={}.pdf'.format(pdf_id)}
        )
        
        return response
        # return Response(response, mimetype='application/pdf',
        #                 headers={'Content-Disposition': 'attachment;filename={}.pdf'.format(pdf_id)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/show_all/<pdf_id>', methods=['POST'])
def show_pdfs(pdf_id):
    pdf_collection = test_db_connection()
    # pdf_id_integer = int(pdf_id)
    try:
        pdf_documents = pdf_collection.find_one({"_id": ObjectId(pdf_id)})
        if pdf_documents:  # Check if a document is found
            pdf_list = [{'id': str(pdf_documents['_id'])}]  # Extract the ID and convert it to a string
            return jsonify(pdf_list), 200 
        else:
            return jsonify({'error': 'No document found for the given PDF ID'}), 404        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/show_all', methods=['POST'])
def show_all_pdfs():
    pdf_collection = test_db_connection()
    
    try:
        pdf_documents = pdf_collection.find({})
        pdf_list = [{'id': str(doc['_id'])} for doc in pdf_documents]  # Extracting the IDs and converting them to strings

        return jsonify(pdf_list), 200  # Returning the list as JSON
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def check_elements(driver):
    try:
        # Attempt to find the PDF link element
        return driver.find_element(By.XPATH, "//a[contains(@href, '/tmp/') and contains(@href, '.pdf')]")
    except NoSuchElementException:
        # If NoSuchElementException is raised, try to find the error element
        try:
            return driver.find_element(By.XPATH, "//div[@class='error']")
        except NoSuchElementException:
            # If neither element is found, return False
            return False

def check_elementsForSecond(driver):
    try:
        # Attempt to find the PDF link element
        return driver.find_element(By.XPATH, "//a[contains(@href, '/tmp/') and contains(@href, '.pdf')]")
    except NoSuchElementException:
        # If NoSuchElementException is raised, try to find the error element
        try:
            return driver.find_element(By.XPATH, "//div[@class='error']")
        except NoSuchElementException:
            # If neither element is found, return False
            return False

def send_email_key(driver, email):
    email_field = driver.find_element(By.NAME, 'email')
    email_field.send_keys(email)

def send_password_key(driver, password):
    password_field = driver.find_element(By.NAME, 'password')
    password_field.send_keys(password)

def goToSecondSite(url_to_convert, email, password):
    try:
        pdf_collection = test_db_connection()

        downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')    
        # download_directory = '/downloads/'
        chrome_options.add_experimental_option('prefs', {
            'download.default_directory': downloads_folder,
            'download.prompt_for_download': False,  # Disable download prompt
            'plugins.always_open_pdf_externally': True  # Disable PDF viewer so it downloads instead
        })
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://docsend2pdf.com/")

        input_field = driver.find_element(By.NAME, 'url')
        input_field.send_keys(url_to_convert)

        details_tag = driver.find_element(By.TAG_NAME, 'details')

        # Use JavaScript to set the 'open' attribute on the 'details' tag
        driver.execute_script("arguments[0].setAttribute('open', '');", details_tag)

        email_field = driver.find_element(By.NAME, 'email')
        email_new = email
        if(email_new == ""):
            email_new = "lightshinemaya@gmail.com"
        email_field.send_keys(email_new)

        # time.sleep(1)
        if(email != ""):        
            password_field = driver.find_element(By.NAME, 'passcode')
            password_field.send_keys(password)
        # t1 = Thread(target=send_email_key, args=(driver, email))
        # t2 = Thread(target=send_password_key, args=(driver, password))

        # # Start threads
        # t1.start()
        # t2.start()

        # # Wait for both threads to complete
        # t1.join()
        # t2.join()

        # email_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'email')))
        # password_field = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'password')))

        # send keys to the email and password fields
        # email_field.send_keys(email)
        # password_field.send_keys(password)
        # print(email_field)
        # email_value = "lightshinemaya@gmail.com"

        # pass_field = driver.find_element(By.NAME, 'passcode')
        # pass_field.send_keys("Showlightning123")

        convert_button = driver.find_element(By.ID, 'submit')
        convert_button.click()

        
        # timeout = 1200
        # link_element = WebDriverWait(driver, timeout).until(check_elements)

        time.sleep(4)  # A slight delay to ensure the file is downloaded.

        error_element = None
        try:
            print("here")
            error_element = driver.find_elements(By.XPATH, "//p[contains(@class, 'text-danger')] | //center[contains(text(), 'nginx/1.22.0')]")            
            print(error_element)
        except NoSuchElementException:
            pass

        if error_element:
            # If error element is found, return the error message in Flask
            print("error")
            return "error"
        else:
            downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
            seen_files = set()  # A set to keep track   of processed files

            pdf_id = None
            s3_client = boto3.client('s3')
            bucket_name = 'docsendpdf'
            while True:
                time.sleep(0.1)  # Poll every second
                for filename in os.listdir(downloads_folder):
                    if filename.endswith('.pdf') and filename not in seen_files:
                        file_path = os.path.join(downloads_folder, filename)
                        # with open(file_path, "rb") as pdf_file:
                        #     binary_data = pdf_file.read()
                        #     pdf_inserted = pdf_collection.insert_one({"url": url_to_convert, "content": binary_data})
                        #     pdf_id = pdf_inserted.inserted_id
                        with open(file_path, "rb") as file:
                            file_data = file.read()             
                        s3_client.put_object(Bucket=bucket_name, Key=filename, Body=file_data)
                        pdf_inserted = pdf_collection.insert_one({"url": url_to_convert, "content": filename})
                        pdf_id = pdf_inserted.inserted_id
                        # pdf_id = filename
                        os.remove(file_path)  # Optionally remove the file after processing                    
                        break
                        # pdf_inserted = pdf_collection.insert_one({"url": url_to_convert, "content": binary_data})
                if pdf_id is not None: 
                    print(pdf_id)
                    print("Success")
                    data_to_send = {"message": f":large_green_circle: Successful conversion\n:file_folder: https://doc-send-admin-express.vercel.app/{pdf_id}.pdf"}
                    zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/18146786/3xd5t05/'  # You'll replace this URL later
                    requests.post(zapier_webhook_url, json=data_to_send)        
                    return pdf_id
                    break     
    except TimeoutException:
        print(f"Timeout occurred after {100} seconds while waiting for the PDF download link.")
        data_to_send = {"message": f":red_circle: Failed conversion\n→ Inputted URL: {url_to_convert}\n→ Failure reason or log: Timeout occurred after {timeout} seconds while waiting for the PDF download link."}
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/18146786/3xd5t05/'  # You'll replace this URL later
        requests.post(zapier_webhook_url, json=data_to_send)        
        return "error"        
       
            #     
    # wait = WebDriverWait(driver, 100)
    # wait.until(EC.presence_of_element_located((By.ID, 'download')))

    # download_button = driver.find_element(By.ID, 'download')
    # download_button.click()
    
    # try:
    # print("waiting")

    # wait = WebDriverWait(driver, 100)
    # wait.until(EC.presence_of_element_located((By.ID, 'download')))
    # download_button = driver.find_element(By.ID, 'download')
    # print("find_download_button")
    # print(download_button)
    # download_button.click()

    # wait = WebDriverWait(driver, 100)
    # try:
    #     download_button = wait.until(EC.presence_of_element_located((By.ID, 'toolBar')))
    #     print("Download button found")
    #     download_button.click()
    #     return jsonify({'message': 'PDF converted and saved to MongoDB', 'pdf_id': str(pdf_id)}), 200 

    # except TimeoutException:
    #     print("Download button was not found within the given time frame")
    # return "Download button is present!"

    # except TimeoutException:
    #     print("waiting download button")

    #     return "Waiting for download button timed out."
    # finally:
    #     print("quit driver")

    #     driver.quit()    
   

@app.route('/convert', methods=['POST'])
def convert():
    
    try:
        data = request.get_json()  # Use get_json to extract JSON data from the request
        url_to_convert = data.get('url')
        email_to_convert = data.get('email')
        password_to_convert = data.get('password')

        pdf_collection = test_db_connection()

        # if not url_to_convert:
        #     return jsonify({'error': 'No URL provided'}), 400
        
        # driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        # driver.get("http://deck2pdf.com")
        # input_field = driver.find_element(By.ID, 'docsendURL')
        # input_field.send_keys(url_to_convert)
        # convert_button = driver.find_element(By.CLASS_NAME, 'btn-primary')
        # convert_button.click()

        # timeout = 1200
        # link_element = WebDriverWait(driver, timeout).until(check_elements)
        



        pdf_id= goToSecondSite(url_to_convert,email_to_convert,password_to_convert)
        if(pdf_id == "error"):
            data_to_send = {"message": f":red_circle: Failed conversion\n→ Inputted URL: {url_to_convert}\n→ Failure reason or log: Unable to download this view."}
            zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/18146786/3xd5t05/'  # You'll replace this URL later
            requests.post(zapier_webhook_url, json=data_to_send)                    
            return jsonify({'error': 'Timeout occurred while waiting for the PDF download link.'}), 500
        else:
            return jsonify({'message': 'PDF converted and saved to MongoDB', 'pdf_id': str(pdf_id)}), 200      
        # if "error" == link_element.get_attribute("class"):
        #     error_text = "Error: Request failed with status code 404" 
        #     if error_text in link_element.text:
        #         pdf_id= goToSecondSite(url_to_convert)
        #         return jsonify({'message': 'PDF converted and saved to MongoDB', 'pdf_id': str(pdf_id)}), 200                          
        #     else:
        #         # HANDLE OTHER ERRORS IF NECESSARY
        #         pass
        # else:
        #     # Clicking the PDF link
        #     link_element.click()
            
        #     downloads_folder = os.path.join(os.path.expanduser('~'), 'Downloads')
        #     seen_files = set()  # A set to keep track   of processed files

        #     time.sleep(2)  # A slight delay to ensure the file is downloaded.

        #     pdf_id = None
        #     while True:
        #         time.sleep(0.1)  # Poll every second
        #         for filename in os.listdir(downloads_folder):
        #             if filename.endswith('.pdf') and filename not in seen_files:
        #                 file_path = os.path.join(downloads_folder, filename)
        #                 with open(file_path, "rb") as pdf_file:
        #                     binary_data = pdf_file.read()
        #                     pdf_inserted = pdf_collection.insert_one({"url": url_to_convert, "content": binary_data})
        #                     pdf_id = pdf_inserted.inserted_id
        #                 os.remove(file_path)  # Optionally remove the file after processing                    
        #                 break
        #                 # pdf_inserted = pdf_collection.insert_one({"url": url_to_convert, "content": binary_data})
        #         if pdf_id is not None: 
        #             print(pdf_id)
        #             print("Success")
        #             data_to_send = {"message": f":large_green_circle: Successful conversion\n:file_folder: https://doc-send-admin-express.vercel.app/{pdf_id}.pdf"}
        #             zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/18146786/3xd5t05/'  # You'll replace this URL later
        #             requests.post(zapier_webhook_url, json=data_to_send)        

        #             return jsonify({'message': 'PDF converted and saved to MongoDB', 'pdf_id': str(pdf_id)}), 200                          
        #             # break
            
        # return jsonify({'message': 'PDF converted and saved to MongoDB'}), 200
    except TimeoutException:
        print(f"Timeout occurred after {timeout} seconds while waiting for the PDF download link.")
        data_to_send = {"message": f":red_circle: Failed conversion\n→ Inputted URL: {url_to_convert}\n→ Failure reason or log: Timeout occurred after {timeout} seconds while waiting for the PDF download link."}
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/18146786/3xd5t05/'  # You'll replace this URL later
        requests.post(zapier_webhook_url, json=data_to_send)        
        
        return jsonify({'error': 'Timeout occurred while waiting for the PDF download link.'}), 500
    except Exception as e:
        data_to_send = {"message": f":red_circle: Failed conversion\n→ Inputted URL: {url_to_convert}\n→ Failure reason or log: An error occurred: {e}"}
        zapier_webhook_url = 'https://hooks.zapier.com/hooks/catch/18146786/3xd5t05/'  # You'll replace this URL later
        requests.post(zapier_webhook_url, json=data_to_send)        
     
        return jsonify({'error': f'An error occurred: {e}'}), 500
    
if __name__ == '__main__':
    app.run(debug=True)    
                                                                                 