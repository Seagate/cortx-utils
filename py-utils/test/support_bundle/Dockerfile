FROM centos:7.9.2009

RUN yum install -y python3

RUN mkdir -p /app /var/cortx/support_bundle/data

COPY support_bundle.py /app/

ENTRYPOINT ["python3", "/app/support_bundle.py"]
