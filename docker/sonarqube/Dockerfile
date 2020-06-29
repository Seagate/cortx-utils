FROM sonarqube:latest

USER root

# Add C++ community Plugin for C,C++ Analysis
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y wget
RUN wget -O /opt/sonarqube/extensions/plugins/sonar-cxx-plugin-1.3.2.1853.jar https://github.com/SonarOpenCommunity/sonar-cxx/releases/download/cxx-1.3.2/sonar-cxx-plugin-1.3.2.1853.jar 

USER sonarqube
