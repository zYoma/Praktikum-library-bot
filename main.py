from flask import Flask # используем Flask
from flask import request # у фласка есть свой request
from flask_sslify import SSLify # данная библиотека необходима для работы с SSL 
from flask import jsonify
import requests
import json
import re
from dotenv import load_dotenv
import os

load_dotenv()
# объявляем переменные
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
URL =  'https://api.telegram.org/bot' + TELEGRAM_TOKEN  + '/'

# метод записывает полученный от телеграмм ответ в json файл в удобочитаемом виде с поддержкой кририлицы
def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent = 2, ensure_ascii=False)

# метод отправляет сообщение от имени бота
def send_Message(chat_id, text):
    url = URL + 'sendMessage'
    kb_markup = {'resize_keyboard': True, 'keyboard':[[{'text': 'Каталог'},{'text': 'Поиск'}],[{'text': 'Добавить запись'},{'text': 'Все'}]]}
    answer = {'chat_id': chat_id, 'text':text, 'reply_markup':kb_markup, 'parse_mode': 'HTML'}
    r =requests.post(url, json=answer)
    return r.json()

# создаем экземпляр фласка
app = Flask(__name__)
sslify =  SSLify(app)

# если прилетает запрос разрешенного метода по данному маршруту, выполняем функцию main
@app.route('/' + TELEGRAM_TOKEN + '/', methods=['POST', 'GET'])
def main():
    if request.method == 'POST':
        r = request.get_json() # читаем что нам прилетело
        write_json(r) # пишем в файлик
        
        try:
            chat_id = r['message']['chat']['id'] # получаем  id юзера, может не быть если бот например в канале или группе
        except:
            chat_id = None
        if chat_id:
            message = r['message']['text']
            username = r['message']['chat']['username'] # получаем имя пользователя
            if re.search(r'Каталог', message):
                text = 'Ребята еще не написали сайт!'
            elif re.search(r'Поиск', message):
                text = 'Искать негде, ждем пока мне API подключат!'
            elif re.search(r'Добавить запись', message):
                text = 'У меня очень короткая память, а сохранить некуда('
            elif re.search(r'Все', message):
                text = '*пустой список*'
            else:
                text = 'Привет <b>{}</b>, я готов к работе с API'.format(username)
            
            send_Message(chat_id, text = text) # отвечаем

        return jsonify(r) 

# если скрипт запушен самостоятельно, а не импортирован, то стартуем сервер на указанном ip и порту. указываем сертификаты для работы с телеграмм
if __name__== '__main__':
    app.run(host = '172.26.1.126',port =88, debug=True, ssl_context=('webhook_cert.pem', 'webhook_pkey.pem'))