#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            // Run deployment on mini_provisioner nodes (vm deployment nodes)
            label "mini_provisioner_hare && !cleanup_req"
        }
    }
	
    parameters {
        string(name: 'CORTX_BUILD', defaultValue: 'http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.8.2003/last_successful_prod/', description: 'Build URL',  trim: true)
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: 'Keep Host for Debuging') 
        string(name: 'HOST', defaultValue: '-', description: 'Host FQDN',  trim: true)
        password(name: 'HOST_PASS', defaultValue: '-', description: 'Host machine root user password')  
    }

	environment {

        // NODE1_HOST - Env variables added in the node configurations
        build_id = sh(script: "echo ${CORTX_BUILD} | rev | cut -d '/' -f2,3 | rev", returnStdout: true).trim()

        // GID/pwd used to update root password 
        NODE_UN_PASS_CRED_ID = "mini-prov-change-pass"
        
        // Credentials used to SSH node
        NODE_DEFAULT_SSH_CRED = credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
        NODE_PASS = "${NODE_DEFAULT_SSH_CRED_PSW}"
        CLUSTER_PASS = "${NODE_DEFAULT_SSH_CRED_PSW}"

        // Control to skip/run stages - (used for trublshooting purpose)
        STAGE_00_PREPARE_ENV = "yes"
        STAGE_01_PREREQ = "yes"
        STAGE_02_MINI_PROV = "yes"
        STAGE_04_VALIDATE = "yes"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    stages {

        // Clone deploymemt scripts from cortx-re repo
        stage ('Prerequisite') {
            steps {
                script {
                    
                    // Add badget to jenkins build
                    manager.addHtmlBadge("&emsp;<b>Build :</b> <a href=\"${CORTX_BUILD}\"><b>${build_id}</b></a> <br /> &emsp;<b>Deployment Host :</b><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'> ${NODE1_HOST}</a>&emsp;")

                    sh """
                        set +x
                        echo "--------------HW DEPLOYMENT PARAMETERS -------------------"
                        echo "NODE1             = ${NODE1_HOST}"
                        echo "CORTX_BUILD       = ${CORTX_BUILD}"
                        echo "-----------------------------------------------------------"
                    """

                    // Clone cortx-re repo
                    dir('cortx-re') {
                        checkout([$class: 'GitSCM', branches: [[name: '*/mini-provisioner-dev']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                    }
                    
                    if ( "${HOST}" == "-" ) {
                        markNodeforCleanup()
                    }
                }
            }
        }

        // Prepare deployment environment - (passwordless ssh, installing requireed tools..etc)
        stage('00. Prepare Environment') {
            when { expression { env.STAGE_00_PREPARE_ENV == "yes" } }
            steps {
                script {
                    
                    info("Running '00. Prepare Environment' Stage")  

                    runAnsible("00_PREP_ENV")
                }
            }
        }

        // Execute hare mini provisioning prereq steps  
        stage('01. Prereq') {
            when { expression { env.STAGE_01_PREREQ == "yes" } }
            steps {
                script {
                    
                    info("Running '01. Prereq' Stage")

                    runAnsible("01_PREREQ")

                }
            } 
        }

        // Install Hare and dependent component(motr,cortx-pyutils) from the provided build
        stage('02. Mini Provisioning') {
            when { expression { env.STAGE_02_MINI_PROV == "yes" } }
            steps {
                script {
                    
                    info("Running '02. Mini Provisioning' Stage")

                    runAnsible("02_MINI_PROV")

                }
            } 
        }

        stage('04. Validate') {
            when { expression { env.STAGE_04_VALIDATE == "yes" } }
            steps {
                script {
                    
                    info("Running '04. Validate' Stage")

                    runAnsible("04_VALIDATE")

                }
            } 
        }
	}

    post { 
        always {
            script {

                // Download deployment log files from deployment node
                try {
                    sh label: 'download_log_files', returnStdout: true, script: """
                        mkdir -p artifacts
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx/hare/conf/*1-node artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/lib/hare/cluster.yaml artifacts/ || true
                    """
                } catch (err) {
                    echo err.getMessage()
                }

                archiveArtifacts artifacts: "artifacts/*", onlyIfSuccessful: false, allowEmptyArchive: true 

                if ( "${HOST}" == "-" ) { 
                    if ( "${DEBUG}" == "yes" ) {  
                        markNodeOffline("Debug Mode Enabled on This Host  - ${BUILD_URL}")
                    } else {
                        build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]                    
                    }
                }
                                     
                cleanWs()
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


// Used Jenkins ansible plugin to execute ansible command
def runAnsible(tags) {
    dir("cortx-re/scripts/mini_provisioner") {
        ansiblePlaybook(
            playbook: 'hare_deploy.yml',
            inventory: 'inventories/hosts',
            tags: "${tags}",
            extraVars: [
                "NODE1"                 : [value: "${NODE1_HOST}", hidden: false],
                "CORTX_BUILD"           : [value: "${CORTX_BUILD}", hidden: false] ,
                "CLUSTER_PASS"          : [value: "${CLUSTER_PASS}", hidden: false]
            ],
            extras: '-v',
            colorized: true
        )
    }
}

// Used below methods for logging
def info(msg) {
    echo "--------------------------------------------------------------"
    echo "\033[44m[Info] : ${msg} \033[0m"
    echo "--------------------------------------------------------------"
}
def error(msg) {
    echo "--------------------------------------------------------------"
    echo "\033[1;31m[Error] : ${msg} \033[0m"
    echo "--------------------------------------------------------------"
}
def success(msg) {
    echo "--------------------------------------------------------------"
    echo "\033[1;32m[Success] : ${msg} \033[0m"
    echo "--------------------------------------------------------------"
}

// Mark node for cleanup ( cleanup job will use this node label to identify cleanup node)
def markNodeforCleanup() {
	nodeLabel = "cleanup_req"
    node = getCurrentNode(env.NODE_NAME)
	node.setLabelString(node.getLabelString()+" "+nodeLabel)
	node.save()
    node = null
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

def getCurrentNode(nodeName) {
  for (node in Jenkins.instance.nodes) {
      if (node.getNodeName() == nodeName) {
        echo "Found node for $nodeName"
        return node
    }
  }
  throw new Exception("No node for $nodeName")
}