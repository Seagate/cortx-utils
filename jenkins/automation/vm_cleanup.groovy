#!/usr/bin/env groovy

properties([[$class: 'ThrottleJobProperty', categories: [], limitOneJobWithMatchingParams: true, maxConcurrentPerNode: 1, maxConcurrentTotal: 10, paramsToUseForLimit: '', throttleEnabled: true, throttleOption: 'project']])

pipeline { 
    agent {
        node {
            // This job runs on vm deployment controller node to execute vm cleanup for the deployment configured host
            label "${NODE_LABEL} && cleanup_req"
        }
    }
	
    // Accept node label as parameter
    parameters {
        string(name: 'NODE_LABEL', defaultValue: 'cleanup_req', description: 'Node Label',  trim: true)
    }

	environment {

        // NODE1_HOST - Env variables added in the node configurations
        
        // Credentials used to SSH node
        NODE_DEFAULT_SSH_CRED = credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
        NODE_PASS = "${NODE_DEFAULT_SSH_CRED_PSW}"
        CLUSTER_PASS = "${NODE_DEFAULT_SSH_CRED_PSW}"

        // GID/pwd used to update root password 
        NODE_UN_PASS_CRED_ID = "mini-prov-change-pass"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    stages {

        // Clone deploymemt scripts from cortx-re repo
        stage ('Checkout Scripts') {
            steps {
                script {
                    
                    // Add badget to jenkins build
                    manager.addHtmlBadge("&emsp;<b>Host :</b><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'> ${env.NODE_NAME}</a>")

                    // Clone cortx-re repo
                    dir('cortx-re') {
                        checkout([$class: 'GitSCM', branches: [[name: '*/mini-provisioner-dev']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])                
                    }

                }
            }
        }

        // Cleanup previous deployment
        stage('Cleanup Node') {
            steps {
                retry(count: 2) {   
                    script {
                        
                        withCredentials([usernamePassword(credentialsId: "${NODE_UN_PASS_CRED_ID}", passwordVariable: 'SERVICE_PASS', usernameVariable: 'SERVICE_USER'), usernameColonPassword(credentialsId: "${CLOUDFORM_TOKEN_CRED_ID}", variable: 'CLOUDFORM_API_CRED')]) {
                            dir("cortx-re/scripts/mini_provisioner") {
                                ansiblePlaybook(
                                    playbook: 'prepare.yml',
                                    inventory: 'inventories/hosts',
                                    extraVars: [
                                        "NODE1"                 : [value: "${NODE1_HOST}", hidden: false],
                                        "CLUSTER_PASS"          : [value: "${CLUSTER_PASS}", hidden: false],
                                        "CLOUDFORM_API_CRED"    : [value: "${CLOUDFORM_API_CRED}", hidden: true],
                                        "SERVICE_USER"          : [value: "${SERVICE_USER}", hidden: true],
                                        "SERVICE_PASS"          : [value: "${SERVICE_PASS}", hidden: true],
                                    ],
                                    extras: '-v',
                                    colorized: true
                                )
                            }                        
                        }

                        def remoteHost = getTestMachine("${NODE1_HOST}", "${NODE_USER}", "${NODE_PASS}")

                        // Validate Cleanup
                        sshCommand remote: remoteHost, command: '''
                            set +x
                            if [[ ! $(ls -1 '/root') ]]; then
                                echo "[ reimage_validation ] : OK - No Files in '/root' location";
                            else 
                                echo "[ reimage_validation ] : NOT_OK - Files found in /root";
                                exit 1
                            fi

                            for folder in "/var/log/seagate" "/opt/seagate";
                            do
                                if [[ ! -d "${folder}" ]]; then
                                    echo "[ reimage_validation ] : OK - Folder does not exists ( ${folder} )";
                                else 
                                    echo "[ reimage_validation ] : NOT_OK - Folder exists ${folder}";
                                    exit 1
                                fi
                            done

                            if [[ ! $(yum list installed | grep "cortx") ]]; then
                                echo "[ reimage_validation ] : OK - No cortx component get installed";
                            else
                                echo "[ reimage_validation ] : NOT_OK - cortx component already installed";
                                exit 1
                            fi 
                        '''
                    }
                }
            }
        }
	}

    post {
        failure {
            script {
                // On cleanup failure take node offline
                markNodeOffline(" VM Re-Image Issue  - Automated offline , Ref : ${BUILD_URL}")
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