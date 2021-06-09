#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            label 'docker-io-centos-7.8.2003-node'
        }
    }

    options { 
        skipDefaultCheckout()
        timeout(time: 180, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')  
    }

    parameters {  
	    string(name: 'CSM_URL', defaultValue: 'https://github.com/Seagate/cortx-management-portal', description: 'Repo for CSM Web')
        string(name: 'CSM_BRANCH', defaultValue: 'main', description: 'Branch for CSM Web') 
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: 'Keep Host for Debuging') 
        string(name: 'HOST', defaultValue: '-', description: 'Host FQDN',  trim: true)
        password(name: 'HOST_PASS', defaultValue: '-', description: 'Host machine root user password')       
	}

    environment {

        GPR_REPO = "https://github.com/${ghprbGhRepository}"
        CSM_URL = "${ghprbGhRepository != null ? GPR_REPO : CSM_URL}"
        CSM_BRANCH = "${sha1 != null ? sha1 : CSM_BRANCH}"

        CSM_GPR_REFSEPEC = "+refs/pull/${ghprbPullId}/*:refs/remotes/origin/pr/${ghprbPullId}/*"
        CSM_BRANCH_REFSEPEC = "+refs/heads/*:refs/remotes/origin/*"
        CSM_PR_REFSEPEC = "${ghprbPullId != null ? CSM_GPR_REFSEPEC : CSM_BRANCH_REFSEPEC}"

        //////////////////////////////// BUILD VARS //////////////////////////////////////////////////

        COMPONENT_NAME = "csm-web".trim()
        BRANCH = "${ghprbTargetBranch != null ? ghprbTargetBranch : 'stable'}"
        OS_VERSION = "centos-7.8.2003"
        THIRD_PARTY_VERSION = "centos-7.8.2003-2.0.0-latest"
        VERSION = "2.0.0"
        PASSPHARASE = credentials('rpm-sign-passphrase')

        // Artifacts root location

        // 'WARNING' - rm -rf command used on this path please careful when updating this value
        DESTINATION_RELEASE_LOCATION = "/mnt/bigstorage/releases/cortx/github/pr-build/${BRANCH}/${COMPONENT_NAME}/${BUILD_NUMBER}"
        PYTHON_DEPS = "/mnt/bigstorage/releases/cortx/third-party-deps/python-deps/python-packages-2.0.0-latest"
        THIRD_PARTY_DEPS = "/mnt/bigstorage/releases/cortx/third-party-deps/centos/${THIRD_PARTY_VERSION}/"
        COMPONENTS_RPM = "/mnt/bigstorage/releases/cortx/components/github/${BRANCH}/${OS_VERSION}/dev/"
        CORTX_BUILD = "http://cortx-storage.colo.seagate.com/releases/cortx/github/pr-build/${BRANCH}/${COMPONENT_NAME}/${BUILD_NUMBER}"

        // Artifacts location
        CORTX_ISO_LOCATION = "${DESTINATION_RELEASE_LOCATION}/cortx_iso"
        THIRD_PARTY_LOCATION = "${DESTINATION_RELEASE_LOCATION}/3rd_party"
        PYTHON_LIB_LOCATION = "${DESTINATION_RELEASE_LOCATION}/python_deps"

        ////////////////////////////////// DEPLOYMENT VARS /////////////////////////////////////////////////////

        STAGE_DEPLOY = "yes"
    }

    stages {

        // Build csm fromm PR source code
        stage('Build') {
            steps {
				script { build_stage = env.STAGE_NAME }
                script { manager.addHtmlBadge("&emsp;<b>Target Branch : ${BRANCH}</b>&emsp;<br />") }

                sh """
                    set +x
                    echo "--------------BUILD PARAMETERS -------------------"
                    echo "CSM_URL              = ${CSM_URL}"
                    echo "CSM_BRANCH           = ${CSM_BRANCH}"
                    echo "CSM_PR_REFSEPEC      = ${CSM_PR_REFSEPEC}"
                    echo "-----------------------------------------------------------"
                """
                 
                dir("csm") {

                    checkout([$class: 'GitSCM', branches: [[name: "${CSM_BRANCH}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CSM_URL}",  name: 'origin', refspec: "${CSM_PR_REFSEPEC}"]]])

                    sh label: '', script: '''
                        sed -i 's/gpgcheck=1/gpgcheck=0/' /etc/yum.conf
                        yum-config-manager --add http://cortx-storage.colo.seagate.com/releases/cortx/github/$BRANCH/$OS_VERSION/last_successful/
                        yum-config-manager --add http://cortx-storage.colo.seagate.com/releases/cortx/components/github/$BRANCH/$OS_VERSION/dev/cortx-utils/last_successful/
                        yum clean all && rm -rf /var/cache/yum
                        pip3.6 install  pyinstaller==3.5
                    '''

                    sh label: 'Build', returnStatus: true, script: '''
                        BUILD=$(git rev-parse --short HEAD)
                        echo "Executing build script"
                        echo "Python:$(python --version)"
                        ./cicd/build.sh -v $VERSION -b $BUILD_NUMBER -t -i
                    '''

                    sh label: 'Collect Release Artifacts', script: '''
                    
                        rm -rf "${DESTINATION_RELEASE_LOCATION}"
                        mkdir -p "${DESTINATION_RELEASE_LOCATION}"
            
                        if [[ ( ! -z `ls ./dist/rpmbuild/RPMS/x86_64/*.rpm `)]]; then
                            mkdir -p "${CORTX_ISO_LOCATION}"
                            cp ./dist/rpmbuild/RPMS/x86_64/*.rpm "${CORTX_ISO_LOCATION}"
                        else
                            echo "RPM not exists !!!"
                            exit 1
                        fi
                    '''	
                }
            }
        }

        // Release cortx deployment stack
        stage('Release') {
            steps {
				script { build_stage = env.STAGE_NAME }

                dir('cortx-re') {
                    checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 1, honorRefspec: true, noTags: true, reference: '', shallow: true], [$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                }

                // Install tools required for release process
                 sh label: 'Installed Dependecies', script: '''
                    yum install -y expect rpm-sign rng-tools python3-pip
                    systemctl start rngd
                '''

                // Integrate components rpms
                sh label: 'Collect Release Artifacts', script: '''
                    
                    pushd ${COMPONENTS_RPM}
                        for component in `ls -1 | grep -E -v "${COMPONENT_NAME}"`
                        do
                            echo -e "Copying RPM's for $component"
                            if ls $component/last_successful/*.rpm 1> /dev/null 2>&1; then
                                cp $component/last_successful/*.rpm "${CORTX_ISO_LOCATION}"
                            fi
                        done
                    popd

                    # Symlink 3rdparty repo artifacts
                    ln -s "${THIRD_PARTY_DEPS}" "${THIRD_PARTY_LOCATION}"
                        
                    # Symlink python dependencies
                    ln -s "${PYTHON_DEPS}" "${PYTHON_LIB_LOCATION}"
                '''

                sh label: 'RPM Signing', script: '''
                    pushd cortx-re/scripts/rpm-signing
                        cat gpgoptions >>  ~/.rpmmacros
                        sed -i 's/passphrase/'${PASSPHARASE}'/g' genkey-batch
                        gpg --batch --gen-key genkey-batch
                        gpg --export -a 'Seagate'  > RPM-GPG-KEY-Seagate
                        rpm --import RPM-GPG-KEY-Seagate
                    popd

                    pushd cortx-re/scripts/rpm-signing
                        chmod +x rpm-sign.sh
                        cp RPM-GPG-KEY-Seagate ${CORTX_ISO_LOCATION}
                        for rpm in `ls -1 ${CORTX_ISO_LOCATION}/*.rpm`
                        do
                            ./rpm-sign.sh ${PASSPHARASE} ${rpm}
                        done
                    popd

                '''
                
                sh label: 'RPM Signing', script: '''
                    pushd ${CORTX_ISO_LOCATION}
                        rpm -qi createrepo || yum install -y createrepo
                        createrepo .
                    popd
                '''	

                sh label: 'RPM Signing', script: '''
                    pushd cortx-re/scripts/release_support
                        sh build_readme.sh "${DESTINATION_RELEASE_LOCATION}"
                        sh build_release_info.sh -v ${VERSION} -l ${CORTX_ISO_LOCATION} -t ${THIRD_PARTY_LOCATION}
                    popd

                    cp "${THIRD_PARTY_LOCATION}/THIRD_PARTY_RELEASE.INFO" "${DESTINATION_RELEASE_LOCATION}"
                    cp "${CORTX_ISO_LOCATION}/RELEASE.INFO" "${DESTINATION_RELEASE_LOCATION}"
                    cp "${CORTX_ISO_LOCATION}/RELEASE.INFO" .
                '''	

                archiveArtifacts artifacts: "RELEASE.INFO", onlyIfSuccessful: false, allowEmptyArchive: true 	
            }

        }

        // Deploy Cortx-Stack
        stage('Deploy') {
            agent { 
                node { 
                    label params.HOST == "-" ? "vm_deployment_1n && !teardown_req" : "vm_deployment_1n_user_host"
                    customWorkspace "/var/jenkins/mini_provisioner/${JOB_NAME}_${BUILD_NUMBER}"
                } 
            }
            when { expression { env.STAGE_DEPLOY == "yes" } }
            environment {
                // Credentials used to SSH node
                NODE_DEFAULT_SSH_CRED =  credentials("${NODE_DEFAULT_SSH_CRED}")
                NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
                NODE1_HOST = "${HOST == '-' ? NODE1_HOST : HOST }"
                NODE_PASS = "${HOST_PASS == '-' ? NODE_DEFAULT_SSH_CRED_PSW : HOST_PASS}"

                NODE_UN_PASS_CRED_ID = "mini-prov-change-pass"
            }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {

                    // Cleanup Workspace
                    cleanWs()

                    markNodeforCleanup()

                    manager.addHtmlBadge("&emsp;<b>Deployment Host :</b><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'> ${NODE1_HOST}</a>&emsp;")

                    // Run Deployment
                    catchError {
                        
                        dir('cortx-re') {
                            checkout([$class: 'GitSCM', branches: [[name: '*/r2_vm_deployment']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 1, honorRefspec: true, noTags: true, reference: '', shallow: true], [$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                        }

                        runAnsible("00_PREPARE, 01_DEPLOY_PREREQ, 02_DEPLOY")

                    }

                    // Collect logs from test node
                    catchError {

                        sh label: 'download_log_files', returnStdout: true, script: """ 
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/log/seagate/provisioner/*.log . &>/dev/null || true
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx_configs/provisioner_cluster.json . &>/dev/null || true
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/root/config.ini . &>/dev/null || true
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/root/*.log . &>/dev/null || true
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/lib/hare/cluster.yaml . &>/dev/null || true
                        """
                        
                        archiveArtifacts artifacts: "*.log, *.json, *.ini, *.yaml", onlyIfSuccessful: false, allowEmptyArchive: true 
                    }

                    hctlStatus = ""
                    if ( fileExists('hctl_status.log') && currentBuild.currentResult == "SUCCESS" ) { 
                        hctlStatus = readFile(file: 'hctl_status.log')
                        MESSAGE = "Cortx Stack VM Deployment Success"
                        ICON = "accept.gif"
                        STATUS = "SUCCESS"
                    } else {
                        manager.buildFailure()
                        MESSAGE = "Cortx Stack VM Deployment Failed"
                        ICON = "error.gif"
                        STATUS = "FAILURE"
                    }

                    hctlStatusHTML = "<textarea rows=20 cols=200 readonly style='margin: 0px; height: 392px; width: 843px;'>${hctlStatus}</textarea>"
                    tableSummary = "<table border='1' cellspacing='0' cellpadding='0' width='400' align='left'> <tr> <td align='center'>Branch/Commit</td><td align='center'>${CSM_BRANCH}</td></tr><tr> <td align='center'>Deploy VM</td><td align='center'>${NODE1_HOST}</td></tr></table>"
                    manager.createSummary("${ICON}").appendText("<h3>${MESSAGE}.</h3><p>Please check <a href=\"${BUILD_URL}/artifact/setup.log\">setup.log</a> for more info <br /><br /><h4>Test Details:</h4> ${tableSummary} <br /><br /><br /><h4>Cluster Status:${hctlStatusHTML}</h4> ", false, false, false, "red")

                    if ( "${HOST}" == "-" ) {
                        if ( "${DEBUG}" == "yes" ) {  
                            markNodeOffline("Motr Debug Mode Enabled on This Host  - ${BUILD_URL}")
                        } else {
                            build job: 'Cortx-Automation/Deployment/VM-Teardown', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]                    
                        }
                    }

                    // Cleanup Workspace
                    cleanWs()
                }
            }
        }
	}

    post {
        always {
            sh label: 'Remove artifacts', script: '''rm -rf "${DESTINATION_RELEASE_LOCATION}"'''
        }
        failure {
            script {
                manager.addShortText("${build_stage} Failed")
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
    withCredentials([usernamePassword(credentialsId: "${NODE_UN_PASS_CRED_ID}", passwordVariable: 'SERVICE_PASS', usernameVariable: 'SERVICE_USER')]) {
        
        dir("cortx-re/scripts/deployment") {
            ansiblePlaybook(
                playbook: 'cortx_deploy_vm_1node.yml',
                inventory: 'inventories/vm_deployment/hosts_1node',
                tags: "${tags}",
                extraVars: [
                    "NODE1"                 : [value: "${NODE1_HOST}", hidden: false],
                    "BUILD_URL"             : [value: "${CORTX_BUILD}", hidden: false] ,
                    "CLUSTER_PASS"          : [value: "${NODE_PASS}", hidden: false],
                    "SERVICE_USER"          : [value: "${SERVICE_USER}", hidden: true],
                    "SERVICE_PASS"          : [value: "${SERVICE_PASS}", hidden: true],
                    "CHANGE_PASS"           : [value: "no", hidden: false]
                ],
                extras: '-v',
                colorized: true
            )
        }
    }
}
def markNodeforCleanup() {
	nodeLabel = "teardown_req"
    node = getCurrentNode(env.NODE_NAME)
	node.setLabelString(node.getLabelString() + " " + nodeLabel)
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

// Make failed node offline
def markNodeOffline(message) {
    node = getCurrentNode(env.NODE_NAME)
    computer = node.toComputer()
    computer.setTemporarilyOffline(true)
    computer.doChangeOfflineCause(message)
    computer = null
    node = null
}

def getBuild(buildURL) {

    buildID = sh(script: "curl -s  $buildURL/RELEASE.INFO  | grep BUILD | cut -d':' -f2 | tr -d '\"' | xargs", returnStdout: true).trim()
    buildbranch = "Build"
    if ( buildURL.contains("/cortx/github/main/") ) { 
        buildbranch="Main"
    } else if ( buildURL.contains("/cortx/github/stable/") ) { 
        buildbranch="Stable"
    } else if ( buildURL.contains("/cortx/github/integration-custom-ci/")) { 
        buildbranch="Custom-CI"
    } 

 return "$buildbranch#$buildID"   
}