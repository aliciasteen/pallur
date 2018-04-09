import click
import ldap
import ldap.modlist
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

ldap_admin_user = "cn=admin,dc=pallur,dc=cloud"
ldap_admin_pass = "admin"
ldap_server="ldap://0.0.0.0:389"

# ----------------------------------------------------------
# Flask API routes
# ----------------------------------------------------------

@app.route('/api')
def hello_world():
    return 'Pallur'

# ----------------------------------------------------------
# Users
# ----------------------------------------------------------

@app.route('/api/users', methods=['POST'])
def api_users():
    api_check_active_session()
    return 'Users'

# Add user to LDAP
@app.route('/api/<username>', methods=['POST'])
def api_add_user(username):
    json = request.get_json(force=True)
    return ldap_add_user(json['username'], json['password'])
    
@app.route('/api/<username>/delete', methods=['POST'])
def api_delete_user(username):
    json = request.get_json(force=True)
    return ldap_delete_user(json['username'], json['password'])

@app.route('/api/<username>/groups')
def api_user_groups(username):
    api_check_active_session()
    return check_group(request.headers['session_id'], 'not')

@app.route('/api/<username>/group', methods=['POST'])
def api_add_user_to_group(username):
    json = request.get_json(force=True)
    click.echo("api_add_user_to_group")
    return ldap_add_user_to_group(username, json['project_name'])

# ----------------------------------------------------------
# Projects
# ----------------------------------------------------------

@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    api_check_active_session()
    if request.method == 'GET':
        return 'Projects'
    if request.method == 'POST':
        json = request.get_json(force=True)
        add_update_project_configuration(json)
        project_name = json['project']['name']
        create_project(project_name)
        return 'Project created'

@app.route('/api/projects/<project_name>')
def api_project(project_name):
    api_check_active_session()
    return get_project_configuration(project_name)

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



@app.route('/api/sessiontest')
def api_session_test():
    api_check_active_session()
    return "Active session"

# ----------------------------------------------------------
# Login
# ----------------------------------------------------------
@app.route('/api/login', methods=['POST'])
def api_login():
    #click.echo("JSON Message: " + json.dumps(request.json))
    json = request.json
    check_credentials(json['username'], json['password'])
    session_id = create_session(json['username'])
    return Response(jsonpickle.encode({'session_id': session_id}), status=200, mimetype='application/json')

# ----------------------------------------------------------
# ----------------------------------------------------------
# Methods
# ----------------------------------------------------------

# ----------------------------------------------------------
# User authenitcation methods
# ----------------------------------------------------------

# ----------------------------------------------------------
# Sessions
def create_session(username):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        exec_run_result = container.exec_run("etcdctl lease grant 3600")
        click.echo('exec_run_result: %s' % exec_run_result[1])
        lease_id = exec_run_result[1].split()[1]
        click.echo(lease_id)
        container.exec_run("etcdctl put --lease=%s %s %s" % (lease_id, lease_id, username))
        return lease_id
    except Exception as e:
        bad_request(e)

def api_check_active_session():
    try:
        session_id = request.headers['session_id']
        if check_active_session(session_id) != 1:
            abort(401)
    except Exception as e:
        bad_request(e)
    

def check_active_session(session_id):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        exec_run_result = container.exec_run("etcdctl lease timetolive --keys %s" % session_id)
        if "remaining(-1s)" in exec_run_result[1]:
            bad_request("Session %s does not exist or is expired" % session_id)
        else:
            return 1
    except Exception as e:
        bad_request(e)

def get_username_from_session(session_id):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        username = container.exec_run("etcdctl get %s -w=simple --print-value-only" % session_id)[1].replace("\n", "")
        return username
    except Exception as e:
        bad_request(e)

# ----------------------------------------------------------
# LDAP

