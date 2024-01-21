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
active_sessions = {}
active_users = 0
active_usernames = ''
active_sids = []


def update_active_usernames(remove_name=None):
    active_usernames = ''
    if remove_name == None:
        for i in active_sessions.keys():
            active_usernames += active_sessions[i]['name'] + '\n'
    else:
        name = active_sessions[request.remote_addr]['name']
        for i in active_sessions.keys():
            if active_sessions[i]['name'] != name:
                active_usernames += active_sessions[i]['name'] + '\n'
    return active_usernames


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


@socketio.on('connect')
def load_chat(data):
    global active_sessions, active_users, active_sids
    f = open('irc_chat.json','r')
    j = json.load(f)
    f.close()
    try:
        logging.info('New Session Created: ' + str(request.sid) + ' | '+request.remote_addr)
    except Exception as e:
        logging.warning(str(e) + ': Unable to get session info.')
    for i in j[-50:]:
        emit('send_msg', i)
    if request.remote_addr not in active_sessions.keys():
        active_sids.append(str(request.sid))
        active_sessions[request.remote_addr] = {'short_sid': str(request.sid)[0:4],
                                                'sid': [str(request.sid)],
                                                'name': '['+str(request.sid)[0:4]+'] Anonymous'}
        active_users += 1
        emit('update_users', {'value': 'Users Online: ' + str(active_users)}, broadcast=True)
        user_list = update_active_usernames()
        emit('update_user_list', {'value': user_list}, broadcast=True)
        logging.info(str(active_sessions[request.remote_addr]['name']) + ' has connected to chat.')
        emit('send_msg', {'info': '<span style="color:green;">'+str(active_sessions[request.remote_addr]['name'])+' has connected to chat.</span>',
             'text': ''}, broadcast=True)
    else:
        still_active = False
        for i in active_sessions[request.remote_addr]['sid']:
            if i in active_sids:
                still_active = True
        if still_active == False:
            active_users += 1
            logging.info(str(active_sessions[request.remote_addr]['name']) + ' has reconnected to chat.')
            emit('send_msg', {'info': '<span style="color:green;">' + str(active_sessions[request.remote_addr]['name']) + ' has reconnected to chat.</span>',
                              'text': ''}, broadcast=True)
        active_sids.append(str(request.sid))
        active_sessions[request.remote_addr]['sid'].append(str(request.sid))
        emit('update_users', {'value': 'Users Online: ' + str(active_users)}, broadcast=True)
        user_list = update_active_usernames()
        emit('update_user_list', {'value': user_list}, broadcast=True)



@socketio.on('disconnect')
def remove_user():
    global active_sessions, active_users, active_sids
    active_sids.remove(str(request.sid))
    still_active = False
    for i in active_sessions[request.remote_addr]['sid']:
        if i in active_sids:
            still_active = True
    if still_active == False:
        active_users -= 1
        logging.info(str(active_sessions[request.remote_addr]['name'])+' has left the chat.')
        emit('send_msg', {'info': '<span style="color:yellow;">' + str(active_sessions[request.remote_addr]['name']) + ' has left the chat.</span>',
                          'text': ''}, broadcast=True)
        emit('update_users', {'value': 'Users Online: '+str(active_users)}, broadcast=True)
        user_list = update_active_usernames(remove_name=active_sessions[request.remote_addr]['name'])
        emit('update_user_list', {'value': user_list}, broadcast=True)


@socketio.on('send_msg')
def handle_message(data):
    global active_sessions, active_usernames
    try:
        logging.info('Received message from: '+str(request.sid)+' | '+request.remote_addr)
    except Exception as e:
        logging.warning(str(e)+': Unable to get session info.')
    text = str(data['text'])
    username = str(data['username'])
    password = str(data['password'])
    now = datetime.datetime.now()
    timestamp = now.strftime('[%Y-%m-%d %H:%M:%S] ')
    if text != '':
        if username == '':
            username = '['+active_sessions[request.remote_addr]['short_sid']+'] Anonymous'
            userinfo = get_style(timestamp, username)
            msg = clean(text)
            d = {'info': userinfo, 'text': msg}
            emit('send_msg', d, broadcast=True)
            logging.info(username+': '+msg)
            log(d)
            if username not in active_usernames:
                active_sessions[request.remote_addr]['name'] = username
                user_list = update_active_usernames()
                emit('update_user_list', {'value': user_list}, broadcast=True)
        else:
            result = login(username, get_hash(password))
            if result == False:
                emit('send_msg', {'info': '<span style="color:red;">Bad Password on Login</span>', 'text': ''})
                # if pw is bad
                logging.info('Bad Password on Login: '+str(username))
            else:
                username = '['+active_sessions[request.remote_addr]['short_sid']+'] '+username
                userinfo = get_style(timestamp, username)
                msg = clean(text)
                d = {'info': userinfo, 'text': msg}
                emit('send_msg', d, broadcast=True)
                logging.info(username+': '+msg)
                log(d)
                if username not in active_usernames:
                    active_sessions[request.remote_addr]['name'] = username
                    user_list = update_active_usernames()
                    emit('update_user_list', {'value': user_list}, broadcast=True)


@app.route('/chat')
def chat():
    return render_template('chat.html', async_mode=socketio.async_mode)


if __name__ == '__main__':
    socketio.run(app, allow_unsafe_werkzeug=True)


# if __name__ == "__main__":
#     # uncomment if you want ssl and have a cert/pkey
#     # context = ('cert.pem','pkey.pem')
#     app.run(host='0.0.0.0') #, ssl_context=context)
