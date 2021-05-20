#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	
	environment {
		component = "csm-web"
        branch = "custom-ci" 
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps ()
        ansiColor('xterm')
	}
	
	parameters {  
        string(name: 'CSM_WEB_URL', defaultValue: 'https://github.com/Seagate/cortx-management-web.git', description: 'Branch for cortx-management-web build.')
		string(name: 'CSM_WEB_BRANCH', defaultValue: 'stable', description: 'Branch for cortx-management-web build.')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
	}	


	stages {

		stage('Checkout') {
			steps {
				script { build_stage = env.STAGE_NAME }
				dir('cortx-management-web') {
				    checkout([$class: 'GitSCM', branches: [[name: "${CSM_WEB_BRANCH}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CSM_WEB_URL}"]]])
				}
				dir('seagate-ldr') {
				    checkout([$class: 'GitSCM', branches: [[name: '*/master']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/seagate-ldr.git']]])
				}
				dir ('cortx-re') {
					checkout changelog: false, poll: false, scm: [$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', noTags: true, reference: '', shallow: true]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]]
				}
			}
		}
		
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }

				sh label: 'Install cortx-prereq package', script: """
					pip3 uninstall pip -y && yum install python3-pip -y && ln -s /usr/bin/pip3 /usr/local/bin/pip3
					sh ./cortx-re/scripts/third-party-rpm/install-cortx-prereq.sh
				"""
				sh label: 'Install Utils and Provisionr', script: '''
					yum install -y cortx-py-utils cortx-prvsnr
					pip3.6 install  pyinstaller==3.5
				'''
			}
		}	
		
		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', script: '''
					pushd cortx-management-web
						BUILD=$(git rev-parse --short HEAD)
						VERSION=$(cat VERSION)
						echo "Executing build script"
						echo "VERSION:$VERSION"
						echo "Python:$(python --version)"
						./cicd/build.sh -v $VERSION -b $CUSTOM_CI_BUILD_ID -t -i -n ldr -l $WORKSPACE/seagate-ldr/ldr-brand/
					popd	
				'''	
			}
		}
		
		stage ('Upload') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir
					cp ./cortx-management-web/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir
					createrepo -v --update $build_upload_dir
				'''
			}
		}	

	}
}	
