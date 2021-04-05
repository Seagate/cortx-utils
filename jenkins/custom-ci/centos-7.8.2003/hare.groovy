#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}

	parameters {  
	    string(name: 'HARE_URL', defaultValue: 'https://github.com/Seagate/cortx-hare/', description: 'Repository URL for Hare build')
        string(name: 'HARE_BRANCH', defaultValue: 'stable', description: 'Branch for Hare build')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
		
		choice(
            name: 'MOTR_BRANCH', 
            choices: ['custom-ci', 'stable', 'Cortx-v1.0.0_Beta'],
            description: 'Branch name to pick-up other components rpms'
        )
	}
	

   	environment {
     	release_dir = "/mnt/bigstorage/releases/cortx"
		branch = "custom-ci"
		os_version = "centos-7.8.2003"
		component = "hare"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }
	
	
	
	options {
		timeout(time: 35, unit: 'MINUTES')
		timestamps() 
	}

	stages {
	
		stage('Checkout hare') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh 'mkdir -p hare'
				dir ('hare') {
					checkout([$class: 'GitSCM', branches: [[name: "${HARE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false, timeout: 15], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false, timeout: 15]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${HARE_URL}"]]])
				}
			}
		}
	
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Configure yum repositories', script: '''
					set +x
					yum-config-manager --disable cortx-C7.7.1908 motr_current_build
					yum-config-manager --add-repo=http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/$os_version/$release_tag/cortx_iso/
					yum-config-manager --save --setopt=cortx-storage*.gpgcheck=1 cortx-storage* && yum-config-manager --save --setopt=cortx-storage*.gpgcheck=0 cortx-storage*
					yum clean all;rm -rf /var/cache/yum
				'''	

				sh label: 'Install packages', script: '''	
					if [ "${HARE_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
						yum install eos-core{,-devel} -y
					else
						yum install cortx-py-utils cortx-motr{,-devel} -y
					fi
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', returnStatus: true, script: '''
					set -xe
					pushd $component
					echo "Executing build script"
					export build_number=${CUSTOM_CI_BUILD_ID}
					make rpm
					popd
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

	}
}