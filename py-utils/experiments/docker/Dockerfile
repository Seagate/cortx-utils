FROM centos:7.9.2009

RUN yum install -y git 

RUN git clone --recursive https://github.com/Seagate/cortx-utils -b kubernetes

RUN yum install -y gcc rpm-build python36 python36-pip python36-devel python36-setuptools openssl-devel libffi-devel python36-dbus

WORKDIR /cortx-utils

RUN bash jenkins/build.sh -v 1.0.0 -b 2

RUN pip3 install -r py-utils/python_requirements.txt

RUN pip3 install -r py-utils/python_requirements.ext.txt

RUN yum install -y  py-utils/dist/cortx-py-utils-*.noarch.rpm

ENTRYPOINT ["tail"] 

CMD ["-f","/dev/null"]
