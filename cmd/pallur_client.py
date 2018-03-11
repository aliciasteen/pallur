import os
from os.path import expanduser
import click
import requests

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

@project.command()
@click.option('--name', default='NewProject', help='Project name')
def create(name):
    """Create new project"""
    click.echo('Initalising project %s' % name)

@project.command()
@click.option('--name')
def status(name):
    r = requests.get(api_root + 'projects/' + name)
    click.echo(r.status_code)
    json = r.json()
    click.echo(json['name'])

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

@pallur_client.command()
@click.option('--username', prompt=True, help='username')
@click.password_option(confirmation_prompt=False)
def login(username, password):
    """Login to Pallur"""
    r = requests.post(api_root + 'login', json={'username': username, 'password': password})
    click.echo(r.status_code)
    if r.status_code == 401:
        click.echo("Login failed please try again")
    else:
        session_id = (r.json()['session_id'])
        file_location = expanduser("~")
        session_file = open(os.path.join(file_location, ".pallursession"),"w+")
        session_file.write(session_id)
        session_file.close

if __name__ == '__main__':
    pallur_client()
