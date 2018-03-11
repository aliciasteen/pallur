FROM python:2

ARG project_name
ARG application_file
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
#ADD resources/HelloWorld /HelloWorld/
COPY resources/HelloWorld/app.py /usr/local/bin/app.py
COPY resources/HelloWorld/requirements.txt /usr/local/bin/requirements.txt
RUN pip install -r /usr/local/bin/requirements.txt
EXPOSE 8000
#ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "$project_name"]
CMD ["python", "/usr/local/bin/app.py"]
