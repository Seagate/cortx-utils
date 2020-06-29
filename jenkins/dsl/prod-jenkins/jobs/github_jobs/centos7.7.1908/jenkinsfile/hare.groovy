#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-rhel7.7-hare-github-node'
		}
	}
    
    environment {
        env="dev"
		component="hare"
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
				dir ('hare') {
					checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'github-shailesh-ssh', url: 'git@github.com:Seagate/hare.git']]])
				}
			}
		}

        stage("Set Mero Build"){
            when { not { triggeredBy 'UpstreamCause' } }
            steps {
                script { build_stage=env.STAGE_NAME }
                script {
                    sh label: '', script: '''
                        sed '/baseurl/d' /etc/yum.repos.d/mero_current_build.repo
                        echo "baseurl=http://ci-storage.mero.colo.seagate.com/releases/eos/components/dev/centos-7.7.1908/mero/last_successful/"  >> /etc/yum.repos.d/mero_current_build.repo
                        rm -f /etc/yum.repos.d/eos_7.7.1908.repo
                        yum clean all;rm -rf /var/cache/yum
                    '''
                }
            }
        }
	
		stage('Install Dependencies') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: '', script: '''
					yum clean all
					rm -rf /var/cache/yum
					yum install eos-core{,-devel} -y
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: 'Build', returnStatus: true, script: '''
					set -xe
					pushd $component
					echo "Executing build script"
					export build_number=${BUILD_ID}
					make rpm
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
				'''
                sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
					rpm -qi createrepo || yum install -y createrepo
					createrepo .
					popd
				'''

			}
		}
			
		stage ('Tag last_successful') {
            when { not { triggeredBy 'UpstreamCause' } }
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
                    env.release_build_location="http://ci-storage.mero.colo.seagate.com/releases/eos/$branch/$os_version/"+releaseBuild.number
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

