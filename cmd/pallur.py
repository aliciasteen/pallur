import click
import ldap
from flask import Flask, request, Response, abort
import jsonpickle
import json
import docker
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
    return 'Deleted user: %s' % username

@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    if request.method == 'GET':

        return 'Projects'
    if request.method == 'POST':
        click.echo("TEST")
        json = request.get_json(force=True)
        click.echo(json['project'])
        add_update_project_configuration(json)
        return 'Project created'

@app.route('/api/projects/<project_name>')
def api_project(project_name):
    api_check_active_session()
    return get_project_configuration(project_name)
    #return jsonpickle.encode(Project(project_name, 'active'))

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
    #click.echo("JSON Message: " + json.dumps(request.json))
    json = request.json
    click.echo(json)
    click.echo("JSON username: " + json['username'])
    click.echo("JSON password: " + json['password'])
    check_credentials(json['username'], json['password'])
    session_id = create_session(json['username'])
    return Response(jsonpickle.encode({'session_id': session_id}), status=200, mimetype='application/json')

@app.route('/api/sessiontest')
def api_session_test():
    api_check_active_session()
    return "Active session"

def api_check_active_session():
    session_id = request.headers['session_id']
    click.echo(session_id)
    if check_active_session(session_id) != 1:
        abort(401)

def check_credentials(username, password):
    ldap_server="ldap://0.0.0.0:389"
    l = ldap.initialize(ldap_server)
    username = "cn=%s,ou=users,dc=pallur,dc=cloud" % username
    try:
      l.simple_bind_s(username, password)
      valid = True
      return "Login successful"
    except ldap.INVALID_CREDENTIALS:
        click.echo("Incorrect Password")
        abort(401)
    except ldap.LDAPError as e:
        click.echo('LDAP  Error {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))
    except Exception as e:
        click.echo(e)
        return "error"

def create_session(username):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        exec_run_result = container.exec_run("etcdctl lease grant 3600")
        lease_id = exec_run_result[1].split()[1]
        click.echo(lease_id)
        container.exec_run("etcdctl put --lease=%s test %s" % (lease_id, username))
        return lease_id
    except Exception as e:
        click.echo(e)

def check_active_session(session_id):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        exec_run_result = container.exec_run("etcdctl lease timetolive --keys %s" % session_id)
        click.echo(exec_run_result[1])
        if "remaining(-1s)" in exec_run_result[1]:
            click.echo("Session does not exist or is expired")
            return -1
        else:
            click.echo("Session is valid")
            return 1
    except Exception as e:
        click.echo(e)

def add_update_project_configuration(json):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        project_name = json['project']['name']
        exec_run_result = container.exec_run("etcdctl put /%s %s" % (project_name, json['project']['description']))
        for section in json:
            for key in json[section]:
                value = json[section][key]
                container.exec_run("etcdctl put /%s/%s/%s %s" % (project_name, section, key, value))
        container.exec_run("etcdctl put /%s/active false" % project_name)
    except:
        pass

def get_project_configuration(project_name):
    try:
        data = {}
        client = docker.from_env()
        container = client.containers.get('etcd')
        data["Name"] = project_name
        # data["Description"] = container.exec_run("etcdctl get /%s/project/description" % project_name)[1]
        # data["Source"] = container.exec_run("etcdctl get /%s/source/url" % project_name)[1]
        # data["Branch"] = container.exec_run("etcdctl get /%s/source/branch" % project_name)[1]
        # data["Commit ID"] = container.exec_run("etcdctl get /%s/source/commit" % project_name)[1]
        # data["Deployed"] = container.exec_run("etcdctl get /%s/active" % project_name)[1]
        data["Description"] = container.exec_run("etcdctl get /%s/project/description -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Source URL"] = container.exec_run("etcdctl get /%s/source/url -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Branch"] = container.exec_run("etcdctl get /%s/source/branch -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Commit ID"] = container.exec_run("etcdctl get /%s/source/commit -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Deployed"] = container.exec_run("etcdctl get /%s/active -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        return json.dumps(data)
    except:
        pass