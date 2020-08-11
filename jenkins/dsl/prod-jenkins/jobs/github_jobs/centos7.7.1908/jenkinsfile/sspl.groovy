#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-rhel7.7-sspl-github-node'
		}
	}

	environment {   
        env="dev"
		component="sspl"
        branch="github"
        os_version="rhel-7.7.1908"
        release_dir="/mnt/bigstorage/releases/eos"
        build_upload_dir="$release_dir/components/$branch/$os_version/$env/$component/"
    }

	options {
		timeout(time: 30, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')  
        disableConcurrentBuilds()  
	}

	stages {
        stage('Checkout') {
            steps {
                script { build_stage=env.STAGE_NAME }
                dir ('sspl') {
                    git credentialsId: 'github-shailesh-ssh', url: 'git@github.com:Seagate/sspl.git'
                }
            }
        }
        
        stage('Install Dependencies') {
            steps {
                script { build_stage=env.STAGE_NAME }
                sh label: '', script: '''
                    yum install sudo python-Levenshtein libtool doxygen python-pep8 openssl-devel graphviz check-devel -y
                '''
            }
        }

        stage('Build') {
            steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Build', returnStatus: true, script: '''
                    set -xe
                    pushd sspl
                    VERSION=$(cat VERSION)
                    export build_number=${BUILD_ID}
                    #Execute build script
                    echo "Executing build script"
                    echo "VERSION:$VERSION"
                    ./jenkins/build.sh -l DEBUG
                    popd
                '''	
            }
        }
        
        stage ('Upload') {
            steps {
                script { build_stage=env.STAGE_NAME }
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