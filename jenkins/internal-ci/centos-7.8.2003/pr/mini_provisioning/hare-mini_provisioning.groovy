#!/usr/bin/env groovy
// CLEANUP REQUIRED
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
	    string(name: 'HARE_URL', defaultValue: 'https://github.com/Seagate/cortx-hare', description: 'Repo for Hare')
        string(name: 'HARE_BRANCH', defaultValue: 'main', description: 'Branch for Hare')
        choice(name: 'DEBUG', choices: ["no", "yes" ], description: 'Keep Host for Debuging')   
        string(name: 'HOST', defaultValue: '-', description: 'Host FQDN',  trim: true)
        password(name: 'HOST_PASS', defaultValue: '-', description: 'Host machine root user password')
    }

    environment {

        // Hare Repo Info

        GPR_REPO = "https://github.com/${ghprbGhRepository}"
        HARE_URL = "${ghprbGhRepository != null ? GPR_REPO : HARE_URL}"
        HARE_BRANCH = "${sha1 != null ? sha1 : HARE_BRANCH}"

        HARE_GPR_REFSPEC = "+refs/pull/${ghprbPullId}/*:refs/remotes/origin/pr/${ghprbPullId}/*"
        HARE_BRANCH_REFSEPEC = "+refs/heads/*:refs/remotes/origin/*"
        HARE_PR_REFSPEC = "${ghprbPullId != null ? HARE_GPR_REFSPEC : HARE_BRANCH_REFSEPEC}"

        //////////////////////////////// BUILD VARS //////////////////////////////////////////////////

        COMPONENT_NAME = "hare".trim()
        BRANCH = "main"
        OS_VERSION = "centos-7.8.2003"
        THIRD_PARTY_VERSION = "centos-7.8.2003-2.0.0-latest"
        VERSION = "2.0.0"
        PASSPHARASE = credentials('rpm-sign-passphrase')

        // Artifacts root location

        // 'WARNING' - rm -rf command used on this path please careful when updating this value
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

        // Build hare fromm PR source code
        stage('Build') {
            steps {
				script { build_stage = env.STAGE_NAME }
                 
                dir("hare") {

                    checkout([$class: 'GitSCM', branches: [[name: "${HARE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false, timeout: 15], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false, timeout: 15]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${HARE_URL}",  name: 'origin', refspec: "${HARE_PR_REFSPEC}"]]])
                    sh label: '', script: '''
					yum erase python36-PyYAML -y
                    cat <<EOF >>/etc/pip.conf
[global]
timeout: 60
index-url: http://cortx-storage.colo.seagate.com/releases/cortx/third-party-deps/python-deps/python-packages-2.0.0-latest/
trusted-host: cortx-storage.colo.seagate.com
EOF
					pip3 install -r https://raw.githubusercontent.com/Seagate/cortx-utils/$BRANCH/py-utils/python_requirements.txt
					rm -rf /etc/pip.conf
                    '''
                    
                    
                    sh label: 'prepare build env', script: """
                        sed '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
                        echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/${BRANCH}/${OS_VERSION}/dev/motr/current_build/"  >> /etc/yum.repos.d/motr_current_build.repo
                        yum clean all;rm -rf /var/cache/yum
                        yum install cortx-py-utils cortx-motr{,-devel} -y
                    """

                    sh label: 'Build', script: '''
                        set -xe
                        echo "Executing build script"
                        export build_number=${BUILD_NUMBER}
                        make VERSION=$VERSION rpm
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
                '''		
            }

        }

        // Ref - https://github.com/Seagate/cortx-hare/wiki/Hare-provisioning
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
                            checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 1, honorRefspec: true, noTags: true, reference: '', shallow: true], [$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                        }

                        runAnsible("00_PREP_ENV, 01_PREREQ, 02_MINI_PROV, 04_VALIDATE")

                    }

                    // Collect logs from test node
                    catchError {

                        sh label: 'download_log_files', returnStdout: true, script: """ 
                            mkdir -p artifacts
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/opt/seagate/cortx/hare/conf/*1-node artifacts/ || true
                            sshpass -p '${NODE_PASS}' scp -r -o StrictHostKeyChecking=no ${NODE_USER}@${NODE1_HOST}:/var/lib/hare/cluster.yaml artifacts/ || true
                        """
                        
                        archiveArtifacts artifacts: "artifacts/*", onlyIfSuccessful: false, allowEmptyArchive: true  
                    }

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
            sh label: 'Delete Old Builds', script: '''
                set +x
                find /mnt/bigstorage/releases/cortx/github/pr-build/${COMPONENT_NAME}/* -maxdepth 0 -mtime +30 -type d -exec rm -rf {} \\;
            '''
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
            playbook: 'hare_deploy.yml',
            inventory: 'inventories/hosts',
            tags: "${tags}",
            extraVars: [
                "NODE1"                 : [value: "${NODE1_HOST}", hidden: false],
                "CORTX_BUILD"           : [value: "${CORTX_BUILD}", hidden: false] ,
                "CLUSTER_PASS"          : [value: "${NODE_PASS}", hidden: false]
            ],
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