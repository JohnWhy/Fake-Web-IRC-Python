import json

users = 'B:/PyCharm/FakeyWebIRC/users.json'  # recommend not keeping this in the root folder of your website


def get_json():
    f = open(users, 'r')
    json_object = json.load(f)
    f.close()
    return json_object


def check_json(user):
    j = open(users, 'r')
    data = json.load(j)
    j.close()
    for item in data['users']:
        if user in item.keys():
            return item[user]
    return False


def add_user(user, hashed_password):
    json_object = get_json()
    json_object['users'].append({user: hashed_password})
    njo = json.dumps(json_object)
    with open(users,'w') as f:
        f.write(njo)
    return True


def login(user, hashed_password):
    json_pw = check_json(user)
    if json_pw == False:
        return add_user(user, hashed_password)
    else:
        if hashed_password == json_pw:
            return True
        return False
