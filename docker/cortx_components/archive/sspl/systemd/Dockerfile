ARG  CENTOS_RELEASE

FROM 10.230.162.34:5000/centos_eos:${CENTOS_RELEASE}

COPY ./repos/*.repo /etc/yum.repos.d/

RUN yum install -y openssh-server java-1.8.0-openjdk make gcc cmake gcc-c++ rpm-build sudo python-Levenshtein libtool doxygen python-pep8 openssl-devel graphviz check-devel

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

