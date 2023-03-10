from flask import Flask, render_template, request, flash
from json_cmds import *
import re
import hashlib
import datetime


app = Flask(__name__)
app.config['SECRET_KEY'] = '---'  # change


session_tokens = {}
# keeps info on who is already authenticated
# probably should clean this up if session is inactive for too long...


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


def send_msg(username, chat):
    now = datetime.datetime.now()
    timestamp = now.strftime('[%Y-%m-%d %H:%M:%S] ')
    msg = get_style(timestamp,username)+clean(chat)
    overwrite = open('last_msg.html','w')  # update last msg for iframe refresh javascript code
    overwrite.write('<p>'+msg+'</p>')
    overwrite.close()
    read = open('irc_chat.html','r+')  # get the current msg list
    rlist = read.readlines()
    read.close()
    rwrite = open('irc_chat.html','w')  # open for writing
    rlist.insert(rlist.index('</dl>\n'),"<p>"+str(msg)+'</p>\n')  # write the msg user sent to the file
    for i in rlist:
        rwrite.write(i)  # save changes
    rwrite.close()  # close html file


@app.route('/chat', methods=['GET', 'POST'])
def web_login():
    global session_tokens
    if request.method == 'POST':
        username = request.form['Username'][:16]
        password = request.form['Password'][:16]
        chat = request.form['Msg'][:256]
        if chat != '':  # if chat is blank, we don't want to send anything
            if username == '':  # this controls anonymous posting and maintains same anonymous tag during session
                token = get_token(username, get_hash('anon'))
                username = "anonymous_"+str(token)[0:2]
                session_tokens[username] = token
                send_msg(username, chat)
                return render_template('chat.html', user=username, pw=token)  # keep generated name/token on re-render
            else:
                if username in session_tokens.keys():
                    if session_tokens[username] == password:
                        send_msg(username, chat)
                        return render_template('chat.html', user=username, pw=password)  # keep username/pw on re-render
                        # note: at this point the password is actually the token since it's matching to the sessions.
                result = login(username, get_hash(password))
                if result == False:
                    flash('Bad password for account.')  # if pw is bad
                    return render_template('chat.html', chat=chat, user=username)  # keep whatever was written+username
                else:
                    token = get_token(username, get_hash(password))
                    session_tokens[username] = token
                    send_msg(username, chat)
                    return render_template('chat.html', user=username, pw=token)  # keep username/token on re-render
        else:
            flash('No message entered.')  # flash that no message is entered
            return render_template('chat.html', user=username, pw=password)  # keep user/pass if entered
    return render_template('chat.html')


if __name__ == "__main__":
    # uncomment if you want ssl and have a cert/pkey
    # context = ('cert.pem','pkey.pem')
    app.run(host='0.0.0.0') #, ssl_context=context)
