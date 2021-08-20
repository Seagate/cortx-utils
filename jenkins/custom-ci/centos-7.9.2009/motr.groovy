#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-centos-7.9.2009-node'
		}
	}

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps()
		buildDiscarder(logRotator(daysToKeepStr: '5', numToKeepStr: '10'))
		parallelsAlwaysFailFast()
	}
	

	parameters {  
        string(name: 'MOTR_URL', defaultValue: 'https://github.com/Seagate/cortx-motr', description: 'Branch for Motr.')
		string(name: 'MOTR_BRANCH', defaultValue: 'stable', description: 'Branch for Motr.')
		string(name: 'S3_URL', defaultValue: 'https://github.com/Seagate/cortx-s3server', description: 'Branch for S3Server')
		string(name: 'S3_BRANCH', defaultValue: 'stable', description: 'Branch for S3Server')
		string(name: 'HARE_URL', defaultValue: 'https://github.com/Seagate/cortx-hare', description: 'Branch to be used for Hare build.')
		string(name: 'HARE_BRANCH', defaultValue: 'stable', description: 'Branch to be used for Hare build.')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')

	}	

	environment {
     	release_dir = "/mnt/bigstorage/releases/cortx"
		os_version = "centos-7.9.2009"
		branch = "custom-ci"
		component = "motr"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }

	stages {	
	
		stage('Checkout') {
			steps {
                step([$class: 'WsCleanup'])
				checkout([$class: 'GitSCM', branches: [[name: "$MOTR_BRANCH"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "$MOTR_URL"]]])
			}
		}
	
	
	stage('Install Dependencies') {
		    steps {
				script { build_stage = env.STAGE_NAME }
				sh label: '', script: '''
						export build_number=${BUILD_ID}
						kernel_src=$(ls -1rd /lib/modules/*/build | head -n1)
						
						cp cortx-motr.spec.in cortx-motr.spec
						sed -i 's/@.*@/111/g' cortx-motr.spec
						yum-builddep -y cortx-motr.spec
					'''	
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
						sh label: '', script: '''
						rm -rf /root/rpmbuild/RPMS/x86_64/*.rpm
						KERNEL=/lib/modules/$(yum list installed kernel | tail -n1 | awk '{ print $2 }').x86_64/build
						./autogen.sh
						./configure --with-linux=$KERNEL
						export build_number=${CUSTOM_CI_BUILD_ID}
						make rpms
					'''
			}
		}
		
		stage ('Copy RPMS') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir
					cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir
					createrepo -v --update $build_upload_dir
				'''
			}
		}
	
		stage ("Trigger Downstream Jobs") {
			parallel {
				stage ("build S3Server") {
					steps {
						script { build_stage = env.STAGE_NAME }
						build job: 's3-custom-build', wait: true,
						parameters: [
									string(name: 'S3_BRANCH', value: "${S3_BRANCH}"),
									string(name: 'MOTR_BRANCH', value: "custom-ci"),
									string(name: 'S3_URL', value: "${S3_URL}"),
									string(name: 'CUSTOM_CI_BUILD_ID', value: "${CUSTOM_CI_BUILD_ID}")
								]
					}
				}

				stage ("build Hare") {
					steps {
						script { build_stage = env.STAGE_NAME }
						build job: 'hare-custom-build', wait: true,
						parameters: [
									string(name: 'HARE_BRANCH', value: "${HARE_BRANCH}"),
									string(name: 'MOTR_BRANCH', value: "custom-ci"),
									string(name: 'HARE_URL', value: "${HARE_URL}"),
									string(name: 'CUSTOM_CI_BUILD_ID', value: "${CUSTOM_CI_BUILD_ID}")
								]
					}
				}
			}	
		}
	}	
}