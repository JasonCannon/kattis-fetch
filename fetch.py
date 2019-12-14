import argparse
import os
import sys
import re
import requests
import requests.exceptions
import configparser
import json
from datetime import datetime
from bs4 import BeautifulSoup

_EMAIL = None # Required by the user, will be updated in the main function
_DEFAULT_CONFIG = '/usr/local/etc/kattisrc'

_HEADERS = {'User-Agent': 'kattis-accepted-fetch by {}'.format(_EMAIL),
            'From':_EMAIL}

def get_url(cfg, option, default):
    if cfg.has_option('kattis', option):
        return cfg.get('kattis', option)
    else:
        return 'https://{}/{}'.format(cfg.get('kattis', 'hostname'), default)

def get_config():
    """ Returns a ConfigParser object for the .kattisrc file(s) """
    cfg = configparser.ConfigParser()
    if os.path.exists(_DEFAULT_CONFIG):
        cfg.read(_DEFAULT_CONFIG)

    if not cfg.read([os.path.join(os.getenv('HOME'), '.kattisrc'),
                     os.path.join(os.path.dirname(sys.argv[0]), '.kattisrc')]):
        raise configparser.Error('''\
I failed to read in a config file from your home directory or from the
same directory as this script. To download a .kattisrc file please visit
https://<kattis>/download/kattisrc
The file should look something like this:
[user]
username: yourusername
token: *********
[kattis]
hostname: <kattis>
loginurl: https://<kattis>/login
submissionurl: https://<kattis>/submit
submissionsurl: https://<kattis>/submissions''')
    return cfg

def login(login_url, username, password=None, token=None):
    """ Authenticates users """
    login_args = {'user': username, 'script': 'true'}
    if password:
        login_args['password'] = password
    if token:
        login_args['token'] = token
    return requests.post(login_url, data=login_args, headers=_HEADERS)

def login_from_config(cfg):
    """ Authenticates user from .kattisrc file """
    username = cfg.get('user', 'username')
    password = token = None
    try:
        password = cfg.get('user', 'password')
    except configparser.NoOptionError:
        pass
    try:
        token = cfg.get('user', 'token')
    except configparser.NoOptionError:
        pass
    if password is None and token is None:
        raise configparser.Error('It looks like the .kattisrc file appears to be corrupted.')
    loginurl = get_url(cfg, 'loginurl', 'login')
    return login(loginurl, username, password, token)

def submissions(submissions_url, cookies):
    """ Get submissions """
    data = {'script': 'true'}
    return requests.get(submissions_url, data=data, cookies=cookies, headers=_HEADERS)

def get_problem(keys, soup):
    """ Format individual solved problem """
    link = soup.find(class_='name_column').find('a', href=True)['href']
    row = soup.get_text()
    return dict(zip(keys, [link.split('/')[2]] + list(row.strip().split('\n'))))

def get_stats(cfg, login_reply, problem_cnt=None):
    """ Gets the users stats """
    username = cfg.get('user', 'username')
    profile_url = get_url(cfg, '', 'users/%s' % username)
    try:
        result = submissions(profile_url, login_reply.cookies)
    except requests.exceptions.RequestException as err:
        print('Profile connection failed:', err)
        sys.exit(1)
    soup = BeautifulSoup(result.text, 'html.parser')
    header = soup.find('div', {'class': 'rank clearfix'})
    out = []
    for tr in header.find_all('tr'):
        out.append([td.text.strip() for td in tr.find_all('td')])

    if problem_cnt is not None:
        out[0].append('Solved')
        out[1].append(str(problem_cnt))
    return dict(zip(out[0], out[1]))

def extract_problems(cfg, login_reply, filename='kattis'):
    """ Stores solved prolbems and stats in .json file """
    data = {}
    solved = []
    header_url = get_url(cfg, '', 'problems')
    try:
        result = submissions(header_url, login_reply.cookies)
    except requests.exceptions.RequestException as err:
        print('Submissions connection failed:', err)
        sys.exit(1)
    soup = BeautifulSoup(result.text, 'html.parser')
    header = soup.find_all('a', href=lambda href: href and '?order=' in href)
    keys = ['ID'] + [link.get_text().strip() for link in header]
    problem_cnt = 0
    # i.e. inf (just so we won't loop forever, no chance of 100 pages of problems)
    for page_num in range(100):
        submissions_url = get_url(cfg, '', 'problems?page=%d&show_solved=on&show_tried=off&show_untried=off' % page_num)
        try:
            result = submissions(submissions_url, login_reply.cookies)
        except requests.exceptions.RequestException as err:
            print('Submissions connection failed:', err)
            sys.exit(1)

        if result.status_code != 200:
            print('Fetching submissions failed.')
            if result.status_code == 403:
                print('Access denied (403)')
            elif result.status_code == 404:
                print('Incorrect submissions URL (404)')
            else:
                print('Status code:', result.status_code)
            sys.exit(1)
        
        soup = BeautifulSoup(result.text, 'html.parser')
        problems = soup.find_all('tr', {'class': ['odd solved', 'even solved']})
        if not len(problems):
            break
        for p in problems:
            solved.append(get_problem(keys, p))
            problem_cnt += 1

    data['stats'] = get_stats(cfg, login_reply, problem_cnt)
    data['solved'] = solved
    with open('{}.json'.format(filename), 'w') as file_out:
        json.dump(data, file_out, indent=4)
    return problem_cnt

def check(email):
    return bool(re.search('^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$', email))

def main(args):
    if not check(args.email):
        print('Please enter a valid Kattis account email address.')
        sys.exit(1)

    _EMAIL = args.email
    _HEADERS = {'User-Agent': 'kattis-accepted-fetch by {}'.format(_EMAIL),
            'From':_EMAIL}

    try:
        cfg = get_config()
    except configparser.Error as exc:
        print(exc)
        sys.exit(1)

    try:
        login_reply = login_from_config(cfg)
    except configparser.Error as exc:
        print(exc)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        print('Login connection failed:', err)
        sys.exit(1)

    if not login_reply.status_code == 200:
        print('Login failed.')
        if login_reply.status_code == 403:
            print('Incorrect username or password/token (403)')
        elif login_reply.status_code == 404:
            print('Incorrect login URL (404)')
        else:
            print('Status code:', login_reply.status_code)
        sys.exit(1)

    cnt = extract_problems(cfg, login_reply)
    get_stats(cfg, login_reply, cnt)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Downloads user\'s Kattis statistics.')
    parser.add_argument(dest='email', metavar='kattis_email', type=str, help='Email address used for Kattis account')
    args = parser.parse_args()
    main(args)
