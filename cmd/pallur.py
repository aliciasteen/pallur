import click
import ldap
from flask import Flask, request, Response, abort
import jsonpickle
import json
import docker
import git
import os
import shutil
from subprocess import call
import subprocess
from string import Template
from .project import Project

app = Flask(__name__)
pallur_home = "/root/pallur"

# API routes

@app.route('/api')
def hello_world():
    return 'Hello world!'

@app.route('/api/users', methods=['POST'])
def api_users():
    api_check_active_session()
    return 'Users'

@app.route('/api/<username>')
def api_delete_user(username):
    api_check_active_session()
    return 'Deleted user: %s' % username

@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    api_check_active_session()
    if request.method == 'GET':
        return 'Projects'
    if request.method == 'POST':
        json = request.get_json(force=True)
        add_update_project_configuration(json)
        project_name = json['project']['name']
        create_project_image(project_name)
        return 'Project created'

@app.route('/api/projects/<project_name>')
def api_project(project_name):
    api_check_active_session()
    return get_project_configuration(project_name)
    #return jsonpickle.encode(Project(project_name, 'active'))

@app.route('/api/projects/<project_name>/config')
def api_project_config(project_name):
    api_check_active_session()
    return 'Project config: %s' % project_name

@app.route('/api/projects/<project_name>/code')
def api_project_code(project_name):
    api_check_active_session()
    return 'Project code: %s' % project_name

@app.route('/api/projects/<project_name>/up')
def api_project_up(project_name):
    api_check_active_session()
    return 'Project up: %s' % project_name

@app.route('/api/projects/<project_name>/down')
def api_project_down(project_name):
    api_check_active_session()
    return 'Project down: %s' % project_name

@app.route('/api/login', methods=['POST'])
def api_login():
    #click.echo("JSON Message: " + json.dumps(request.json))
    json = request.json
    check_credentials(json['username'], json['password'])
    session_id = create_session(json['username'])
    return Response(jsonpickle.encode({'session_id': session_id}), status=200, mimetype='application/json')

@app.route('/api/sessiontest')
def api_session_test():
    api_check_active_session()
    return "Active session"

# Methods

def api_check_active_session():
    session_id = request.headers['session_id']
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
        click.echo('exec_run_result: %s' % exec_run_result[1])
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
        if "remaining(-1s)" in exec_run_result[1]:
            click.echo("Session %s does not exist or is expired" % session_id)
            return -1
        else:
            return 1
    except Exception as e:
        click.echo(e)

def add_update_project_configuration(json):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        project_name = json['project']['name']
        container.exec_run("etcdctl put /%s %s" % (project_name, json['project']['description']))
        for section in json:
            for key in json[section]:
                value = json[section][key]
                container.exec_run("etcdctl put /%s/%s/%s %s" % (project_name, section, key, value))
        container.exec_run("etcdctl put /%s/active false" % project_name)
    except Exception as e:
        click.echo(e)

def etcd_set(project_name, key, value):
    client = docker.from_env()
    container = client.containers.get('etcd')
    try:
        container.exec_run("etcdctl put /%s/%s %s" % (project_name, key, value))[1].replace("\n", "")
    except Exception as e:
        click.echo(e)

def etcd_get(project_name, key):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        etcd_result = container.exec_run("etcdctl get /%s/%s -w=simple --print-value-only" % (project_name, key))
        return etcd_result[1].replace("\n", "")
    except Exception as e:
        click.echo(e)

def get_project_configuration(project_name):
    try:
        data = {}
        client = docker.from_env()
        container = client.containers.get('etcd')
        data["Name"] = project_name
        data["Description"] = container.exec_run("etcdctl get /%s/project/description -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Source URL"] = container.exec_run("etcdctl get /%s/source/url -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Branch"] = container.exec_run("etcdctl get /%s/source/branch -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Commit ID"] = container.exec_run("etcdctl get /%s/source/commit -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        data["Deployed"] = container.exec_run("etcdctl get /%s/active -w=simple --print-value-only" % project_name)[1].replace("\n", "")
        return json.dumps(data)
    except Exception as e:
        click.echo(e)

def create_project_image(project_name):
    # Clone repository   
    path = '/project-data/%s/resources' % project_name
    if not os.path.exists(path):
        os.makedirs(path)
    else:
        shutil.rmtree(path)
        os.makedirs(path)
    client = docker.from_env()
    container = client.containers.get('etcd')
    source_url = container.exec_run("etcdctl get /%s/source/url -w=simple --print-value-only" % project_name)[1].replace("\n", "")
    source_branch = container.exec_run("etcdctl get /%s/source/branch -w=simple --print-value-only" % project_name)[1].replace("\n", "")
    repo = git.Repo.clone_from(source_url, path, branch=source_branch)
    etcd_set(project_name, "source/commit", repo.head.object.hexsha)

    # Create docker file
    dockerfile = open(os.path.join(pallur_home, "projectskeleton/Dockerfile.template"),"r")
    src = Template(dockerfile.read())
    dockerfile.close()
    # # Substitute values
    python_version = etcd_get(project_name, "project/python_version")
    port = etcd_get(project_name, "configuration/port")
    main_file = etcd_get(project_name, "configuration/file")
    d = {'python_version':python_version, 'port':8000, 'main_file':'app.py', 'project_name':project_name}
    result = src.substitute(d)
    click.echo("Changed file: ")
    click.echo(result)

    # Save temp dockerfile
    try:
        temp_dockerfile = open("/project-data/%s/Dockerfile" % project_name, 'w')
        temp_dockerfile.write(result)
        temp_dockerfile.close()
    except Exception as e:
        click.echo(e)
        return

    # Build docker image
    click.echo("Building docker image")
    #docker_image = client.images.build(path='/project-data/test', tag='test:0.0.1', rm='true')[0]
    #click.echo(docker_image.tags)



    # Create docker-compose file
    dockercompose = open(os.path.join(pallur_home, "projectskeleton/docker-compose.yml"),"r")
    src = Template(dockercompose.read())
    dockercompose.close()
    # # Substitute values
    d = {'image':'test', 'tag':'0.0.1', 'port':8000, 'project_name':project_name}
    result = src.substitute(d)
 
    # Save temp docker-compose file
    try:
        temp_dockercompose = open("/project-data/%s/docker-compose.yml" % project_name, 'w')
        temp_dockercompose.write(result)
        temp_dockercompose.close()
    except Exception as e:
        click.echo(e)
        return

    # Deploys docker-compose
    compose_file = "/project-data/%s/docker-compose.yml" % project_name
    #docker_tag = docker_image.tags[0]
    docker_tag = 'test:0.0.1'
    environment = "project_name=%s image=%s port=8000" % (project_name, docker_tag)
    #click.echo("Environment: %s    Compose File: %s" % (environment, compose_file))
    try:
        #call([environment, 'docker-compose', '-f', compose_file, '-p', project_name, 'up', '-d'])
        output = call(['docker-compose', '-f', compose_file, 'up', '-d'])
        click.echo(output)
        #call(['docker-compose', '-f', '/root/pallur/projectskeleton/docker-compose.yml', '-p', 'test', 'up', '-d'])
    except Exception as e:
        click.echo(e)
    shutil.rmtree(path)