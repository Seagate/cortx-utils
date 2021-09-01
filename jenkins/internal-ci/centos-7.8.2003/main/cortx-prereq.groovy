#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
           label 'cortx-prereq-validation'
        }
    }
    
    environment {
        version = "2.0.0"
        env = "dev"
        component = "cortx-prereq"
        branch = "main"
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "$release_dir/components/github/$branch/$os_version/$env/$component"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        disableConcurrentBuilds()   
    }
    
    triggers {
        pollSCM '*/5 * * * *'
    }

    stages {
    
        stage('Prerequisite') {
            steps {
                sh encoding: 'utf-8', label: 'Install Prerequisite Packages', script: """
                    yum erase cortx-prereq -y
                    yum install rpm-build rpmdevtools -y 
                    rpmdev-setuptree        
                """
            }
        }
    
        stage('Checkout') {
            steps {
                script { build_stage = env.STAGE_NAME }
                checkout([$class: 'GitSCM', branches: [[name: "${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'PathRestriction', excludedRegions: '', includedRegions: 'scripts/third-party-rpm/.*']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
            }
        }

        stage('Build') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh encoding: 'utf-8', label: 'Build cortx-prereq package', script: """
                    pushd ./scripts/third-party-rpm
                        sh ./build-prerequisite-rpm.sh -v $version -r ${BUILD_NUMBER} -g \$(git rev-parse --short HEAD)
                    popd    
                """
            }
        }

        stage('Test') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh encoding: 'utf-8', label: 'Test cortx-prereq package', script: """
                pushd ./scripts/third-party-rpm
                      sh ./install-cortx-prereq.sh -b "http://cortx-storage.colo.seagate.com/releases/cortx/github/$branch/$os_version/last_successful_prod/" -r local
                popd  
                """
            }
        }

        stage ('Upload') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script: '''
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
                '''
                sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
            }
        }
            
        stage ('Tag last_successful') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Clean-up', script: '''
                    pushd $build_upload_dir/
                    test -d $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
            }
        }
    }
    
    post {
    
        always {
                sh label: 'Clean-up', script: '''
                set +x
                rm -rf /etc/yum.repos.d/cortx-storage.colo.seagate.com* /etc/pip.conf /root/rpmbuild/RPMS/x86_64/*.rpm
                if [ -f /opt/seagate/cortx/python-deps/python-requirements.txt ]; then
                    pip3 uninstall -r /opt/seagate/cortx/python-deps/python-requirements.txt -y
                fi
                yum erase cortx-prereq -y
                '''
                script {

                env.release_build = (env.release_build != null) ? env.release_build : "" 
                env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
                env.component = (env.component).toUpperCase()
                env.build_stage = "${build_stage}"

                def toEmail = ""
                def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
                if ( manager.build.result.toString() == "FAILURE") {
                    toEmail = "shailesh.vaidya@seagate.com"
                    recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
                }
                emailext (
                    body: '''${SCRIPT, template="component-email.template"}''',
                    mimeType: 'text/html',
                    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
                    attachLog: true,
                    to: toEmail,
                    recipientProviders: recipientProvidersClass
                )
            } 
        }
    }
}