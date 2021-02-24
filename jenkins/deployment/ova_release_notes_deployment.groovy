#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            label 'docker-io-centos-7.8.2003-node'
        }  
    }
    parameters {  
        string(name: 'OVA_BUILD', defaultValue: "21", description: 'OVA build number')
        string(name: 'GITHUB_RELEASE', defaultValue: "", description: 'GitHub release number')
        string(name: 'SOURCE_BUILD', defaultValue: "531", description: 'Source cortx build number')
        string(name: 'TARGET_BUILD', defaultValue: "571", description: 'Target cortx build number')
	}
	environment {
	    GITHUB_TOKEN = credentials('generic-github-token')
	}    
	options {
        timestamps()
        ansiColor('xterm') 
        buildDiscarder(logRotator(numToKeepStr: "30"))
    }
    stages {
        stage('Checkout') {
            steps {
                script {
                        
                            checkout([$class: 'GitSCM', 
                                branches: [[name: '*/main']], 
                                doGenerateSubmoduleConfigurations: false, 
                                extensions: [], 
                                submoduleCfg: [], 
                                userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re.git']]
                    
                            ])
                            sh label: '', script: '''
                                sed -i 's/gpgcheck=1/gpgcheck=0/' /etc/yum.conf
                                python3 --version
                                pip3 install jira githubrelease
                            '''
                        
                }    
            }
        }
        stage('Execute Script') {
            steps {
                dir("scripts/release_support/ova-release-notes") {
                    withCredentials([usernamePassword(credentialsId: 'jira-token', passwordVariable: 'VM_PASS', usernameVariable: 'VM_USER')]) {
                        sh"python3 ova_release.py -u ${VM_USER} -p ${VM_PASS} --build ${OVA_BUILD} --release ${GITHUB_RELEASE} --sourceBuild ${SOURCE_BUILD} --targetBuild ${TARGET_BUILD}"
                    }
                }    
            }
        }
    }
}
