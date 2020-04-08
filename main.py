from flask import Flask
from flask import request
from flask_sslify import SSLify
from flask import jsonify
import requests
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
URL =  'https://api.telegram.org/bot' + TELEGRAM_TOKEN  + '/'

def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent = 2, ensure_ascii=False)

def send_Message(chat_id, text):
    url = URL + 'sendMessage'
    answer = {'chat_id': chat_id, 'text':text, 'parse_mode': 'HTML'}
    r =requests.post(url, json=answer)
    return r.json()

app = Flask(__name__)
sslify =  SSLify(app)

@app.route('/' + TELEGRAM_TOKEN + '/', methods=['POST', 'GET'])
def main():
    if request.method == 'POST':
        r = request.get_json()
        write_json(r)
        
        try:
            chat_id = r['message']['chat']['id']
        except:
            chat_id = None

        username = r['message']['chat']['username']
        text = 'Привет <b>{}</b>, я готов к работе с API'.format(username)
        if chat_id:
            send_Message(chat_id, text = text)

        return jsonify(r) 


if __name__== '__main__':
    app.run(host = '172.26.1.126',port =88, debug=True, ssl_context=('webhook_cert.pem', 'webhook_pkey.pem'))