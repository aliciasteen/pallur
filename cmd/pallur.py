import click

@click.group
def project():
    """Interact with, create and destroy projects"""

@project.command
@click.option('--name', default='NewProject', help='Project name')
def create(name):
    """Create new project"""
    click.echo('Initalising project %s' % name)

@project.command
@click.option('--name', default='NewProject', help='Project name')
def up(name):
    """Project up"""
    click.echo('project up %s' % name)

@project.command
def login():
    """login to project"""
    click.echo('Woo login')

@project.command
def delete():
    """Delete project"""
    click.echo('Deleted project')

@project.command
def down():
    """project down"""
    click.echo('project down')

@project.command
def update():
    """project update"""
    click.echo('project update')
