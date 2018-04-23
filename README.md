# Pallur
Pallur is a PaaS for python applications.

  - Docker based
  - Easy to use
  - Fast

# Client Installation

### Requirements:
  - Python 2.7 or 2.6 installed
  - Setuptools installed

### Installlation:
```sh
$ cd pallur/client
$ pip install .
$ pallur
```

### Commands

Client commands to interact with client

| Command | Subcommand | Description | Options | 
| ------ | ------ | ------ | ------ |
| Login | | Login to Pallur | Username, Password |
| Project | Create | Create new project | Project name, configuration file |
| | Delete | Delete project | Project name |
| | Down | Stop project | Project name |
| | List | List projects you have access to | Project name |
| | Logs | Get project logs | Project name |
| | Status | Get status of project | Project name |
| | Up | Deploy existing project | Project name |
| | Update | Update project | Project name |
| User | Create | Create user | Username, Password |
| | Delete | Delete user | Username, Password |
| | Project | Add user to project | User, Project name |

# Server Installation

### Requirements:
  - Docker
  - Docker-Compose

### Installlation:
```sh
$ cd pallur/server
$ docker network create proxy
$ export DOMAIN=<pallur domain name>
$ . resources/compose/configuration/traefik.sh
$ docker-compose -f resources/compose/docker-compose-setup.yaml up -d
```
