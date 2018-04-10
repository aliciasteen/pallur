FROM python:2.7

RUN mkdir /server
COPY pallur.py /server
COPY requirements.txt /server
COPY projectskeleton/ /server
WORKDIR /server
EXPOSE 5000
RUN apt-get update &&  apt-get install -y python-dev libldap2-dev libsasl2-dev libssl-dev
RUN pip install --upgrade pip &&  pip install -r /server/requirements.txt
ENTRYPOINT ["python"]
CMD ["pallur.py"]
