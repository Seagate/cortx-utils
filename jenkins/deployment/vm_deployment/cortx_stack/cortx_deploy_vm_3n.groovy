#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            // Run deployment on mini_provisioner nodes (vm deployment nodes)
            label params.NODE1.isEmpty() ? "vm_deployment_3n && !cleanup_req" : "vm_deployment_3n_controller"
            customWorkspace "/var/jenkins/cortx_deployment_vm/${JOB_NAME}_${BUILD_NUMBER}"
        }
    }
	
    parameters {
        string(name: 'CORTX_BUILD', defaultValue: 'http://cortx-storage.colo.seagate.com/releases/cortx/github/main/centos-7.8.2003/last_successful_prod/', description: 'Build URL',  trim: true)
        string(name: 'NODE1', defaultValue: '', description: 'Node 1 Host FQDN',  trim: true)
        string(name: 'NODE2', defaultValue: '', description: 'Node 2 Host FQDN',  trim: true)
        string(name: 'NODE3', defaultValue: '', description: 'Node 3 Host FQDN',  trim: true)
        string(name: 'NODE_PASS', defaultValue: '', description: 'Host machine root user password',  trim: true)
        string(name: 'NODE_MGMT_VIP', defaultValue: '', description: 'The floating static VIP for management network interface.',  trim: true)
        booleanParam(name: 'DEBUG', defaultValue: false, description: 'Select this if you want to preserve the VM temporarily for troublshooting')
        booleanParam(name: 'CREATE_JIRA_ISSUE_ON_FAILURE', defaultValue: false, description: 'Internal Use : Select this if you want to create Jira issue on failure')
        booleanParam(name: 'AUTOMATED', defaultValue: false, description: 'Internal Use : Only for Internal RE workflow')
    }

	environment {

        // NODE1_HOST - Env variables added in the node configurations
        build_id = getBuild("${CORTX_BUILD}")

        CORTX_BUILD = getActualBuild("${CORTX_BUILD}")

        NODE_DEFAULT_SSH_CRED =  credentials("${NODE_DEFAULT_SSH_CRED}")
        NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
        
        NODE_PASS   = "${NODE_PASS.isEmpty() ? NODE_DEFAULT_SSH_CRED_PSW : NODE_PASS}"
        NODE1_HOST  = "${NODE1.isEmpty() ? NODE1_HOST : NODE1 }"
        NODE2_HOST  = "${NODE2.isEmpty() ? NODE2_HOST : NODE2 }"
        NODE3_HOST  = "${NODE3.isEmpty() ? NODE3_HOST : NODE3 }"
        MGMT_VIP    = "${NODE_MGMT_VIP.isEmpty() ? MGMT_VIP : NODE_MGMT_VIP }"
        NODES       = "${NODE1_HOST},${NODE2_HOST},${NODE3_HOST}"

        SETUP_TYPE = '3_node'
        SKIP_STAGE = "no"
    }

    options {
        timeout(time: 180, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }

    stages {

        stage ('Prerequisite') {
            steps {
                script {

                    manager.addHtmlBadge("&emsp;<b>Build :</b> <a href=\"${CORTX_BUILD}\"><b>${build_id}</b></a> <br /> <b>Host :</b> <a href='${JENKINS_URL}/computer/${env.NODE_NAME}'><b>${NODE1_HOST}</b></a>")

                    sh """
                        set +x
                        echo "--------------VM DEPLOYMENT PARAMETERS -------------------"
                        echo "NODES                         = ${NODES}"
                        echo "CORTX_BUILD                   = ${CORTX_BUILD}"
                        echo "DEBUG                         = ${DEBUG}"
                        echo "-----------------------------------------------------------"
                    """
                    dir('cortx-re') {
                        checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                    }

                    if ( NODE1.isEmpty() ) {
					    markNodeforCleanup()
                    }
                }
            }
        }

        stage('00. Prepare Environment') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    try {
                        info("Running '00. Prepare Environment' Stage")  

                        runAnsible("00_PREPARE")
                    }
                    catch (err) {
                        currentBuild.result = 'UNSTABLE'
                        SKIP_STAGE = "yes"
                    }
                }
            }
        }

        stage('01. Deploy Prereq') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    try {
                        info("Running '01. Deploy Prereq' Stage")

                        runAnsible("01_DEPLOY_PREREQ")
                    }
                    catch (err) {
                        currentBuild.result = 'UNSTABLE'
                        SKIP_STAGE = "yes"
                    }
                }
            } 
        }

        stage('02.1 Bootstarp Provisioner') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.1 Bootstarp Provisioner' Stage")

                    runAnsible("02_1_PRVSNR_BOOTSTRAP,02_DEPLOY_VALIDATE")
                }
            } 
        }

        stage('02.2 Platform Setup') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.2 Platform Setup' Stage")

                    runAnsible("02_2_PLATFORM_SETUP, 02_DEPLOY_VALIDATE")
                }
            } 
        }

        stage('02.3 3party Tools Setup') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.3 Prereq/Configuration 3party tools")

                    runAnsible("02_3_PREREQ,02_DEPLOY_VALIDATE")
                }
            } 
        }

        stage('02.4 Cortx Utils Setup') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.4 Cortx Utils Setup' Stage")

                    runAnsible("02_4_UTILS, 02_DEPLOY_VALIDATE")
                }
            } 
        }

        stage('02.5 IO Path Setup') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.5 IO Path Setup' Stage")

                    runAnsible("02_5_IO_PATH,02_DEPLOY_VALIDATE")
                }
            } 
        }

        stage('02.6 Control Path Setup') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.6 Control Path Setup' Stage")

                    runAnsible("02_DEPLOY_VALIDATE, 02_6_CONTROL_PATH")
                }
            } 
        }

        stage('02.7 HA Setup') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    
                    info("Running '02.7 HA Setup' Stage")

                    runAnsible("02_DEPLOY_VALIDATE,02_7_HA")
                }
            } 
        }

        stage('03. Validate') {
            when { expression { SKIP_STAGE == "no"  } }
            steps {
                script {
                    try {
                        info("Running '03. Validate Deployment' Stage")

                        runAnsible("03_VALIDATE")
                    }
                    catch (err) {
                        currentBuild.result = 'UNSTABLE'
                        SKIP_STAGE = "yes"
                    }                
                }
            } 
        }
	}

    post { 
        always {
            script {
                
                // POST ACTIONS

                // 1. Download Log files from Deployment Machine
                try {
                    sh label: 'download_log_files', returnStdout: true, script: """ 
                        mkdir -p artifacts/srvnode1 
                        mkdir -p artifacts/srvnode2 
                        mkdir -p artifacts/srvnode3 
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/log/seagate/cortx/ha artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/log/cluster artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/log/pacemaker.log artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/log/pcsd/pcsd.log artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/log/seagate/provisioner artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx_configs/provisioner_cluster.json artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/lib/hare/cluster.yaml artifacts/srvnode1 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/root/cortx_deployment artifacts/srvnode1 &>/dev/null || true

                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE2_HOST}:/root/cortx_deployment artifacts/srvnode2 &>/dev/null || true
                        sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE3_HOST}:/root/cortx_deployment artifacts/srvnode3 &>/dev/null || true
                    """
                } catch (err) {
                    echo err.getMessage()
                }

                // 2. Archive Deployment artifacts in jenkins build
                archiveArtifacts artifacts: "artifacts/**/*.*", onlyIfSuccessful: false, allowEmptyArchive: true 

                // 3. Trigger Cleanup Deployment Nodes
                if (NODE1.isEmpty()) {
                    if ( params.DEBUG ) {  
                        // Take Node offline for debugging  
                        markNodeOffline("R2 - 3N VM Deployment Debug Mode Enabled on This Host - ${BUILD_URL}")
                    } else {
                        // Trigger cleanup VM
                        build job: 'Cortx-Automation/Deployment/VM-Cleanup-MultiNode', wait: false, parameters: [string(name: 'DEPLOYMENT_NODE_LABEL', value: "${env.NODE_NAME}")]                    

                    }
                }
                
                // 4. Assume Deployment Status Based on log results
                hctlStatus = ""
                if ( fileExists('artifacts/srvnode1/cortx_deployment/log/hctl_status.log') && currentBuild.currentResult == "SUCCESS" ) {
                    hctlStatus = readFile(file: 'artifacts/srvnode1/cortx_deployment/log/hctl_status.log')
                    MESSAGE = "3 Node - Cortx Stack VM Deployment Success for the build ${build_id}"
                    ICON = "accept.gif"
                    STATUS = "SUCCESS"
                } else if ( currentBuild.currentResult == "FAILURE" ) {
                    manager.buildFailure()
                    MESSAGE = "3 Node - Cortx Stack VM Deployment Failed for the build ${build_id}"
                    ICON = "error.gif"
                    STATUS = "FAILURE"
                    // Failure component name and Cause can be retrived from deployment status log
                    if ( fileExists('artifacts/srvnode1/cortx_deployment/log/deployment_status.log')
                        && fileExists('artifacts/srvnode1/cortx_deployment/log/failed_component.log') ) {
                        try {   
                            deployment_status_log = readFile(file: 'artifacts/srvnode1/cortx_deployment/log/deployment_status.log').trim()
                            failed_component_stage = readFile(file: 'artifacts/srvnode1/cortx_deployment/log/failed_component.log').trim()
                            failed_component_stage = failed_component_stage.trim().replaceAll("'","")
                            
                            // Failed Component from Failed Stage
                            component_info_map = getComponentInfo(failed_component_stage)
                            component_name = component_info_map["name"]
                            component_email = component_info_map["email"] 
                    
                            env.failure_cause = deployment_status_log
                            env.deployment_status_log = deployment_status_log
                            env.failed_component_stage = failed_component_stage
                            env.component_name = component_name
                            env.component_email = component_email

                            MESSAGE = "3 Node - Cortx Stack VM-Deployment Failed in ${component_name} for the build ${build_id}"
                            manager.addHtmlBadge("<br /> <b>Status :</b> <a href='${BUILD_URL}/artifact/artifacts/srvnode1/cortx_deployment/log/deployment_status.log'><b>Failed in '${component_name}'</a>")
                        
                        } catch (err) {
                            echo err.getMessage()
                        }
                    }
                } else {
                    manager.buildUnstable()
                    MESSAGE = "3 Node - Cortx Stack VM Deployment is Unstable"
                    ICON = "warning.gif"
                    STATUS = "UNSTABLE"
                }

                // 5. Create JIRA on Failure - Create JIRA if deployment failed and create Jira true
                //  - Jira issue should be created only when 'CREATE_JIRA_ISSUE_ON_FAILURE' option is enabled
                //  - Jira issue should be created only when 'previous build is success' (To avoid Multiple jira tickets)
                //  FIXME - LOGIC NEED TO BE IMPROVED TO QUERY JIRA TO IDENTIFY EXSITING TICKETS FOR THE SAME ISSUE
                if ( params.CREATE_JIRA_ISSUE_ON_FAILURE 
                    && "FAILURE".equals(currentBuild.currentResult)
                    && ( !params.AUTOMATED || "SUCCESS".equals(currentBuild.previousBuild.result))
                    &&  env.failed_component_stage && env.component_name && env.deployment_status_log ) {
                    
                    jiraIssue = createJiraIssue(env.failed_component_stage, env.component_name, env.deployment_status_log)

                    manager.addHtmlBadge(" <br /><b>Jira Issue :</b> <a href='https://jts.seagate.com/browse/${jiraIssue}'><b>${jiraIssue}</b></a>")

                    env.jira_issue="https://jts.seagate.com/browse/${jiraIssue}"
                }

                // 5. Create Jenkins Summary page with deployment info
                hctlStatusHTML = "<pre>${hctlStatus}</pre>"
                tableSummary = "<table border='1' cellspacing='0' cellpadding='0' width='400' align='left'> <tr> <td align='center'>Build</td><td align='center'><a href=${CORTX_BUILD}>${build_id}</a></td></tr><tr> <td align='center'>Test VM</td><td align='center'><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'><b>${NODE1_HOST}</b></a></td></tr></table>"
                manager.createSummary("${ICON}").appendText("<h3>Cortx Stack VM-Deployment ${currentBuild.currentResult} for the build <a href=\"${CORTX_BUILD}\">${build_id}.</a></h3><p>Please check <a href=\"${BUILD_URL}/artifact/setup.log\">setup.log</a> for more info <br /><br /><h4>Test Details:</h4> ${tableSummary} <br /><br /><br /><h4>Cluster Status:</h4>${hctlStatusHTML}", false, false, false, "red")
                     
                // 6. Send Email about deployment status
                env.build_id = build_id
                env.build_location = "${CORTX_BUILD}"
                env.host = "${NODES}"
                env.deployment_status = "${MESSAGE}"
                if (fileExists('artifacts/srvnode1/cortx_deployment/log/hctl_status.log')) {
                    env.cluster_status = "${BUILD_URL}/artifact/artifacts/srvnode1/cortx_deployment/log/hctl_status.log"
                }
                
                if ( "FAILURE".equals(currentBuild.currentResult) && params.AUTOMATED && env.component_email ) {
                    toEmail = "${env.component_email}, priyank.p.dalal@seagate.com, gaurav.chaudhari@seagate.com"
                } else {
                    toEmail = "gaurav.chaudhari@seagate.com"
                }
                
                emailext (
                    body: '''${SCRIPT, template="vm-deployment-email.template"}''',
                    mimeType: 'text/html',
                    subject: "${MESSAGE}",
                    to: toEmail,
                    recipientProviders: [[$class: 'RequesterRecipientProvider']]
                )

                 // 7. Archive all log generated by Test
                cleanWs()
            }
        }
    }
}	


