# Docker installation script for centos-7 

# Cleanup Exsiting docker related tools
yum remove docker \
            docker-client \
            docker-client-latest \
            docker-common \
            docker-latest  \
            docker-latest-logrotate \
            docker-logrotate \
            docker-engine

# Install Docker
yum install -y yum-utils
yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
yum install -y docker-ce docker-ce-cli containerd.io

# Install Docker compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.25.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
 
# Enable and start docker
systemctl start docker
systemctl enable docker 
