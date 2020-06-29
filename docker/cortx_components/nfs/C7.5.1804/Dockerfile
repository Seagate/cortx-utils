FROM registry.gitlab.mero.colo.seagate.com/centos:eos
ARG USER_PASS

RUN rm -rf /etc/yum.repos.d/*.repo
COPY ./repos/*.repo /etc/yum.repos.d/

RUN yum install -y openssh-server java-1.8.0-openjdk make gcc
RUN mkdir /var/run/sshd
RUN echo  "${USER_PASS}" | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
RUN ssh-keygen -P "" -t rsa -f /etc/ssh/ssh_host_rsa_key
# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

