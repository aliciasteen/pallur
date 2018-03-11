import click
import ldap
from flask import Flask, request
import jsonpickle
from .project import Project

app = Flask(__name__)

@app.route('/api')
def hello_world():
    return 'Hello world!'

@app.route('/api/users', methods=['POST'])
def api_users():
    return 'Users'

@app.route('/api/<username>')
def api_delete_user(username):
    return 'Delted user: %s' % username

@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    if request.method == 'GET':
        return 'Projects'
    if request.method == 'POST':
        return 'Project create'

@app.route('/api/projects/<project_name>')
def api_project(project_name):
    return jsonpickle.encode(Project(project_name, 'active'))

@app.route('/api/projects/<project_name>/config')
def api_project_config(project_name):
    return 'Project config: %s' % project_name

@app.route('/api/projects/<project_name>/code')
def api_project_code(project_name):
    return 'Project code: %s' % project_name

@app.route('/api/projects/<project_name>/up')
def api_project_up(project_name):
    return 'Project up: %s' % project_name

@app.route('/api/projects/<project_name>/down')
def api_project_down(project_name):
    return 'Project down: %s' % project_name

@app.route('/api/login', methods=['POST'])
def api_login():
    error = None
    json = request.get_json()
    return check_credentials(json['username'], json['password'])

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

@project.command()
def list():
    """project list"""
    click.echo('project list')

@user.command()
@click.option('--username', prompt=True, help='Login username')
@click.password_option()
def login(username, password, server_address):
    """login to project"""

    click.echo(check_credentials(username, password))

def check_credentials(username, password):
    ldap_server="ldap://0.0.0.0:389"
    l = ldap.initialize(ldap_server)
    username = "cn=%s,ou=users,dc=pallur,dc=cloud" % username
    try:
      l.simple_bind_s(username, password)
      valid = True
      return 1
    except ldap.INVALID_CREDENTIALS:
        click.echo("Incorrect Password")
        return 0
    except ldap.LDAPError as e:
        click.echo('LDAP  Error {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))
    except Exception as e:
        click.echo(e)
        return 0

#def create_session():
    #client = docker.from_env()
    #client.exec_run(cmd(etcdctl lease grant 3600))
    #client.exec_run(cmd(etcdctl set ))
