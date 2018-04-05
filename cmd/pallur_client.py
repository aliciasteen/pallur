import os
from os.path import expanduser, realpath
import click
import requests
import json
import click_spinner

api_root = 'http://server.pallur.cloud:5000/api/'

# ----------------------------------------------------------
# Click groups
# ----------------------------------------------------------

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

# ----------------------------------------------------------
# ----------------------------------------------------------
# Click Commands

# ----------------------------------------------------------
# Click user commands
# ----------------------------------------------------------

# Add user to ldap directory. No login needed
@user.command(name='create')
@click.option('--username', '-n', help='Username', prompt=True)
@click.password_option()
def create_user(username, password):
    """Create User"""
    r = requests.post(api_root + username, json={'username': username, 'password': password})
    check_status_code(r)
    click.echo(r.text)

# Delete user from ldap. User must login first.
# Cannot be deleted if group only has one member. Must delete group first
@user.command(name='delete')
@click.option('--username', '-n', help='Username', prompt=True)
@click.password_option(confirmation_prompt=False)
def delete_user(username, password):
    """Delete User"""
    headers = {'session_id': session_id()}
    url = api_root + username + "/delete"
    r = requests.post(url, headers=headers, json={'username': username, 'password': password})
    check_status_code(r)
    click.echo(r.text)

# Add user to ldap group. This allows users to access projects.
# Requires user with access to group to be logged in
@user.command(name='project')
@click.option('--name', help='Username', prompt=True)
@click.option('--project', help='Project to add user to', prompt=True)
def user_groups(name, project):
    """Add user to project"""
    headers = {'session_id': session_id()}
    url = api_root + name + '/group'
    r = requests.post(url, headers=headers, json={'project_name': project})
    check_status_code(r)
    click.echo(r.text)

# ----------------------------------------------------------
# Click project commands
# ----------------------------------------------------------

# Creates project
# - Adds group to LDAP
# - Saves configuration to LDAP
# - Deploys project
# - Returns project URL 
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
            check_status_code(r)
        except requests.exceptions.ConnectionError as e:
            click.echo("Connection error. Please wait and try again.")        
    
# Gets status of project. Returns:
# - Name
# - URL
# - If deployed
@project.command()
@click.option('--name', help='Project Name', prompt=True)
def status(name):
    headers = {'session_id': session_id()}
    url = api_root + 'projects/' + name
    r = requests.get(url, headers=headers)
    check_status_code(r)
    click.echo(json.dumps(r.json(), indent=4, separators=(',', ': ')))
    
# Deploys project from configuration saved
@project.command()
@click.option('--name', default='NewProject', help='Project name') 
def up(name):
    """Project up"""
    click.echo('project up %s' % name)

# Deletes project
# Removes all configuration, and ldap groups, remove project deployment
@project.command()
def delete():
    """Delete project"""
    headers = {'session_id': session_id()}
    click.echo('Deleted project')

# Stops project. Does not delete anything
@project.command()
def down():
    """project down"""
    headers = {'session_id': session_id()}
    click.echo('project down')

# Update project
# Can redeploy if needed
@project.command()
def update():
    """project update"""
    headers = {'session_id': session_id()}
    click.echo('project update')

# List projects user has access to
@project.command()
def list():
    """project list"""
    headers = {'session_id': session_id()}
    click.echo('project list')

# ----------------------------------------------------------
# Click login
# ----------------------------------------------------------

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
    pallur_client()