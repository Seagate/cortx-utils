FROM centos:8.4.2105

# created a new directory inside home directory
RUN mkdir -p /home/cortx


# defining working directory for use
WORKDIR /home/cortx

# installing git
RUN yum install -y git

# using kubernetes branch to clone cortx-py-utils
RUN git clone --recursive https://github.com/Seagate/cortx-utils -b kubernetes

# installing required python dependencies
RUN yum install -y gcc rpm-build python36 python36-pip python36-devel python36-setuptools openssl-devel libffi-devel python36-dbus

# changing work directory to use
WORKDIR /home/cortx/cortx-utils

# build the rpm
RUN bash jenkins/build.sh -v 1.0.0 -b 2

# installing requirement files
RUN pip3 install -r py-utils/python_requirements.txt
RUN pip3 install -r py-utils/python_requirements.ext.txt

#installing cortx-py-utils rpm
RUN yum install -y  py-utils/dist/cortx-py-utils-*.noarch.rpm

ENTRYPOINT ["tail"]

CMD ["-f","/dev/null"]