// Run Ansible playbook to perform deployment
def runAnsible(tags) {
    
    dir("cortx-re/scripts/deployment") {
        ansiblePlaybook(
            playbook: 'cortx_deploy_vm.yml',
            inventory: 'inventories/vm_deployment/hosts_srvnodes',
            tags: "${tags}",
            extraVars: [
                "HOST"          : [value: "${NODES}", hidden: false],
                "CORTX_BUILD"   : [value: "${CORTX_BUILD}", hidden: false] ,
                "CLUSTER_PASS"  : [value: "${NODE_PASS}", hidden: false],
                "SETUP_TYPE"    : [value: "${SETUP_TYPE}", hidden: false],
                "MGMT_VIP"      : [value: "${MGMT_VIP}", hidden: false],
            ],
            extras: '-v',
            colorized: true
        )
    }
}

// Get build id from build url
def getBuild(buildURL) {

    buildID = sh(script: "curl -s  $buildURL/RELEASE.INFO  | grep BUILD | cut -d':' -f2 | tr -d '\"' | xargs", returnStdout: true).trim()
    buildBranch = "Build"
    if ( buildURL.contains("/cortx/github/main/") ) {
        buildBranch = "Main"
    } else if ( buildURL.contains("/cortx/github/stable/") ) {
        buildBranch = "Stable"
    } else if ( buildURL.contains("/cortx/github/integration-custom-ci/")) {
        buildBranch = "Custom-CI"
    }

 return "$buildBranch#$buildID"   
}

