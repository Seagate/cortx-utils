#!/usr/bin/env groovy

pipeline { 
    agent {
        node {
            // Run deployment on mini_provisioner nodes (vm deployment nodes)
            label "mini_provisioner_ha && !cleanup_req && !cortx_deployed"
        }
    }
	
    parameters {
        string(name: 'CORTX_BUILD', defaultValue: 'http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.8.2003/last_successful_prod/', description: 'Build URL',  trim: true)
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: 'Keep Host for Debuging')   
    }

	environment {
        // Credentials used to SSH node
        NODE_DEFAULT_SSH_CRED = credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
        NODE_PASS = "${NODE_DEFAULT_SSH_CRED_PSW}"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    stages {

        // Clone deploymemt scripts from cortx-re repo
        stage ('Validate Deployment Environment ') {
            steps {
                script {

                    remote = getTestMachine("${NODE1_HOST}", "${NODE_USER}", "${NODE_PASS}")
                    
                    // Add badget to jenkins build
                    manager.addHtmlBadge("&emsp;<b>Build :</b> <a href=\"${CORTX_BUILD}\"><b>${build_id}</b></a> <br /> &emsp;<b>Deployment Host :</b><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'> ${NODE1_HOST}</a>&emsp;")

                    // Validate SSH Connection
                    sshCommand remote: remote, command: "exit"

                    // Validate Build URL
                    try { 
                        sh label: '', returnStatus: true, script: 'test 200 == $(curl -ksI ${CORTX_BUILD}/RELEASE.INFO|grep "HTTP/1.1" | cut -d " " -f 2)'
                        echo "Valid build URL. Check Successful!"
                    } catch (ex) {
                        error 'Please provide Valid Build URL'
                    }

                    // Validate SSH Connection
                    try { 
                        sshCommand remote: remote, command: "exit"
                        echo "Able to perform SSH. Check Successful!"
                    } catch (ex) {
                        error 'Please check the SSH credentials & Host status'
                    }

                    // Validate Storage 
                    try { 
                        sshCommand remote: remote, command: """
                            test 2 == \$(lsblk -d|grep -E 'sdb|sdc'|wc -l)
                        """
                        echo "The VM has exactly 2 nos. of attached disks. Check Successful!"
                    } catch (ex) {
                        error 'The VM should have exactly 2 attached disks. Kindly provide a VM with exactly 2 attached disks.'
                    }
                }
            }
        }

        stage('Prepare config.ini') {
            steps {
                
                sshCommand remote: remote, command: "wget -q https://raw.githubusercontent.com/Seagate/cortx-prvsnr/main/pillar/samples/config_vm.ini -O /root/config.ini"
                sshCommand remote: remote, command: "sed -i '/srvnode-2/,\$d; s/hostname=.*/hostname='$NODE1_HOST'/g; /roles=/d ; s/enclosure/storage/g' /root/config.ini"
                echo "Successfully created config.ini file!"
            }
        }

        stage("Install Provisioner API") {
            steps {
                sshCommand remote: remote, command: """
                    yum install -y yum-utils
                    yum-config-manager --add-repo "${CORTX_BUILD}/3rd_party/"
                    yum install --nogpgcheck -y python3 python36-m2crypto salt salt-master salt-minion
                    rm -rf /etc/yum.repos.d/*3rd_party*.repo
                    yum-config-manager --add-repo "${CORTX_BUILD}/cortx_iso/"
                    yum install --nogpgcheck -y python36-cortx-prvsnr
                    rm -rf /etc/yum.repos.d/*cortx_iso*.repo
                    yum clean all
                    rm -rf /var/cache/yum/
                """
                echo "Successfully installed Provisioner API!"
            }
        }
            
        stage("Bootstrap Provisioner") {
            steps {
                sshCommand remote: remote, failOnError: false, command: """
                    sshpass -p ${NODE_PASS} provisioner setup_provisioner srvnode-1:${NODE1_HOST} \
                    --logfile --logfile-filename /var/log/seagate/provisioner/setup.log --source rpm --config-path ~/config.ini \
                    --dist-type bundle --target-build ${CORTX_BUILD}

                    provisioner configure_setup ./config.ini 1
                    
                    provisioner pillar_export
                """
                echo "Successfully bootstrapped provisioner!"
            }
        }
        
        stage("Validate Bootstrap Provisioner") {
            steps {
                sleep(5)
                sshCommand remote: remote, failOnError: false, command: """
                    salt '*' test.ping  
                    salt "*" service.stop puppet
                    salt "*" service.disable puppet
                    salt '*' pillar.get release  
                    salt '*' grains.get node_id  
                    salt '*' grains.get cluster_id  
                    salt '*' grains.get roles
                """
                echo "Successfully validated bootstrap!"
            }
        }
        
        stage("Platform Setup") {
            steps {
                sleep(10)
                sshCommand remote: remote, failOnError: false, command: "provisioner deploy_vm --setup-type single --states system"
                echo "Successfully deployed system states!"
            }
        }
        
        stage("3rd Party Software Deployment") {
            steps {
                sleep(10)
                sshCommand remote: remote, command: "provisioner deploy_vm --setup-type single --states prereq", failOnError: false
               
                // sh label: 'ssh', returnStdout: true, script: """
                //     sshpass -p '${NODE_PASS}' ssh ${NODE_USER}@${NODE1_HOST} "provisioner deploy_vm --states prereq --setup-type single"
                // """
                echo "Successfully deployed prereq states!"


            }
        }
        
        stage("Data Path States Deployment") {
            steps {
                sleep(10)
                sshCommand remote: remote, failOnError: true, command: "provisioner deploy_vm --setup-type single --states iopath"
                echo "Successfully deployed iopath states!"
            }
        }
        
        stage("Control Stack States Deployment") {
            steps {
                sleep(10)
                sshCommand remote: remote, failOnError: true, command: "provisioner deploy_vm --setup-type single --states controlpath"
                echo "Successfully deployed controlpath states!"
            }
        }

        stage("Validate Deployment") {
            steps {
                sshCommand remote: remote, failOnError: true, command: "hctl status"
                echo "Validation success !!"
            }
        }
    }

    post { 
        always {
            script {

                // sshGet remote: remote, from: '/opt/seagate/cortx_configs/provisioner_cluster.json', into: 'archives/provisioner_cluster.json', override: true
                // sshGet remote: remote, from: '/var/log/seagate/provisioner/setup.log', into: 'archives/setup.log', override: true
                sshGet remote: remote, from: '/root/config.ini', into: 'archives/config.ini', override: true
                archiveArtifacts artifacts: 'archives/config.ini', followSymlinks: false, onlyIfSuccessful: false, allowEmptyArchive: true                       
                cleanWs()
            }
        }
        success {
            addNodeLabel("cortx_deployed")
        }
        failure {
            
            addNodeLabel("cleanup_req")

            build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]
        }
         aborted {
            addNodeLabel("cleanup_req")

            build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]
        }
    }
}	

// Method returns VM Host Information ( host, ssh cred)
def getTestMachine(host, user, pass) {

    def remote = [:]
    remote.name = 'cortx'
    remote.host = host
    remote.user =  user
    remote.password = pass
    remote.allowAnyHosts = true
    remote.fileTransfer = 'scp'
    return remote
}

// Mark node for cleanup (cleanup job will use this node label to identify cleanup node)
def addNodeLabel(nodeLabel) {
    node = getCurrentNode(env.NODE_NAME)
	node.setLabelString(node.getLabelString()+" "+nodeLabel)
	node.save()
    node = null
}

def getCurrentNode(nodeName) {
  for (node in Jenkins.instance.nodes) {
      if (node.getNodeName() == nodeName) {
        echo "Found node for $nodeName"
        return node
    }
  }
  throw new Exception("No node for $nodeName")
}