# Check login to ldap
def check_credentials(username, password):
    l = ldap.initialize(ldap_server)
    username = "cn=%s,ou=users,dc=pallur,dc=cloud" % username
    try:
      l.simple_bind_s(username, password)
      return "Login successful"
    except ldap.INVALID_CREDENTIALS:
        abort(401, {'message': "Incorrect Password"})
    except ldap.LDAPError as e:
        bad_request('LDAP  Error {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))
    except Exception as e:
        bad_request(e)

# Check user is in group
def check_group(session_id, project_name):
    l = ldap.initialize(ldap_server)
    l.simple_bind_s(ldap_admin_user, ldap_admin_pass)
    username = get_username_from_session(session_id)
    search_filter = "(&(objectClass=posixGroup)(cn=%s)(memberUid=%s))" % (project_name, username)
    
    try:
        results = l.search_s("dc=pallur,dc=cloud", ldap.SCOPE_SUBTREE, search_filter, ['memberUid'])
        if results:
            return "In group"
        else:
            return "Not in group"
        return str(results)
    except ldap.LDAPError as e:
        return ('LDAP  Error {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))
    except Exception as e:
        bad_request(e)

# Gets maximum UID number from LDAP
def ldap_max_uid():
    l = ldap.initialize(ldap_server)
    l.simple_bind_s(ldap_admin_user, ldap_admin_pass)
    search_filter = "(&(objectClass=posixAccount))"
    try:
        results = l.search_s("dc=pallur,dc=cloud", ldap.SCOPE_SUBTREE, search_filter, ['uidNumber'])
        return max(x[1]['uidNumber'][0] for x in results)
    except ldap.LDAPError as e:
        return ('LDAP  Error {0}'.format(e.message['desc'] if 'desc' in e.message else str(e)))
    except Exception as e:
        return 1000

# Add ldap group
def ldap_add_group(project_name):
    l = ldap.initialize(ldap_server)
    l.simple_bind_s(ldap_admin_user, ldap_admin_pass)
    dn = "cn=%s,ou=groups,dc=pallur,dc=cloud" % project_name
    modlist = {
           "objectClass": ["inetOrgPerson", "posixAccount", "shadowAccount"],
           "cn": ["Maarten De Paepe"],
           "displayName": ["Maarten De Paepe"],
           "uidNumber": ["5000"],
           "gidNumber": ["10000"]
          }
    l.add(dn, modlist)

# Add ldap user
def ldap_add_user(username, password):
    l = ldap.initialize(ldap_server)
    click.echo("GETS HERE")
    l.simple_bind_s(ldap_admin_user, ldap_admin_pass)
    dn = 'cn=%s,ou=users,dc=pallur,dc=cloud' % username
    username = str (username)
    password = str (password)
    uid = str ((int (ldap_max_uid())) + 1)
    modlist = {
        "objectClass": ["inetOrgPerson", "posixAccount", "top"],
        "sn": [username],
        "cn": [username],
        "uid": [username],
        "uidNumber": [uid],
        "userpassword": [password],
        "gidNumber": ["500"],
        "homeDirectory": ["/home/%s" % username]
        }
    try:
        result = l.add_s(dn, ldap.modlist.addModlist(modlist))
    except ldap.ALREADY_EXISTS as e:
        return bad_request('User already exists')
    except Exception as e:
        bad_request(e)
    return "User %s created" % username

# Add ldap user to group
def ldap_add_user_to_group(username, project_name):
    l = ldap.initialize(ldap_server)
    l.simple_bind_s(ldap_admin_user, ldap_admin_pass)
    dn = "cn=%s,ou=group,dc=pallur,dc=cloud" % project_name
    #modlist = {
    #       "objectClass": ["posixGroup", "top"],
    #       "cn": [project_name],
    #       "memberUid": [username]
    #      }
    modlist = [
        (ldap.MOD_ADD, 'objectClass', ["posixGroup", "top"]),
        (ldap.MOD_ADD, 'cn', project_name),
        (ldap.MOD_ADD, 'memberUid', username)
        ]
    try:
        return l.modify_s(dn, ldap.modlist.addModlist(modlist))
    except Exception as e:
        bad_request(e)
    

# Delete user from LDAP
def ldap_delete_user(username, password):
    #check_credentials(username, password)
    l = ldap.initialize(ldap_server)
    l.simple_bind_s(ldap_admin_user, ldap_admin_pass)
    dn = "cn=%s,ou=users,dc=pallur,dc=cloud" % username
    try:
        l.delete_s(dn)
    except ldap.NO_SUCH_OBJECT as e:
        bad_request("User does not exist")
    return 'Deleted user: %s' % username


# ----------------------------------------------------------
# Project methods
# ----------------------------------------------------------

# ----------------------------------------------------------
# ETCD methods

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
        bad_request(e)

def etcd_set(project_name, key, value):
    client = docker.from_env()
    container = client.containers.get('etcd')
    try:
        container.exec_run("etcdctl put /%s/%s %s" % (project_name, key, value))[1].replace("\n", "")
    except Exception as e:
        bad_request(e)

def etcd_get(project_name, key):
    try:
        client = docker.from_env()
        container = client.containers.get('etcd')
        etcd_result = container.exec_run("etcdctl get /%s/%s -w=simple --print-value-only" % (project_name, key))
        return etcd_result[1].replace("\n", "")
    except Exception as e:
        bad_request(e)

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
        bad_request(e)

# ----------------------------------------------------------
# Docker methods

def create_project(project_name):  
    build_docker_image(project_name)
    create_docker_compose(project_name)
    docker_network_create(project_name)
    if etcd_get(project_name, "database/name"):
        docker_db_deploy(project_name)
    docker_compose_up(project_name)  

def build_docker_image(project_name):
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
    network = etcd_get(project_name, "network")
    d = {'python_version':python_version, 'port':port, 'main_file':main_file, 'project_name':project_name, 'network': network}
    substitute_dockerfile = src.substitute(d)

    # Save temp dockerfile
    try:
        temp_dockerfile = open("/project-data/%s/Dockerfile" % project_name, 'w')
        temp_dockerfile.write(substitute_dockerfile)
        temp_dockerfile.close()
    except Exception as e:
        bad_request(e)

    # Build docker image
    # Should use commit ID as tag

    click.echo("Building docker image")
    path="/project-data/%s" % project_name
    tag="%s:0.0.1" % project_name
    docker_image = client.images.build(path=path, tag=tag, rm='true')[0]
    etcd_set(project_name, "image_tag", docker_image.tags.split(':')[1])

    # Delete cloned repo
    shutil.rmtree(path)

def docker_network_create(project_name):
    client = docker.from_env()
    network = client.networks.create(project_name)
    etcd_set(project_name, "network", network.id)

# Start project
def docker_compose_up(project_name):
    # Deploys docker-compose
    compose_file = "/project-data/%s/docker-compose.yml" % project_name
    try:
        click.echo(call(['docker-compose', '-f', compose_file, 'up', '-d']))
    except Exception as e:
        bad_request(e)
    
# Stop project
def docker_compose_down(project_name):
    # Deploys docker-compose
    compose_file = "/project-data/%s/docker-compose.yml" % project_name
    try:
        click.echo(call(['docker-compose', '-f', compose_file, 'down']))
    except Exception as e:
        bad_request(e)


# Create docker compose file
def create_docker_compose(project_name):
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
        bad_request(e)

def bad_request(message):
    abort(400, {'message': message})
    #return Response(jsonpickle.encode({'message': message}), status=400, mimetype='application/json')


# ----------------------------------------------------------
# Docker database
# MySQL
# mongo
# postgres

def docker_db_deploy(project_name):
    database_type = etcd_get(project_name, "database/type")
    database_version = etcd_get(project_name, "database/version")
    database_password = etcd_get(project_name, "database/password")
    docker_network = etcd_get(project_name, "network")

    database_tag = "%s:%s" % (database_type, database_version)
    container_name = "%s-db" % project_name

    client = docker.from_env()

    if (database_type == 'mysql'):
        environment = ['MYSQL_ROOT_PASSWORD=%s' % database_password]
    elif (database_type == 'mongodb'):
        environment = []
    elif (database_type == 'postgres'):
        environment = ['POSTGRES_PASSWORD=%s' % database_password]
    else:
        bad_request("Database type not supported")
    container = client.containers.run(
        database_tag, 
        name=container_name, 
        network=docker_network,
        environment=environment,  
        detach=True
    )

    etcd_set(project_name, "database/id", container.id)
    etcd_set(project_name, "database/active", 'True')

def docker_db_remove(project_name):
    client = docker.from_env()
    database_id = etcd_get(project_name, "database/id")
    container = client.containers.get(database_id)
    try:
        container.stop()
        container.remove()
    except docker.errors.APIError as e:
        bad_request("Docker error: %s" % e)
    etcd_set(project_name, "database/active", 'False')