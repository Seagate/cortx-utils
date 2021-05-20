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
        choice(name: 'MINI_PROV_END_STEP', choices: ["Cleanup", "Reset", "Test", "Start", "Init", "Config", "Prepare", "Post_Install", "Pre_Requisites" ], description: '''<pre>

Cleanup         -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3cleanup">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3cleanup</a>
Reset           -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3reset">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3reset</a>
Test            -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3test">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3test</a>
Start           -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#start-s3server-and-motr-for-io">S3server-provisioning-on-single-node-VM-cluster:-Manual#start-s3server-and-motr-for-io</a>
Init            -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3init">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3init</a>
Config          -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3config">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3config</a>
Prepare         -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3prepare">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3prepare</a>
Post_Install    -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#s3post_install">S3server-provisioning-on-single-node-VM-cluster:-Manual#s3post_install</a>
Pre_Requisites  -> <a href="https://github.com/Seagate/cortx-s3server/wiki/S3server-provisioning-on-single-node-VM-cluster:-Manual#pre-requisites">S3server-provisioning-on-single-node-VM-cluster:-Manual#pre-requisites</a>

</pre>''')
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: '''<pre>
NOTE : Only applicable when 'HOST' parameter is provided

no -> Cleanup the vm on post deployment  
yes -> Preserve host for troublshooting [ WARNING ! Automated Deployment May be queued/blocked if more number of vm used for debuging ]  
</pre>''')
        string(name: 'HOST', defaultValue: '-', description: '''<pre>
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
                        echo "-------------- DEPLOYMENT PARAMETERS -------------------"
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
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '00. Prepare Environment' Stage")  

                    runAnsible("00_PREP_ENV")
                }
            }
        }

        stage('01. Pre_Requisites') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Pre_Requisites|Post_Install|Prepare|Config|Init|Start|Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    info("Running '01. Prereq' Stage")

                    runAnsible("01_PREREQ")

                }
            } 
        }

        stage('02.1 : Post_Install') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Post_Install|Prepare|Config|Init|Start|Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    runAnsible("02_MINI_PROV_POST_INSTALL")
                }
            } 
        }

        stage('02.2 : Prepare') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Prepare|Config|Init|Start|Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    runAnsible("02_MINI_PROV_PREPARE")

                }
            } 
        }

        stage('02.3 : Config') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Config|Init|Start|Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    runAnsible("02_MINI_PROV_CONFIG")

                }
            } 
        }

        stage('02.4 : Init') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Init|Start|Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    runAnsible("02_MINI_PROV_INIT")

                }
            } 
        }

        stage('03 : Start') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Start|Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {
                    
                    runAnsible("03_START_S3SERVER")

                }
            } 
        }

        stage('04 : Test') {
            when { expression { params.MINI_PROV_END_STEP ==~ /Test|Reset|Cleanup/ } }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {

                    runAnsible("04_VALIDATE")

                }
            } 
        }
	}

    post { 
        always {
            script {

                runAnsible("SUPPORT_BUNDLE")

                // Download deployment log files from deployment node
                try {
                    sh label: 'download_log_files', returnStdout: true, script: """ 
                        mkdir -p artifacts
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/root/*.log artifacts/ || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/root/support_bundle artifacts/ || true
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

                archiveArtifacts artifacts: "artifacts/**/*.*", onlyIfSuccessful: false, allowEmptyArchive: true                           
        
                 // Archive all log generated by Test
                cleanWs()

                env.build_stage = "${build_stage}"
                env.build_url = "${CORTX_BUILD}"

                def mailRecipients = "nilesh.govande@seagate.com, basavaraj.kirunge@seagate.com, rajesh.nambiar@seagate.com, amit.kumar@seagate.com"
                emailext body: '''${SCRIPT, template="mini_prov-email.template"}''',
                mimeType: 'text/html',
                recipientProviders: [requestor()], 
                subject: "[Jenkins] S3ManualMiniProvisioning : ${currentBuild.currentResult}, ${JOB_BASE_NAME}#${BUILD_NUMBER}",
                to: "${mailRecipients}"
            }
        }
        cleanup {
            script {

                if ( params.MINI_PROV_END_STEP == "Reset" ||  params.MINI_PROV_END_STEP == "Cleanup") {
                    runAnsible("05_MINI_PROV_RESET")
                } 

                if ( params.MINI_PROV_END_STEP == "Cleanup" ) {
                    runAnsible("05_MINI_PROV_CLEANUP")
                } 
                
                if ( "${HOST}" == "-" ) {

                    if ( "${DEBUG}" == "yes" ) {  
                        markNodeOffline("S3 Debug Mode Enabled on This Host  - ${BUILD_URL}")
                    } else {
                        build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]                    
                    }
                } 

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