#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}
    
    environment {
		component = "cortx-ha"
        branch = "custom-ci" 
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"

    }
	
	parameters {
		string(name: 'HA_URL', defaultValue: 'https://github.com/Seagate/cortx-ha', description: 'Repository URL to be used for cortx-ha build.')
		string(name: 'HA_BRANCH', defaultValue: 'stable', description: 'Branch to be used for cortx-ha build.')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
	}
	
	
	options {
		timeout(time: 35, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')  
	}

	stages {
		stage('Checkout') {
			steps {
				script { build_stage = env.STAGE_NAME }
				dir ('cortx-ha') {
					checkout([$class: 'GitSCM', branches: [[name: "$HA_BRANCH"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "$HA_URL"]]])
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
   				   ./jenkins/build.sh -b $CUSTOM_CI_BUILD_ID
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
					mkdir -p $build_upload_dir
					cp $WORKSPACE/cortx-ha/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir
					createrepo -v --update $build_upload_dir
				'''
			}
		}
	}
}