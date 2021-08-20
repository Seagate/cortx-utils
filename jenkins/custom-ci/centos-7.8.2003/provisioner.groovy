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
        buildDiscarder(logRotator(daysToKeepStr: '5', numToKeepStr: '10'))
    }
    
    stages {
        stage('Checkout') {
            steps {
				script { build_stage = env.STAGE_NAME }
					checkout([$class: 'GitSCM', branches: [[name: "${PRVSNR_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${PRVSNR_URL}"]]])
            }
        }

        stage('Build') {
            steps {
				script { build_stage = env.STAGE_NAME }
                sh encoding: 'utf-8', label: 'Provisioner RPMS', returnStdout: true, script: """
                    rm -rf /etc/yum.repos.d/CentOS-*
                    sh ./devops/rpms/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 2.0.0 -b ${CUSTOM_CI_BUILD_ID}
                """
                sh encoding: 'utf-8', label: 'Provisioner CLI RPMS', returnStdout: true, script: """
				    sh ./cli/buildrpm.sh -g \$(git rev-parse --short HEAD) -e 2.0.0 -b ${CUSTOM_CI_BUILD_ID}
                """
                sh encoding: 'UTF-8', label: 'cortx-setup', script: """
                if [ -f "./devops/rpms/node_cli/node_cli_buildrpm.sh" ]; then
                    sh ./devops/rpms/node_cli/node_cli_buildrpm.sh -g \$(git rev-parse --short HEAD) -e 2.0.0 -b ${CUSTOM_CI_BUILD_ID}
                else
                    echo "node_cli package creation is not implemented"
                fi
                """
				sh encoding: 'UTF-8', label: 'api', script: '''
					bash ./devops/rpms/api/build_python_api.sh -vv --out-dir /root/rpmbuild/RPMS/x86_64/ --pkg-ver ${CUSTOM_CI_BUILD_ID}_git$(git rev-parse --short HEAD)
				'''
                sh encoding: 'UTF-8', label: 'cortx-setup', script: '''
                if [ -f "./devops/rpms/lr-cli/build_python_cortx_setup.sh" ]; then
					bash ./devops/rpms/lr-cli/build_python_cortx_setup.sh -vv --out-dir /root/rpmbuild/RPMS/x86_64/ --pkg-ver ${CUSTOM_CI_BUILD_ID}_git$(git rev-parse --short HEAD)
                else
                    echo "cortx-setup package creation is not implemented"
                fi        
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