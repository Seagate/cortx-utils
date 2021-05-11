#!/usr/bin/env groovy
pipeline { 
    agent {
        
        node {
            // This job runs on vm deployment controller node to execute vm cleanup for the deployment configured host
            label params.HOST.isEmpty() ? "${NODE_LABEL} && cleanup_req" : "vm_deployment_1n_user_host"
        }
    }
	
    // Accept node label as parameter
    parameters {
        string(name: 'NODE_LABEL', description: 'Optional : Node Label',  trim: true)
        string(name: 'HOST', description: 'Host FQDN',  trim: true)
        password(name: 'HOST_PASS', description: 'Host machine root user password')
    }

	environment {
        // NODE1_HOST - Env variables added in the node configurations

        // Credentials used to SSH node
        NODE_DEFAULT_SSH_CRED = credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
        NODE_PASS = "${params.HOST.isEmpty() ? NODE_DEFAULT_SSH_CRED_PSW : HOST_PASS}"
        NODE1_HOST = "${params.HOST.isEmpty() ? NODE1_HOST : HOST }"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    
    stages {
        stage ('Checkout Scripts') {
            steps {
                script {
                    
                    // Add badget to jenkins build
                    manager.addHtmlBadge("&emsp;<b>Host :</b><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'> ${env.NODE_NAME}</a>")

                    // Clone cortx-re repo
                    dir('cortx-re') {
                        checkout([$class: 'GitSCM', branches: [[name: '*/mini-provisioner-dev']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re.git']]])                
                    }

                }
            }
        }
        stage('Cleanup Node') {
            steps {
                script {
                    dir("cortx-re/scripts/mini_provisioner") {
                        ansiblePlaybook(
                            playbook: 'host_cleanup.yml',
                            inventory: 'inventories/hosts',
                            tags: '00_PREP_ENV,01_CLEANUP',
                            extraVars: [
                                "NODE1"                 : [value: "${NODE1_HOST}", hidden: false],
                                "CLUSTER_PASS"          : [value: "${NODE_PASS}", hidden: false]
                            ],
                            extras: '-v',
                            colorized: true
                        )
                    }                        
                }
            }
        }
    }

    post {
        failure {
            script {
                if ( params.HOST.isEmpty() ) {
                    markNodeOffline("VM Cleanup Failure - Automated offline")
                }    
            }
        }    
        success {
            script {
                // remove cleanup label from the node
                removeCleanupLabel()
            }
        }
    }
}	


// Method returns VM Host Information ( host, ssh cred )
def getTestMachine(host, user, pass) {

    def remote = [:]
    remote.name = 'cortx'
    remote.host = host
    remote.user =  user
    remote.password = pass
    remote.allowAnyHosts = true
    return remote
}

// Make failed node offline
def markNodeOffline(message) {
    node = getCurrentNode(env.NODE_NAME)
    computer = node.toComputer()
    computer.setTemporarilyOffline(true)
    computer.doChangeOfflineCause(message)
    computer = null
    node = null
}

def removeCleanupLabel() {
	nodeLabel = "cleanup_req"
    node = getCurrentNode(env.NODE_NAME)
	node.setLabelString(node.getLabelString().replaceAll(nodeLabel, ""))
    echo "[ ${env.NODE_NAME} ] : Cleanup label removed. The current node labels are ( ${node.getLabelString()} )"
	node.save()
    node = null
    
}

// Get running node instance
def getCurrentNode(nodeName) {
  for (node in Jenkins.instance.nodes) {
      if (node.getNodeName() == nodeName) {
        echo "Found node for $nodeName"
        return node
    }
  }
  throw new Exception("No node for $nodeName")
}

