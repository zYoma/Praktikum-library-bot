from flask import Flask  # используем Flask
from flask import request  # у фласка есть свой request
from flask_sslify import SSLify  # данная библиотека необходима для работы с SSL
from flask import jsonify
import requests
import json
import re
from dotenv import load_dotenv
import os
from parsing import get_content
import time

load_dotenv()
# объявляем переменные
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
URL = 'https://api.telegram.org/bot' + TELEGRAM_TOKEN + '/'
search_dict = {}
create_dict = {}
re_start_word = r"(^|\s)%s"

# метод записывает полученный от телеграмм ответ в json файл в
# удобочитаемом виде с поддержкой кририлицы


def write_json(data, filename='answer.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# метод отправляет сообщение от имени бота


def send_Message(chat_id, text):
    url = URL + 'sendMessage'
    kb_markup = {'resize_keyboard': True, 'keyboard': [[{'text': 'Разделы'}, {
        'text': 'Поиск'}], [{'text': 'Добавить запись'}, {'text': 'Все записи'}]]}
    answer = {'chat_id': chat_id, 'text': text,
              'reply_markup': kb_markup, 'parse_mode': 'HTML'}
    r = requests.post(url, json=answer)
    return r.json()

# метод отправляет результаты поиска в inline режим


def send_inline_results(id, result):
    url = URL + 'answerInlineQuery'
    results = []
    for post in result:
        input_message_content = {
            'message_text': post['url'], 'parse_mode': 'Markdown'}
        data = {
            'type': 'article',
            'title': post['title'],
            'id': post['id'],
            'input_message_content': input_message_content
        }
        results.append(data)

    answer = {
        'inline_query_id': id,
        'results': json.dumps(results),
    }
    r = requests.post(url, json=answer)
    return r.json()

# дергаем api


def get_posts():
    api = 'http://3.126.19.96:5000/api/v1/posts/'
    r = requests.get(api)
    result = []
    for post in r.json():
        title = post.get('title')
        description = post.get('description')
        url = post.get('url')
        id = post.get('id')
        data = {
            'title': title,
            'description': description,
            'url': url,
            'id': id
        }
        result.append(data)

    return result


def create_post(create_dict):
    api = 'http://3.126.19.96:5000/api/v1/posts/'
    data = {
        'title': create_dict['title'],
        'description': create_dict['description'],
        'url': create_dict['url'],
        'language': 'RU'
    }
    r = requests.post(api, data=data)


def search(query):
    text = re.escape(query.lower())
    posts = get_posts()
    result = [post for post in posts if re.search(
        re_start_word % text, str(post['title'].lower()))]
    return result

# создаем экземпляр фласка
app = Flask(__name__)
sslify = SSLify(app)

# если прилетает запрос разрешенного метода по данному маршруту, выполняем
# функцию main


@app.route('/' + TELEGRAM_TOKEN + '/', methods=['POST', 'GET'])
def main():
    if request.method == 'POST':
        r = request.get_json()  # читаем что нам прилетело
        write_json(r)  # пишем в файлик
        # если бот вызван в inlineрежиме
        if 'inline_query' in r:
            id = r['inline_query']['id']
            query = r['inline_query']['query']
            result = search(query)
            if result:
                send_inline_results(id, result)
            return jsonify(r)

        try:
            # получаем  id юзера, может не быть если бот например в канале или
            # группе
            chat_id = r['message']['chat']['id']
        except:
            chat_id = None
        if chat_id:
            message = r['message']['text']
            username = r['message']['chat'][
                'username']  # получаем имя пользователя

            # Если введен поисковой запрос
            if chat_id in search_dict:
                result = search(message)
                if result:
                    for post in result:
                        send_Message(chat_id, text=post['url'])

                else:
                    send_Message(chat_id, text='Я ничего не смог найти!')
                search_dict.pop(chat_id)
                return jsonify(r)

            # отмена
            if re.search(r'/exit', message):
                create_dict.pop(chat_id)
                send_Message(chat_id, text='ок!')
                return jsonify(r)

            # Добавление поста
            if chat_id in create_dict:
                # if create_dict[chat_id]['title'] == None:
                #     create_dict[chat_id]['title'] = message
                #     send_Message(
                # chat_id, text='<b>Введите описание</b>\n<i>Для отмены
                # -/exit</i>')
                if create_dict[chat_id]['description'] == None:
                    create_dict[chat_id]['description'] = message
                    send_Message(
                        chat_id, text='<b>Кидай мне ссылку, дальше я разберусь.</b>\n<i>Для отмены - /exit</i>')
                elif create_dict[chat_id]['url'] == None:
                    try:
                        message_type = r['message']['entities'][0]['type']
                    except KeyError:
                        send_Message(
                            chat_id, text='<b>Я жду от вас именно ссылку, не текст и не смайлы.</b>\n<i>Для отмены -/exit</i>')
                    else:
                        title = get_content(message)
                        create_dict[chat_id]['title'] = title
                        create_dict[chat_id]['url'] = message
                        create_post(create_dict[chat_id])
                        send_Message(chat_id, text='Я это запомню!')
                        create_dict.pop(chat_id)
                return jsonify(r)

            if re.search(r'Разделы', message):
                text = 'Скоро я буду предлагать контент по разной тематике 😜'
            elif re.search(r'Поиск', message):
                text = 'Что будем искать?'
                search_dict[chat_id] = username

            elif re.search(r'https://stackoverflow.com/questions/35956045/extract-title-with-beautifulsoup/35956388', message):
                get_content(message)
                text = 'Что будем искать?'

            elif re.search(r'Добавить запись', message):
                text = '<b>О чем статья? Чем она полезна?</b>\n<i>Для отмены - /exit</i>'
                create_dict[chat_id] = {
                    'title': None,
                    'description': None,
                    'url': None,
                }

            elif re.search(r'Все записи', message):
                posts = get_posts()
                for post in posts:
                    text = '{}'.format(post['url'])
                    send_Message(chat_id, text=text)
                    time.sleep(1)
                return jsonify(r)
            else:
                text = 'Привет <b>{}</b>, я готов к работе с API'.format(
                    username)

            send_Message(chat_id, text=text)  # отвечаем

        return jsonify(r)

# если скрипт запушен самостоятельно, а не импортирован, то стартуем
# сервер на указанном ip и порту. указываем сертификаты для работы с
# телеграмм
if __name__ == '__main__':
    app.run(host='172.26.1.126', port=88, debug=True,
            ssl_context=('webhook_cert.pem', 'webhook_pkey.pem'))
