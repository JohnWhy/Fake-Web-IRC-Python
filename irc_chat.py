from flask import Blueprint, Flask, render_template, request, flash, session, redirect, url_for
from flask_socketio import SocketIO, emit
from threading import Lock
from json_cmds import *
import re
import hashlib
import datetime
import logging
import json
LOG_FOLDER = 'logs/'
log_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H')
logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s",
                    level=logging.DEBUG,
                    handlers=[
                        logging.FileHandler(LOG_FOLDER+log_timestamp + "_IRC_chat.log"),
                        logging.StreamHandler()
                    ]
                    )

async_mode = None

app = Flask(__name__)
auth = Blueprint('auth', __name__)
# app.config['SECRET_KEY'] = '---'  # change
socketio = SocketIO(app, async_mode=async_mode)

thread = None
thread_lock = Lock()


def clean(string):
    # removes characters that might execute code
    return re.sub(r'[^a-zA-Z0-9/!?[]{}():.,\'" -]', r'', string)


def get_hash(pw):
    h = hashlib.sha256(pw.encode('utf-8'))
    return h.hexdigest()


def get_token(username, hashed_pw):
    # gets the token for the user for comparison
    global session_tokens
    t = hashed_pw + datetime.datetime.now().strftime('%H%M%S')
    h = hashlib.sha256(t.encode('utf-8'))
    token = h.hexdigest()[0:5]
    session_tokens[username] = token
    return token


def get_style(timestamp,username):
    # can be adjusted or built out to allow custom colors for different users
    # this currently makes PPR user Red (admin acc)
    if username=='PPR' or username=='ppr':
        color_val='Red'
    else:
        color_val='#337dff'  # default user color
    info = timestamp+username
    return '<span style="color:'+color_val+';">'+info+': </span>'


def log(d):
    try:
        f = open('irc_chat.json','r')
        j = json.load(f)
        f.close()
    except:
        j = []
        pass
    f = open('irc_chat.json', 'w')
    j.append(d)
    json.dump(j, f)
    f.close()


@socketio.on('my_event')
def load_chat():
    f = open('irc_chat.json','r')
    j = json.load(f)
    for i in j:
        emit('send_msg', i)



@socketio.on('send_msg')
def handle_message(data):
    text = str(data['text'])
    username = str(data['username'])
    password = str(data['password'])
    now = datetime.datetime.now()
    timestamp = now.strftime('[%Y-%m-%d %H:%M:%S] ')
    if text != '':
        if username == '':
            username = "Anonymous"
            userinfo = get_style(timestamp, username)
            msg = clean(text)
            d = {'info': userinfo, 'text': msg}
            emit('send_msg', d, broadcast=True)
            logging.info(username+': '+msg)
            log(d)
        else:
            result = login(username, get_hash(password))
            if result == False:
                emit('send_msg', {'info': '<span style="color:red;">Bad Password on Login</span>', 'text': ''})
                # if pw is bad
                logging.info('Bad Password on Login: '+str(username))
            else:
                userinfo = get_style(timestamp, username)
                msg = clean(text)
                d = {'info': userinfo, 'text': msg}
                emit('send_msg', d, broadcast=True)
                logging.info(username+': '+msg)
                log(d)


@app.route('/chat')
def chat():
    return render_template('chat.html', async_mode=socketio.async_mode)



if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)


# if __name__ == "__main__":
#     # uncomment if you want ssl and have a cert/pkey
#     # context = ('cert.pem','pkey.pem')
#     app.run(host='0.0.0.0') #, ssl_context=context)
