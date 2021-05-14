#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            // random node to execute the groovy script - no operations are performed on the node
            label "${DEPLOYMENT_NODE_LABEL} && cleanup_req"
        }
    }
	
    parameters {
        string(name: 'DEPLOYMENT_NODE_LABEL', defaultValue: 'vm_deployment_3n', description: 'Cleanup Node Label',  trim: true)
    }	

    environment {

        NODE_DEFAULT_SSH_CRED = credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
        NODE_PASS = "${NODE_DEFAULT_SSH_CRED_PSW}"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
        parallelsAlwaysFailFast()
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
                        checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])                
                    }

                }
            }
        }

        stage ('Cleanup Nodes') {
            steps {
                script {
                    
                    srvnodes = []
                    for (i = 0; i <36; i++) {
                        if (env["NODE${i}_HOST"] != null ) {
                            srvnodes.add(env["NODE${i}_HOST"])
                        }
                    } 
                    
                    cleanup_nodes = [:]
                    srvnodes.eachWithIndex { n, index ->
                        cleanup_nodes[n] = {
                            runCleanup(n, (1+index)*30) 
                        }
                    }

                    parallel cleanup_nodes
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


def runCleanup(host, sleepCount) {
    
    sleep(sleepCount)

    withCredentials([usernameColonPassword(credentialsId: "${CLOUDFORM_TOKEN_CRED_ID}", variable: 'CLOUDFORM_API_CRED')]) {
        dir("cortx-re/scripts/mini_provisioner") {
            ansiblePlaybook(
                playbook: 'prepare.yml',
                inventory: 'inventories/hosts',
                extraVars: [
                    "NODE1"                 : [value: "${host}", hidden: false],
                    "CLUSTER_PASS"          : [value: "${NODE_PASS}", hidden: false],
                    "CLOUDFORM_API_CRED"    : [value: "${CLOUDFORM_API_CRED}", hidden: true],
                ],
                extras: '-v',
                colorized: true
            )
        }                        
    } 

    sshCommand remote: getTestMachine("${host}", "${NODE_USER}", "${NODE_PASS}"), command: '''
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