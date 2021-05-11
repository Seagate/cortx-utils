#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            // Run deployment on mini_provisioner nodes (vm deployment nodes)
            label params.HOST == "-" ? "mini_provisioner_s3 && !cleanup_req" : "mini_provisioner_s3_user_host"
            customWorkspace "/var/jenkins/mini_provisioner/${JOB_NAME}_${BUILD_NUMBER}"
        }
    }
	
    parameters {
        string(name: 'CORTX_BUILD', defaultValue: 'http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.8.2003/last_successful_prod/', trim: true, description: '''<pre>
Target build URL  
Example: The URL should contain directory structure like,  
3rd_party/  
cortx_iso/  
python_deps/   
RELEASE.INFO  
THIRD_PARTY_RELEASE.INFO  
</pre>  
        '''  )
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: '''<pre>
NOTE : Only applicable when 'HOST' parameter is provided

no -> Cleanup the vm on post deployment  
yes -> Preserve host for troublshooting [ WARNING ! Automated Deployment May be queued/blocked if more number of vm used for debuging ]  
</pre>''')
        string(name: 'HOST', defaultValue: '-', description: '''<pre>
When Host is provided the job will run till s3init step  - https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3init
FQDN of ssc-vm

Recommended VM specification:
- Cloudform VM Template : LDRr2 - CentOS 7.8  
- vCPUs                 : 1  
- Memory (RAM)          : 4GB  
- Additional Disks      : 2   
- Additional Disk Size  : 25 GB  
</pre>
        ''',  trim: true)
        password(name: 'HOST_PASS', defaultValue: '-', description: 'VM <b>root</b> user password')   
    }

	environment {

        // NODE1_HOST - Env variables added in the node configurations
        build_id = sh(script: "echo ${CORTX_BUILD} | rev | cut -d '/' -f2,3 | rev", returnStdout: true).trim()

        // Credentials used to SSH node
        NODE_DEFAULT_SSH_CRED = credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"

        NODE1_HOST = "${HOST == '-' ? NODE1_HOST : HOST }"
        NODE_PASS = "${HOST_PASS == '-' ? NODE_DEFAULT_SSH_CRED_PSW : HOST_PASS}"
    
        // Control to skip/run stages - (used for trublshooting purpose)
        STAGE_00_PREPARE_ENV = "yes"
        STAGE_01_PREREQ = "yes"
        STAGE_02_MINI_PROV = "yes"
        STAGE_03_START_S3SERVER = "yes"
        STAGE_04_VALIDATE_DEPLOYMENT = "yes"

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
                script { build_stage = env.STAGE_NAME }
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
                        checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])                
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
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '00. Prepare Environment' Stage")  

                    runAnsible("00_PREP_ENV")
                }
            }
        }

        // Execute s3 mini provisioning prereq steps  
        stage('01. Prereq') {
            when { expression { env.STAGE_01_PREREQ == "yes" } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '01. Prereq' Stage")

                    runAnsible("01_PREREQ")

                }
            } 
        }

        // Execute s3 mini provisioning to configure the deployment attributes
        stage('03. Mini Provisioning') {
            when { expression { env.STAGE_02_MINI_PROV == "yes" } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '02. Mini Provisioning' Stage")

                    runAnsible("02_MINI_PROV")

                }
            } 
        }

        // Start S3Server, Motr to perform I/O
        stage('04. Start S3server') {
            when { expression { env.STAGE_03_START_S3SERVER == "yes" && params.HOST == "-" } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '03. Start S3server' Stage")

                    runAnsible("03_START_S3SERVER")

                }
            } 
        }

        // Validate the deployment by performing basic i/o using s3cli command
        stage('04. Validate Deployment') {
            when { expression { env.STAGE_04_VALIDATE_DEPLOYMENT == "yes"  && params.HOST == "-" } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '04. Validate Deployment' Stage")

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
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/root/*.log artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/etc/haproxy/haproxy.cfg artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx/s3/conf/*1-node artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx/s3/s3backgrounddelete/config.yaml artifacts/s3backgrounddelete_config.yaml || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/tmp/cortx-config-new artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/etc/hosts artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx/s3/mini-prov/*.json artifacts/ || true
                    """
                } catch (err) {
                    echo err.getMessage()
                }

                archiveArtifacts artifacts: "artifacts/*", onlyIfSuccessful: false, allowEmptyArchive: true 

                if ( "${HOST}" == "-" ) {

                    if ( "${DEBUG}" == "yes" ) {  
                        markNodeOffline("S3 Debug Mode Enabled on This Host  - ${BUILD_URL}")
                    } else {
                        build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]                    
                    }

                    // Define build status based on hctl command
                    hctl_status = ""
                    if (fileExists ('artifacts/hctl_status.log')) { 
                        hctl_status = readFile(file: 'artifacts/hctl_status.log')
                        MESSAGE = "S3Server Deployment Completed"
                        ICON = "accept.gif"
                    } else {
                        manager.buildFailure()
                        MESSAGE = "S3Server Deployment Failed"
                        ICON = "error.gif"
                    }

                    hctl_status_html = "<textarea rows=20 cols=200 readonly style='margin: 0px; height: 392px; width: 843px;'>${hctl_status}</textarea>"
                    table_summary = "<table border='1' cellspacing='0' cellpadding='0' width='400' align='left'> <tr> <td align='center'>Build</td><td align='center'><a href=${CORTX_BUILD}>${build_id}</a></td></tr><tr> <td align='center'>Test VM</td><td align='center'>${NODE1_HOST}</td></tr></table>"
                    manager.createSummary("${ICON}").appendText("<h3>${MESSAGE} for the build <a href=\"${CORTX_BUILD}\">${build_id}.</a></h3><br /><br /><h4>Test Details:</h4> ${table_summary} <br /><br /><br /><h4>HCTL Status:${hctl_status_html}</h4> ", false, false, false, "red")
                
                }                            
        
                 // Archive all log generated by Test
                cleanWs()

                env.build_stage = "${build_stage}"
                env.build_url = "${CORTX_BUILD}"

                def mailRecipients = "nilesh.govande@seagate.com, basavaraj.kirunge@seagate.com, rajesh.nambiar@seagate.com, ajinkya.dhumal@seagate.com, amit.kumar@seagate.com"
                emailext body: '''${SCRIPT, template="mini_prov-email.template"}''',
                mimeType: 'text/html',
                recipientProviders: [requestor()], 
                subject: "[Jenkins] S3ManualMiniProvisioning : ${currentBuild.currentResult}, ${JOB_BASE_NAME}#${BUILD_NUMBER}",
                to: "${mailRecipients}"
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
            playbook: 's3server_deploy.yml',
            inventory: 'inventories/hosts',
            tags: "${tags}",
            extraVars: [
                "NODE1"                 : [value:"${NODE1_HOST}", hidden: false],
                "CORTX_BUILD"           : [value: "${CORTX_BUILD}", hidden: false] ,
                "CLUSTER_PASS"          : [value: "${NODE_PASS}", hidden: false]
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