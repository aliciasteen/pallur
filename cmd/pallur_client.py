import os
from os.path import expanduser, realpath
import click
import requests
import json
import click_spinner

api_root = 'http://server.pallur.cloud:5000/api/'

@click.group()
def pallur_client():
    "PaaS for python"
    pass

@pallur_client.group()
def project():
    """Interact with, create and destroy projects"""
    pass

@pallur_client.group()
def user():
    """User login, logout, management and deletion"""
    pass

#TODO Send configuration file, and project name
@project.command()
@click.option('--name', '-n' , default='NewProject', help='Project name', prompt=True)
@click.option('--configuration', type=click.File('r'), help='Path of configuration file', prompt='Configuration file path')
def create(name, configuration):
    """Create new project"""
    headers = {'session_id': session_id()}
    url = api_root + 'projects'
    data = configuration.read()
    click.echo('Initalising project %s' % name)
    with click_spinner.spinner():
        try:
            r = requests.post(url, data=data, headers=headers)
            check_status_code(r.status_code)
        except requests.exceptions.ConnectionError as e:
            click.echo("Connection error. Please wait and try again.")        
    

@project.command()
@click.option('--name', help='Project Name', prompt=True)
def status(name):
    headers = {'session_id': session_id()}
    url = api_root + 'projects/' + name
    r = requests.get(url, headers=headers)
    check_status_code(r.status_code)
    click.echo(json.dumps(r.json(), indent=4, separators=(',', ': ')))
    
@project.command()
@click.option('--name', default='NewProject', help='Project name') 
def up(name):
    """Project up"""
    click.echo('project up %s' % name)

@project.command()
def delete():
    """Delete project"""
    click.echo('Deleted project')

@project.command()
def down():
    """project down"""
    click.echo('project down')

@project.command()
def update():
    """project update"""
    click.echo('project update')

@project.command()
def list():
    """project list"""
    click.echo('project list')

def session_id():
    try:
        file_location = expanduser("~")
        session_file = open(os.path.join(file_location, ".pallursession"),"r")
        session_id = session_file.read()
        return session_id
    except:
        return

def check_status_code(status_code):
    if status_code == 401:
        click.echo(click.style("You are not logged in or session may have expired. Please login in.", fg='red'))
        quit()
    elif status_code == 200:
        pass
    else:
        click.echo(click.style("%s An error has occured." % status_code, fg='red'))
        quit()

@pallur_client.command()
@click.option('--username', prompt=True, help='username')
@click.password_option(confirmation_prompt=False)
def login(username, password):
    """Login to Pallur"""
    r = requests.post(api_root + 'login', json={'username': username, 'password': password})
    if r.status_code == 401:
        click.echo("Login failed please try again")
    else:
        session_id = (r.json()['session_id'])
        file_location = expanduser("~")
        session_file = open(os.path.join(file_location, ".pallursession"),"w")
        click.echo(session_id)
        session_file.write(session_id)
        session_file.close

if __name__ == '__main__':
    pallur_client()
