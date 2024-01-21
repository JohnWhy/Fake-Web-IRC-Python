import json

def get_json():
    f = open('irc_chat.json', 'r')
    json_object = json.load(f)
    f.close()
    return json_object


def get_msg_id(text):
    chat = get_json()
    msgs = []
    msg_ids = []
    for i in chat:
        if text in i['text']:
            msgs.append(i)
            msg_ids.append(i['id'])
    return msg_ids,msgs


def delete_msg_id(id):
    chat = get_json()
    print(chat[0])
    for i in chat:
        if i['id'] == id:
            print(i)
            i['text'] = '* THIS MESSAGE HAS BEEN DELETED BY AN ADMINISTRATOR *'
            print(i)
    f = open('irc_chat.json', 'w')
    json.dump(chat, f)
    f.close()


def full_delete_msg_id(id):
    chat = get_json()
    print(chat[0])
    for i in chat:
        if i['id'] == id:
            chat.remove(i)
    f = open('irc_chat.json', 'w')
    json.dump(chat, f)
    f.close()

# Get MSG IDs of offending messages
# Delete Msgs
# Restart Flask IRC