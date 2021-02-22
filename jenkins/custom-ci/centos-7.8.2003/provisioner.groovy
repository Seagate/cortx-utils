#!/usr/bin/env groovy
pipeline { 
    agent {
        node {
            label 'docker-cp-centos-7.8.2003-node'
        }
    }
    
	parameters {  
        string(name: 'PRVSNR_URL', defaultValue: 'https://github.com/Seagate/cortx-prvsnr', description: 'Repository URL for Provisioner.')
		string(name: 'PRVSNR_BRANCH', defaultValue: 'stable', description: 'Branch for Provisioner.')
        string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
	}	

	environment {
        component = "provisioner"
        branch = "custom-ci"
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
        release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }

    options {
        timeout(time: 15, unit: 'MINUTES')
        timestamps()
        ansiColor('xterm')
    }
    
    stages {
        stage('Checkout') {
            steps {
				script { build_stage = env.STAGE_NAME }
					checkout([$class: 'GitSCM', branches: [[name: "${PRVSNR_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${PRVSNR_URL}"]]])
            }
        }

        stage('Install Dependencies') {
            steps {
				script { build_stage = env.STAGE_NAME }
                sh encoding: 'utf-8', label: 'Install Python', returnStdout: true, script: 'yum install -y python'
                sh encoding: 'utf-8', label: 'Cleanup', returnStdout: true, script: 'test -d /root/rpmbuild && rm -rf /root/rpmbuild || echo "/root/rpmbuild absent. Skipping cleanup..."'
            }
        }

        stage('Build') {
            steps {
				script { build_stage = env.STAGE_NAME }
                sh encoding: 'utf-8', label: 'Provisioner RPMS', returnStdout: true, script: """
                    sh ./devops/rpms/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 1.0.0 -b ${CUSTOM_CI_BUILD}
                """
                sh encoding: 'utf-8', label: 'Provisioner CLI RPMS', returnStdout: true, script: """
				    sh ./cli/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 1.0.0 -b ${CUSTOM_CI_BUILD}
                """
				
				sh encoding: 'UTF-8', label: 'api', script: '''
				if [ "${PRVSNR_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
					echo "No Provisioner API RPMS in Beta Build hence skipping"
				else
					bash ./devops/rpms/api/build_python_api.sh -vv --out-dir /root/rpmbuild/RPMS/x86_64/ --pkg-ver ${custom_build_number}_git$(git rev-parse --short HEAD)
				fi
				   ls -ltr /root/rpmbuild/RPMS/x86_64/*.rpm
				'''
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