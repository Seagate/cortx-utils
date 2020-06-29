# What is SonarQube?

[SonarQube](https://www.sonarqube.org/) is an open source product for continuous inspection of code quality.

![logo](https://raw.githubusercontent.com/docker-library/docs/84479f149eb7d748d5dc057665eb96f923e60dc1/sonarqube/logo.png)


## Docker Host Requirements

On Linux, you can set the recommended values for the current session by running the following commands as root on the host:

1. Add the below line in `/etc/sysctl.conf`
```console
vm.max_map_count=262144
fs.file-max=65536
```
2. Add the below line in `/etc/security/limits.conf` to increase ulimit
```console
ulimit -n 65536
ulimit -u 4096
```


## How to Use

/!\ This section shows you how to quickly run a demo instance. When you are ready to move to a more sustainable setup, take some time to read the **Configuration** section below.

Start the server by running:
```console
$ docker-compose up
```

By default you can login as `admin` with password `admin`, see [authentication documentation](https://docs.sonarqube.org/latest/instance-administration/security/).


## Configuration

### Volumes:

The official docker images for sonarqube contain the SonarQube installation folders at `/opt/sonarqube`. so we are doing the volume mapping to those folder to make it production ready setup :

-	`/opt/sonarqube/conf`: configuration files, such as `sonar.properties`
-	`/opt/sonarqube/data`: data files, such as the embedded H2 database and Elasticsearch indexes
-	`/opt/sonarqube/logs`: contains SonarQube logs about access, web process, CE process, Elasticsearch logs
-	`/opt/sonarqube/extensions`: plugins, such as language analyzers

## Current setup

***Sonarqube Server Host*** : `eos-demo-0183.mero.colo.seagate.com`  
***Docker mount path*** : `/home/eosjenkins/docker-mounts/dev/eos-demo-0183/`  
***Volumes Used*** : 
- sonarqube_conf:
- sonarqube_data:
- postgresql:
- postgresql_data:
 
***Sonarqube image:***
       - For c, c++ support sonar-cxx plugin is installed on top of default sonarqube docker image and custom docker image created with this change.
     
*Custom Image Creation Steps*    
        
    Refer Dockerfile
 
    Ref : https://github.com/SonarOpenCommunity/sonar-cxx/wiki/Installation-into-Docker-Sonarqube-Image
        

## Administration

The administration guide can be found [here](https://redirect.sonarsource.com/doc/administration-guide.html).


 