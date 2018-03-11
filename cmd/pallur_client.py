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

@user.command()
@click.option('--username', prompt=True, help='Login username')
@click.password_option()
def login(username, password, server_address):
    """login to project"""
    click.echo('login')

if __name__ == '__main__':
    pallur_client()