// Get build id from build url
def getActualBuild(buildURL) {

    buildRoot = "http://cortx-storage.colo.seagate.com/releases/cortx/github"
    buildID = sh(script: "curl -s  $buildURL/RELEASE.INFO  | grep BUILD | cut -d':' -f2 | tr -d '\"' | xargs", returnStdout: true).trim()
    if ( buildURL.contains("/cortx/github/main/") ) {
        buildURL = "${buildRoot}/main/centos-7.8.2003/${buildID}/prod"
    } else if ( buildURL.contains("/cortx/github/stable/") ) {
        buildURL = "${buildRoot}/stable/centos-7.8.2003/${buildID}/prod"
    } else if ( buildURL.contains("/cortx/github/integration-custom-ci/")) {
        buildURL = "${buildRoot}/integration-custom-ci/centos-7.8.2003/custom-build-${buildID}"
    }

 return buildURL  
}

// Get failed component name
def getComponentInfo(String stage) {
    
    stage = stage.count(".") > 1 ? stage.tokenize(".")[0]+"."+stage.tokenize(".")[1] : stage
    
    def defaultComponentMap = [ name : "RE", email : "CORTX.DevOps.RE@seagate.com"]
    def componentInfoMap = [
        "bootstrap"                 : [ name : "Provisioner",   email : "CORTX.Provisioner.Re@seagate.com" ],
        "components.system"         : [ name : "Provisioner",   email : "CORTX.Provisioner.Re@seagate.com" ],
        "components.misc_pkgs"      : [ name : "Provisioner",   email : "CORTX.Provisioner.Re@seagate.com" ],
        "components.motr"           : [ name : "Motr",          email : "cortx.motr@seagate.com" ],
        "components.s3server"       : [ name : "S3Server",      email : "CORTX.s3@seagate.com" ],
        "components.hare"           : [ name : "hare",          email : "CORTX.Hare@seagate.com" ],
        "components.ha"             : [ name : "HA",            email : "CORTX.HA@seagate.com" ],
        "components.sspl"           : [ name : "Monitor",       email : "CORTX.monitor@seagate.com" ],
        "components.csm"            : [ name : "CSM",           email : "CORTX.CSM@seagate.com" ],
        "components.cortx_utils"    : [ name : "Foundation",    email : "CORTX.Foundation@seagate.com" ]
    ]

    return componentInfoMap[stage] ? componentInfoMap[stage] : defaultComponentMap
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

// Make failed node offline
def markNodeOffline(message) {
    node = getCurrentNode(env.NODE_NAME)
    computer = node.toComputer()
    computer.setTemporarilyOffline(true)
    computer.doChangeOfflineCause(message)
    computer = null
    node = null
}

// Get current Node
def getCurrentNode(nodeName) {
  for (node in Jenkins.instance.nodes) {
      if (node.getNodeName() == nodeName) {
        echo "Found node for $nodeName"
        return node
    }
  }
  throw new Exception("No node for $nodeName")
}

// Add 'cleanup_req' label to VM to identify unclean vm
def markNodeforCleanup() {
	nodeLabel = "cleanup_req"
    node = getCurrentNode(env.NODE_NAME)
	node.setLabelString(node.getLabelString() + " " + nodeLabel)
	node.save()
    node = null
}

// Create jira issues on failure and input parameter 
def createJiraIssue(String failedStage, String failedComponent, String failureLog) {

    def issue = [
                    fields: [ 
                        project: [key: 'EOS'],
                        issuetype: [name: 'Bug'],
                        priority: [name: "Blocker"],
                        versions: [[name: "LDR-R2"]],
                        labels: ["PI-1"],
                        components: [[name: "${failedComponent}"]],
                        summary: "3N VM-Deployment Failed in ${failedComponent} for the build ${build_id}",
                        description: "{panel}VM Deployment is failed in ${failedStage} for the build [${build_id}|${CORTX_BUILD}]. Please check Jenkins console log and deployment log for more info.\n"+
                                    "\n h4. Deployment Info \n"+
                                    "|Cortx build|[${build_id}|${CORTX_BUILD}]|\n"+
                                    "|Jenkins build|[${JOB_BASE_NAME}#${BUILD_NUMBER} |${BUILD_URL}]|\n"+
                                    "|Failed Component |*${failedComponent}*|\n"+
                                    "|Deployment Host|${NODE1_HOST}|\n"+
                                    "|Deployment Log|[${JOB_BASE_NAME}/${BUILD_NUMBER}/artifact|${BUILD_URL}artifact]|\n"+
                                    "\n\n"+
                                    "h4. Failure Log\n"+
                                    "{code:java}${failureLog}{code} \n {panel}"
                    ]
                ]


    def newIssue = jiraNewIssue issue: issue, site: 'SEAGATE_JIRA'
    return newIssue.data.key
}