#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}

    parameters {
        string(name: 'branch', defaultValue: 'main', description: 'Branch Name')
    }

	environment {
        version = "2.0.0"   
        env = "dev"
		component = "sspl"
        os_version = "centos-7.8.2003"
        pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

        // Param hack for initial config
        branch="${branch != null ? branch : 'main'}"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')  
        disableConcurrentBuilds()  
	}
	
	triggers {
        pollSCM 'H/5 * * * *'
    }

	stages {

        stage('Checkout') {
            steps {
                script { build_stage = env.STAGE_NAME }
                dir ('cortx-sspl') {
                    checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-monitor']]])
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: '', script: '''
					sed -i 's/gpgcheck=1/gpgcheck=0/' /etc/yum.conf
					yum-config-manager --disable cortx-C7.7.1908
					yum-config-manager --add http://cortx-storage.colo.seagate.com/releases/cortx/github/stable/$os_version/last_successful/
					yum-config-manager --add http://cortx-storage.colo.seagate.com/releases/cortx/components/github/main/$os_version/dev/cortx-utils/last_successful/
					yum clean all && rm -rf /var/cache/yum
                '''
            }
        }

        stage('Build') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Build', script: '''
                    set -xe
                    pushd cortx-sspl
                    VERSION=$(cat VERSION)
                    export build_number=${BUILD_ID}
                    #Execute build script
                    echo "Executing build script"
                    echo "VERSION:$VERSION"
                    ./jenkins/build.sh -v $version -l DEBUG
                    popd
                '''	
            }
        }
        
        stage ('Upload') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script: '''
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
                    cp /root/rpmbuild/RPMS/noarch/*.rpm $build_upload_dir/$BUILD_NUMBER
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
                sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
                    test -d $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
            }
        }

        stage ("Release") {
            //when { triggeredBy 'SCMTrigger' }
            steps {
                script { build_stage = env.STAGE_NAME }
				script {
                	def releaseBuild = build job: 'Main Release', propagate: true, parameters: [string(name: 'release_component', value: "${component}"), string(name: 'release_build', value: "${BUILD_NUMBER}")]
				 	env.release_build = "${BUILD_NUMBER}"
                    env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$pipeline_group/$os_version/${component}_${BUILD_NUMBER}"
				}
            }
        }

        stage ("Test") {
            when { expression { false } }
            steps {
                script { build_stage = env.STAGE_NAME }
				script {
                	build job: '../SSPL/SSPL_Build_Sanity', propagate: false, wait: false,  parameters: [string(name: 'TARGET_BUILD', value: "main:${component}_${BUILD_NUMBER}")]
				}
            }
        }  
	}

	post {
		always {
			script {
            	
				echo 'Cleanup Workspace.'
				deleteDir() /* clean up our workspace */

				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).toUpperCase()
				env.build_stage = "${build_stage}"

				def toEmail = ""
				def recipientProvidersClass = [[$class: 'DevelopersRecipientProvider']]
				if ( manager.build.result.toString() == "FAILURE") {
					toEmail = ""
					recipientProvidersClass = [[$class: 'DevelopersRecipientProvider'],[$class: 'RequesterRecipientProvider']]
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