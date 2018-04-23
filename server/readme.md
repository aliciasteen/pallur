# Server

## setup.py
This file is used to install the Pallur client. It uses the setuptool python program.
More information can be found here: http://click.pocoo.org/6/setuptools/

## pallur.py
This file is the Pallur server. It uses Flask to receive user requests and executes commands to manage projects. 

## Dockerfile
This Dockerfile builds the docker image for pallur.py

## requirements.txt
This file contains a list of pip libraies to install when building the Pallur Docker image
