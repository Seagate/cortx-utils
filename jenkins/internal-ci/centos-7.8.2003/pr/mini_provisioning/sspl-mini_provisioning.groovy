#!/usr/bin/env groovy

pipeline {

    agent {
        node {
            // Run deployment on mini_provisioner nodes (vm deployment nodes)
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
        string(name: 'SSPL_URL', defaultValue: 'https://github.com/Seagate/cortx-monitor', description: 'Repo for SSPL')
        string(name: 'SSPL_BRANCH', defaultValue: 'main', description: 'Branch for SSPL')
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: 'Keep Host for Debuging')
        string(name: 'HOST', defaultValue: '-', description: 'Host FQDN',  trim: true)
        password(name: 'HOST_PASS', defaultValue: '-', description: 'Host machine root user password')
    }

    environment {

        COMPONENT_NAME = "sspl".trim()
        OS_VERSION = "centos-7.8.2003"
        GPR_REPO = "https://github.com/${ghprbGhRepository}"
        SSPL_URL = "${ghprbGhRepository != null ? GPR_REPO : SSPL_URL}"
        SSPL_BRANCH = "${sha1 != null ? sha1 : SSPL_BRANCH}"

        SSPL_GPR_REFSEPEC = "+refs/pull/${ghprbPullId}/*:refs/remotes/origin/pr/${ghprbPullId}/*"
        SSPL_BRANCH_REFSEPEC = "+refs/heads/*:refs/remotes/origin/*"
        SSPL_PR_REFSEPEC = "${ghprbPullId != null ? SSPL_GPR_REFSEPEC : SSPL_BRANCH_REFSEPEC}"
		
		BRANCH = "main"
		THIRD_PARTY_VERSION = "centos-7.8.2003-2.0.0-latest"
		VERSION = "2.0.0"
        PASSPHARASE = credentials('rpm-sign-passphrase')
		
        ////////////////////////////////// DEPLOYMENT VARS /////////////////////////////////////////////////////
        DESTINATION_RELEASE_LOCATION = "/mnt/bigstorage/releases/cortx/github/pr-build/${COMPONENT_NAME}/${BUILD_NUMBER}"
        PYTHON_DEPS = "/mnt/bigstorage/releases/cortx/third-party-deps/python-deps/python-packages-2.0.0-latest"
        THIRD_PARTY_DEPS = "/mnt/bigstorage/releases/cortx/third-party-deps/centos/${THIRD_PARTY_VERSION}/"
        COMPONENTS_RPM = "/mnt/bigstorage/releases/cortx/components/github/${BRANCH}/${OS_VERSION}/dev/"
        CORTX_BUILD = "http://cortx-storage.colo.seagate.com/releases/cortx/github/pr-build/${COMPONENT_NAME}/${BUILD_NUMBER}"

        // Artifacts location
        CORTX_ISO_LOCATION = "${DESTINATION_RELEASE_LOCATION}/cortx_iso"
        THIRD_PARTY_LOCATION = "${DESTINATION_RELEASE_LOCATION}/3rd_party"
        PYTHON_LIB_LOCATION = "${DESTINATION_RELEASE_LOCATION}/python_deps"
        STAGE_DEPLOY = "yes"
       
    }

    stages {

        // Build SSPL from PR source code
        stage('Build') {
            steps {
                
                script { build_stage = env.STAGE_NAME }

                dir("cortx-monitor") {

                    checkout([$class: 'GitSCM', branches: [[name: "${SSPL_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false], [$class: 'CloneOption', depth: 1, honorRefspec: true, noTags: true, reference: '', shallow: true]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${SSPL_URL}",  name: 'origin', refspec: "${SSPL_PR_REFSEPEC}"]]])

                    sh label: '', script: '''
                        rm -rf /root/SSPL_RPMS
                        rm -rf /root/*.html
                        yum install -y autoconf automake libtool check-devel doxygen rpm-build gcc openssl-devel graphviz python-pep8 python36-devel libffi-devel
                        sed -i 's/gpgcheck=1/gpgcheck=0/' /etc/yum.conf
                    '''
                    sh label: 'Build', script: '''
                        VERSION=$(cat VERSION)
                        export build_number=${BUILD_ID}
                        #Execute build script
                        echo "Executing build script"
                        echo "VERSION:$VERSION"
                        ./jenkins/build.sh -v $VERSION -l DEBUG
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
                    yum install -y expect rpm-sign rng-tools genisoimage python3-pip
                    systemctl start rngd
                '''

                // Integrate components rpms
                sh label: 'Collect Release Artifacts', script: '''

                    rm -rf "${DESTINATION_RELEASE_LOCATION}"
                    mkdir -p "${DESTINATION_RELEASE_LOCATION}"

                    if [[ ( ! -z `ls /root/rpmbuild/RPMS/x86_64/*.rpm `)]]; then
                        mkdir -p "${CORTX_ISO_LOCATION}"
                        cp /root/rpmbuild/RPMS/x86_64/*.rpm "${CORTX_ISO_LOCATION}"
                        cp /root/rpmbuild/RPMS/noarch/*.rpm "${CORTX_ISO_LOCATION}"
                    else
                        echo "RPM not exists !!!"
                        exit 1
                    fi

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

                sh label: 'Create Repo', script: '''
                    pushd ${CORTX_ISO_LOCATION}
                        rpm -qi createrepo || yum install -y createrepo
                        createrepo .
                    popd
                '''

                sh label: 'Release info generation', script: '''
                    pushd cortx-re/scripts/release_support
                        sh build_release_info.sh -v ${VERSION} -l ${CORTX_ISO_LOCATION} -t ${THIRD_PARTY_LOCATION}
                        sh build_readme.sh "${DESTINATION_RELEASE_LOCATION}"
                    popd

                    cp "${THIRD_PARTY_LOCATION}/THIRD_PARTY_RELEASE.INFO" "${DESTINATION_RELEASE_LOCATION}"
                    cp "${CORTX_ISO_LOCATION}/RELEASE.INFO" "${DESTINATION_RELEASE_LOCATION}"
                '''
            }

        }

        // Deploy SSPL mini provisioner
        stage('Deploy') {
            when { expression { env.STAGE_DEPLOY == "yes" } }
            agent {
                node {
                    // Run deployment on mini_provisioner nodes (vm deployment nodes)
                    label params.HOST == "-" ? "mini_provisioner && !cleanup_req" : "mini_provisioner_user_host"
                    customWorkspace "/var/jenkins/mini_provisioner/${JOB_NAME}_${BUILD_NUMBER}"
                }
            }
            environment {
                // Credentials used to SSH node
                NODE_DEFAULT_SSH_CRED =  credentials("${NODE_DEFAULT_SSH_CRED}")
                NODE_USER = "${NODE_DEFAULT_SSH_CRED_USR}"
                NODE1_HOST = "${HOST == '-' ? NODE1_HOST : HOST }"
                NODE_PASS = "${HOST_PASS == '-' ? NODE_DEFAULT_SSH_CRED_PSW : HOST_PASS}"
            }
            steps {
                script { build_stage = env.STAGE_NAME }
                script {

                    // Cleanup Workspace
                    cleanWs()

                    if ( "${HOST}" == "-" ) {
                        markNodeforCleanup()
                    }
                    manager.addHtmlBadge("&emsp;<b>Deployment Host :</b><a href='${JENKINS_URL}/computer/${env.NODE_NAME}'> ${NODE1_HOST}</a>&emsp;")

                    // Run Deployment
                    catchError {

                        dir('cortx-re') {
                            checkout([$class: 'GitSCM', branches: [[name: '*/mini-provisioner-dev']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 1, honorRefspec: true, noTags: true, reference: '', shallow: true], [$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                        }

                        runAnsible("00_PREP_ENV, 01_PREREQ, 02_MINI_PROV, 03_START_SSPL, 04_VALIDATE")

                    }

                     // Collect logs from test node
                    catchError {

                            // Download deployment log files from deployment node
                            try {
                                sh label: 'download_log_files', returnStdout: true, script: """ 
                                    mkdir -p artifacts
                                    sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx/sspl/conf/*1-node artifacts/ || true
                                """
                            } catch (err) {
                                echo err.getMessage()
                            }

                            archiveArtifacts artifacts: "artifacts/*", onlyIfSuccessful: false, allowEmptyArchive: true 
                    }

                    // Trigger cleanup VM
                    if ( "${HOST}" == "-" ) {
                        if ( "${DEBUG}" == "yes" ) {
                            markNodeOffline("Debug Mode Enabled on This Host  - ${BUILD_URL}")
                        } else {
                            build job: 'Cortx-Automation/Deployment/VM-Cleanup', wait: false, parameters: [string(name: 'NODE_LABEL', value: "${env.NODE_NAME}")]       
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
            script  {
                sh label: 'Delete Old Builds', script: '''
                    set +x
                    find /mnt/bigstorage/releases/cortx/github/pr-build/${COMPONENT_NAME}/* -maxdepth 0 -mtime +30 -type d -exec rm -rf {} \\;
                '''
            }
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

    dir("cortx-re/scripts/mini_provisioner") {

        ansiblePlaybook(
            playbook: 'sspl_deploy.yml',
            inventory: 'inventories/hosts',
            tags: "${tags}",
            extraVars: [
                "NODE1"                 : [value: "${NODE1_HOST}", hidden: false],
                "CORTX_BUILD"           : [value: "${CORTX_BUILD}", hidden: false] ,
                "CLUSTER_PASS"          : [value: "${NODE_PASS}", hidden: false]            ],
            extras: '-v',
            colorized: true
        )
    }
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