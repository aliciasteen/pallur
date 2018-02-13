import click
import ldap

@click.group()
def pallur():
    "PaaS for python"
    pass

@pallur.group()
def project():
    """Interact with, create and destroy projects"""
    pass

@pallur.group()
def user():
    """User login, logout, management and deletion"""
    pass

@project.command()
@click.option('--name', default='NewProject', help='Project name')
def create(name):
    """Create new project"""
    click.echo('Initalising project %s' % name)

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

@user.command()
@click.option('--username', prompt=True, help='Login username')
@click.password_option()
def login(username, password):
    """login to project"""
    click.echo(check_credentials(username, password))

def check_credentials(username, password):
    ldap_server="ldap://0.0.0.0:389"
    l = ldap.initialize(ldap_server)
    username = "cn=%s,ou=users,dc=pallur,dc=cloud" % username
    password = password
    try:
      l.simple_bind_s(username, password)
      valid = True
      return 1
    except ldap.INVALID_CREDENTIALS:
        click.echo("Incorrect Password")
        return 0
    except ldap.LDAPError as e:
        click.echo('LDAP Error {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))
    except Exception as e:
        click.echo(e)
        return 0
