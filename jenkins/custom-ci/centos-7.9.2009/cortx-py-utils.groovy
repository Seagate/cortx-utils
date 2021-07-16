#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-centos-7.9.2009-node'
		}
	}

	parameters {  
	    string(name: 'CORTX_UTILS_URL', defaultValue: 'https://github.com/Seagate/cortx-utils', description: 'Repository URL for cortx-py-utils build')
        string(name: 'CORTX_UTILS_BRANCH', defaultValue: 'stable', description: 'Branch for cortx-py-utils build')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
	}
	

   	environment {
     	release_dir = "/mnt/bigstorage/releases/cortx"
        version = "2.0.0"
		branch = "custom-ci"
		os_version = "centos-7.9.2009"
		component = "hare"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }
	
	
	
	options {
		timeout(time: 35, unit: 'MINUTES')
		timestamps() 
	}

	stages {
	
		stage('Checkout py-utils') {
			steps {
                script { build_stage = env.STAGE_NAME }
                checkout([$class: 'GitSCM', branches: [[name: "${CORTX_UTILS_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CORTX_UTILS_URL}"]]])
			}
		}
	
		stage('Build') {
			steps {
                script { build_stage = env.STAGE_NAME }
				sh label: 'Build', script: '''
				yum install python36-devel -y
				pushd py-utils
                        ../jenkins/build.sh -v $version -b $BUILD_NUMBER
                popd
				./statsd-utils/jenkins/build.sh -v $version -b $BUILD_NUMBER
	        '''	
			}
		}	

        stage ('Copy RPMS') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir
                    shopt -s extglob
					cp ./py-utils/dist/!(*.src.rpm|*.tar.gz) $build_upload_dir
                    cp ./statsd-utils/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir
					createrepo -v --update $build_upload_dir
				'''
			}
		}

	}
}