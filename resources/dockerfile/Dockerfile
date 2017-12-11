FROM python:2

ARG project_name
ARG application_file
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
EXPOSE 80
ENTRYPOINT ["/usr/local/bin/entrypoint.sh", "$project_name"]
