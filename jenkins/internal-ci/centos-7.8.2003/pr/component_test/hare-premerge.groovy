#!/usr/bin/env groovy
/*
 * Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * For any questions about this software or licensing,
 * please email opensource@seagate.com or cortx-questions@seagate.com.
 */
/*
 * Pipeline syntax: https://www.jenkins.io/doc/book/pipeline/syntax/
 * Groovy syntax: http://groovy-lang.org/syntax.html
 */
pipeline {
    agent { label 'docker-cp-centos-7.8.2003-node' }
    options {
        timeout(50)  // abort the build after that many minutes
        disableConcurrentBuilds()
        timestamps()
        ansiColor('xterm')  // XXX Delete if not useful.
        lock('hare-ci-vm')  // get exclusive access to the SSC VM
    }
     parameters {
        string(name: 'HARE_REPO', defaultValue: 'https://github.com/Seagate/cortx-hare', description: 'Repo to be used for Hare build.')
        string(name: 'HARE_BRANCH', defaultValue: 'main', description: 'Branch to be used for Hare build.')
    }
    environment {
        REPO_NAME = 'cortx-hare'
        // Updates :
        //   - Need new VM with clean state snapshot for HARE CI : https://jts.seagate.com/browse/EOS-18463
        VM_FQDN = 'ssc-vm-3370.colo.seagate.com' // SSC VM used for Hare CI 
        VM_CRED = credentials('node-user') // To connect SSC VM over SSH
        GITHUB_TOKEN = credentials('cortx-admin-github') // To clone cortx-hare repo
        GPR_REPO = "https://github.com/${ghprbGhRepository}"
        HARE_REPO = "${ghprbGhRepository != null ? GPR_REPO : HARE_REPO}"
        HARE_BRANCH = "${sha1 != null ? sha1 : HARE_BRANCH}"
        HARE_GPR_REFSPEC = "+refs/pull/${ghprbPullId}/*:refs/remotes/origin/pr/${ghprbPullId}/*"
        HARE_BRANCH_REFSPEC = "+refs/heads/*:refs/remotes/origin/*"
        HARE_PR_REFSPEC = "${ghprbPullId != null ? HARE_GPR_REFSPEC : HARE_BRANCH_REFSPEC}"
    }
    stages {
        stage('Prepare VM') {
            environment {
                SSC_AUTH = credentials('RE-CF-CRED') // To connect SSC CloudForm
            }
            steps {
                checkout([$class: 'GitSCM', branches: [[name: "${HARE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false,  timeout: 5], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${HARE_REPO}",  name: 'origin', refspec: "${HARE_PR_REFSPEC}"]]])
                //sh 'VERBOSE=true WAIT_TIMEOUT=40 jenkins/vm-reset'
                script {
                    def remote = getTestMachine(VM_FQDN)
                    def commandResult = sshCommand remote: remote, command: """
                        echo "Clean up VM before use"                         
                        yum remove cortx-hare cortx-motr{,-devel} cortx-py-utils consul -y 
                        rm -rf /var/crash/* /var/log/seagate/* /var/log/hare/* /var/log/motr/* /var/lib/hare/* /var/motr/* /etc/motr/*
                        rm -rf /root/.cache/dhall* /root/rpmbuild
                        rm -rf /etc/yum.repos.d/motr_last_successful.repo /etc/yum.repos.d/motr_uploads.repo /etc/yum.repos.d/lustre_release.repo
                        loop_devices=$(losetup -a | grep -o "/dev/loop[0-9]*")
                        [[ ! -z "$loop_devices" ]] && losetup -d $loop_devices
                        """
                        echo "Result: " + commandResult
                }    
            }
        }
        stage('Prepare environment') {
            parallel {
                stage('Download cortx-hare repo') {
                    steps {
                        script {
                            def repoURL = "${HARE_REPO}".replace("github.com", "$GITHUB_TOKEN@github.com")
                            def remote = getTestMachine(VM_FQDN)
                            def commandResult = sshCommand remote: remote, command: """
                            rm -rf $REPO_NAME
                            
                            git clone "$repoURL" "$REPO_NAME"
                            cd "${REPO_NAME}"
                            git fetch origin "${HARE_PR_REFSPEC}"
                            git checkout "${HARE_BRANCH}"
                            git log -1
                            ls -la
                            """
                            echo "Result: " + commandResult
                        }
                    }
                }
                stage('Prepare RPM dependencies') {
                    stages {
                        stage('Prepare repo files') {
                            steps {
                                script {
                                    def remote = getTestMachine(VM_FQDN)
                                    def commandResult = sshScript(
                                        remote: remote,
                                        script: "jenkins/prepare-yum-repos"
                                    )
                                    echo "Result: " + commandResult
                                }
                            }
                        }
                        // TODO: Revise when VM snapshot is ready
                        stage('Install Dependencies') {
                            steps {
                                script {
                                    def remote = getTestMachine(VM_FQDN)
                                    def commandResult = sshCommand remote: remote, command: """                                    
                                    yum install python3 python3-devel gcc rpm-build -y
                                    yum install cortx-py-utils -y
                                    yum install consul-1.9.1 -y
                                    yum install cortx-motr{,-devel} -y                                    
                                    """
                                    echo "Result: " + commandResult
                                }
                            }
                        }
                    }
                }
            }
        }
        stage('RPM test: build & install') {
            steps {
                script {
                    def remote = getTestMachine(VM_FQDN)
                    def commandResult = sshCommand remote: remote, command: """
                        cd "${REPO_NAME}"
                        make rpm
                        package_path=\$(find /root/rpmbuild/RPMS/x86_64/ | grep -E "cortx\\-hare\\-[0-9]+.*\\.rpm")
                        yum install -y \$package_path
                        """
                    echo "Result: " + commandResult
                }
            }
        }
        stage('Bootstrap singlenode') {
            options {
                timeout(time: 2, unit: 'MINUTES')
            }
            steps {
                script {
                    def remote = getTestMachine(VM_FQDN)
                    def commandResult = sshScript(
                        remote: remote,
                        script: "jenkins/bootstrap-singlenode"
                    )
                    echo "Result: " + commandResult
                }
            }
        }
        stage('Unit-tests') {
            steps {
                script {
                    def remote = getTestMachine(VM_FQDN)
                    def commandResult = sshCommand remote: remote, command: """
                        cd "${REPO_NAME}"
                        export PATH=/opt/seagate/cortx/hare/bin:\$PATH
                        make check
                        make test
                        """
                    echo "Result: " + commandResult
                }
            }
        }
        stage('Stop cluster') {
            options {
                timeout(time: 10, unit: 'MINUTES')
            }
            steps {
                script {
                    def remote = getTestMachine(VM_FQDN)
                    def commandResult = sshCommand remote: remote, command: """
                        PATH=/opt/seagate/cortx/hare/bin/:\$PATH
                        hctl shutdown
                        """
                    echo "Result: " + commandResult
                }
            }
        }
        stage('I/O test with m0crate') {
            options {
                timeout(time: 15, unit: 'MINUTES')
            }
            steps {
                script {
                    def remote = getTestMachine(VM_FQDN)
                    // sshScript does not work in this case for unknown reason
                    def commandResult = sshCommand remote: remote, command: """
                        cd "${REPO_NAME}"
                        jenkins/test-boot1
                        """
                    echo "Result: " + commandResult
                }
            }
        }
        // NOTE: Add here new stages with tests if needed
    }
    post {
        always {
            script {
                echo 'Cleanup Workspace.'
                cleanWs() /* clean up workspace */
            }
        }
    }        
}
// Method returns VM Host Information ( host, ssh cred)
def getTestMachine(String host) {
    def remote = [:]
    remote.name = 'cortx-vm-name'
    remote.host = host
    remote.user =  VM_CRED_USR
    remote.password = VM_CRED_PSW
    remote.allowAnyHosts = true
    remote.fileTransfer = 'scp'
    return remote
}