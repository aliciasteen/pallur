import os
from os.path import expanduser, realpath
import click
import requests
import json
import click_spinner

api_root = 'http://server.pallur.cloud:5000/api/'

# ----------------------------------------------------------
# Error test

@click.command()
def client_test():
    "PaaS for python"
    pass

@client_test.command()
def errortest():
    r = requests.get(api_root + 'errortest')
    check_status_code(r)

# ----------------------------------------------------------
# Methods
# ----------------------------------------------------------

def check_status_code(r):
    status_code = r.status_code
    try:
        message = r.json()['message']
    except:
        message = 'No Message'
    if status_code == 401:
        click.echo(click.style("You are not logged in or session may have expired. Please login in.", fg='red'))
        quit()
    elif status_code == 200:
        pass
    else:
        click.echo(click.style("%s An error has occured: %s" % (status_code, message), fg='red'))
        quit()

def session_id():
    try:
        file_location = expanduser("~")
        session_file = open(os.path.join(file_location, ".pallursession"),"r")
        session_id = session_file.read()
        return session_id
    except:
        return

if __name__ == '__main__':
    client_test()