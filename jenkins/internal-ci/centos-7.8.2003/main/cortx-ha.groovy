#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}

	parameters {
        string(name: 'branch', defaultValue: 'main', description: 'Branch Name')
    }
    
    environment {
        version = "2.0.0"
        env = "dev"
		component = "cortx-ha"
        os_version = "centos-7.8.2003"
		pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
		build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

		// Param hack for initial config
        branch = "${branch != null ? branch : 'main'}"
    }
	
	options {
		timeout(time: 35, unit: 'MINUTES')
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
				dir ('cortx-ha') {
					checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-ha']]])
				}   
			}
		}
	
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: '', script: '''
					pushd $component
					yum clean all;rm -rf /var/cache/yum
				    yum erase python36-PyYAML -y
					bash jenkins/cicd/cortx-ha-dep.sh
					pip3 install numpy
					popd
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', script: '''
					set -xe
					pushd $component
					echo "Executing build script"
   				   ./jenkins/build.sh -v $version -b $BUILD_NUMBER
					popd
				'''	
			}
		}
		
		stage('Test') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Test', script: '''
					set -xe
					pushd $component
					yum localinstall $WORKSPACE/$component/dist/rpmbuild/RPMS/x86_64/cortx-ha-*.rpm -y
					bash jenkins/cicd/cortx-ha-cicd.sh
					popd
				'''	
			}
		}

        stage ('Upload') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp $WORKSPACE/cortx-ha/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
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
					toEmail = "CORTX.HA@seagate.com,shailesh.vaidya@seagate.com"
					
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