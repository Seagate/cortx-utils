#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-rhel7.7-hare-github-node'
		}
	}
    
    environment {
        env="dev"
		component="cortx-ha"
        branch="github"
        os_version="rhel-7.7.1908"
        release_dir="/mnt/bigstorage/releases/eos"
        build_upload_dir="$release_dir/components/$branch/$os_version/$env/$component/"
    }
	
	options {
		timeout(time: 35, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')
		disableConcurrentBuilds()  
	}

	stages {
		stage('Checkout') {
			steps {
				script { build_stage=env.STAGE_NAME }
				dir ('cortx-ha') {
					checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'github-shailesh-ssh', url: 'ssh://git@github.com:Seagate/cortx-ha.git']]])
				}
			}
		}
	
		stage('Install Dependencies') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: '', script: '''
					pushd $component
					yum clean all;rm -rf /var/cache/yum
					yum -q erase eos-py-utils -y;yum install eos-py-utils -y
					bash jenkins/cicd/cortx-ha-dep.sh
					pip3 install numpy
					popd
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: 'Build', script: '''
					set -xe
					pushd $component
					echo "Executing build script"
   				   ./jenkins/build.sh -b $BUILD_NUMBER
					popd
				'''	
			}
		}
		
		stage('Test') {
			steps {
				script { build_stage=env.STAGE_NAME }
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
				script { build_stage=env.STAGE_NAME }
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
				script { build_stage=env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
					test -d $build_upload_dir/last_successful && rm -f last_successful
					ln -s $build_upload_dir/$BUILD_NUMBER last_successful
					popd
				'''
			}
		}

		stage ("Release") {
            steps {
                script { build_stage=env.STAGE_NAME }
				script {
                	def releaseBuild = build job: 'GitHub Release', propagate: false
				 	env.release_build = releaseBuild.number
                    env.release_build_location="http://cortx-storage.colo.seagate.com/releases/eos/$branch/$os_version/"+releaseBuild.number
				}
            }
        } 
	}
	
	post {
		always{                
			script{
				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).capitalize()
				env.build_stage = "${build_stage}"

				def toEmail = "gowthaman.chinnathambi@seagate.com"
				emailext (
					body: '''${SCRIPT, template="component-email.template"}''',
					mimeType: 'text/html',
					subject: "${env.JOB_BASE_NAME} GitHub Build ${currentBuild.currentResult}",
					attachLog: true,
					to: toEmail,
				)
			}
		}
	}
}	