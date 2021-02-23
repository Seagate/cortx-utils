#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}
	
	options {
		timeout(time: 55, unit: 'MINUTES')
		timestamps()  
	}

	environment {
     	release_dir = "/mnt/bigstorage/releases/cortx"
		branch = "custom-ci" 
		os_version = "centos-7.8.2003"
		component = "s3server"
		release_tag = "custom-build-$CUSTOM_CI_BUILD_ID"
		build_upload_dir = "$release_dir/github/integration-custom-ci/$os_version/$release_tag/cortx_iso"
    }

	parameters {  
	    string(name: 'S3_URL', defaultValue: 'https://github.com/Seagate/cortx-s3server', description: 'Repository URL for S3Server')
        string(name: 'S3_BRANCH', defaultValue: 'stable', description: 'Branch for S3Server')
		string(name: 'CUSTOM_CI_BUILD_ID', defaultValue: '0', description: 'Custom CI Build Number')
		
		choice(
            name: 'MOTR_BRANCH', 
            choices: ['custom-ci', 'stable', 'Cortx-v1.0.0_Beta'],
            description: 'Branch name to pick-up Motr components rpms'
        )

	}

	
	stages {
	
		stage ("Dev Build") {
			stages {
				
			
				stage('Checkout') {
					steps {
						step([$class: 'WsCleanup'])
						checkout([$class: 'GitSCM', branches: [[name: "${S3_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: '${S3_URL}']]])
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
								export build_number=${CUSTOM_CI_BUILD_ID}
								if [ "${S3_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
									yum erase log4cxx_cortx-devel cortx-motr{,-devel} -y -q
									yum install eos-core{,-devel} -y
								else
									yum install cortx-motr{,-devel} -y
									yum erase log4cxx_eos-devel -q -y
								fi
							'''
					}
				}

				stage('Build s3server RPM') {
					steps {
						script { build_stage = env.STAGE_NAME }
								sh label: '', script: '''
								export build_number=${CUSTOM_CI_BUILD_ID}
								./rpms/s3/buildrpm.sh -P $PWD
							'''
					}
				}
				
				stage('Build s3iamcli RPM') {
					steps {
						script { build_stage = env.STAGE_NAME }
								sh label: '', script: '''
								export build_number=${CUSTOM_CI_BUILD_ID}
								./rpms/s3iamcli/buildrpm.sh -P $PWD
							'''
					}
				}

				stage ('Copy RPMS') {
					steps {
						script { build_stage = env.STAGE_NAME }
						sh label: 'Copy RPMS', script: '''	
							mkdir -p $build_upload_dir
							cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir
							cp /root/rpmbuild/RPMS/noarch/*.rpm $build_upload_dir
							createrepo -v --update $build_upload_dir
						'''
					}
				}

			}	
		}
    }
}