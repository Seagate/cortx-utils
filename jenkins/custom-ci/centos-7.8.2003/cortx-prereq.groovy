#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
           label 'docker-cp-centos-7.8.2003-node'
        }
    }
	
	environment { 
		component = "csm-agent"
        branch = "custom-ci" 
        os_version = "centos-7.8.2003"
        version = "2.0.0"
        release_dir = "/mnt/bigstorage/releases/cortx"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }

    options {
        timeout(time: 120, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm') 
        disableConcurrentBuilds()   
    }

    parameters {  
        string(name: 'CORTX_RE_URL', defaultValue: 'https://github.com/Seagate/cortx-re.git', description: 'Repository URL for cortx-prereq build.')
		string(name: 'CORTX_RE_BRANCH', defaultValue: 'stable', description: 'Branch for cortx-prereq build.')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
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
                checkout([$class: 'GitSCM', branches: [[name: "${CORTX_RE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'PathRestriction', excludedRegions: '', includedRegions: 'scripts/third-party-rpm/.*']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CORTX_RE_URL}"]]])
            }
        }

        stage('Build') {
            steps {
				script { build_stage = env.STAGE_NAME }
                sh encoding: 'utf-8', label: 'Build cortx-prereq package', script: """
                    pushd ./scripts/third-party-rpm
                        sh ./build-prerequisite-rpm.sh -v $version -r $CUSTOM_CI_BUILD_ID -g \$(git rev-parse --short HEAD)
                    popd    
                """
            }
        }

		stage ('Upload') {
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