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
		env = "dev"
		component_dir = "$release_dir/components/github/$branch/$os_version/$env/$component"
    }

	parameters {  
	    string(name: 'S3_URL', defaultValue: 'https://github.com/Seagate/cortx-s3server', description: 'Repository URL for S3Server')
        string(name: 'S3_BRANCH', defaultValue: 'stable', description: 'Branch for S3Server')
		
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
						sh label: 'Script', script: '''
						set +x
						echo "---------------------------------------------------------------------------"
						echo "Building & Running S3 from '${S3_BRANCH}'"
						echo "---------------------------------------------------------------------------"
						'''
						}
					}
				
				
				stage('Build s3server RPM') {
					steps {
						script { build_stage = env.STAGE_NAME }
								sh label: '', script: '''
								sed '/baseurl/d' /etc/yum.repos.d/motr_current_build.repo
								if [ $MOTR_BRANCH == "stable" ]; then
									echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/stable/$os_version/dev/motr/current_build/"  >> /etc/yum.repos.d/motr_current_build.repo
								elif [ $MOTR_BRANCH == "Cortx-v1.0.0_Beta" ]; then 	
									echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/Cortx-v1.0.0_Beta/$os_version/dev/mero/current_build/" >> /etc/yum.repos.d/motr_current_build.repo	
								else
									echo "baseurl=http://cortx-storage.colo.seagate.com/releases/cortx/components/github/custom-ci/$os_version/dev/motr/current_build/"  >> /etc/yum.repos.d/motr_current_build.repo
								fi	
							    yum-config-manager --disable cortx-C7.7.1908
								yum clean all;rm -rf /var/cache/yum
								export build_number=${BUILD_ID}
								
								if [ "${S3_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
									yum erase log4cxx_cortx-devel cortx-motr{,-devel} -y -q
									yum install eos-core{,-devel} -y
								else
									yum install cortx-motr{,-devel} -y
									yum erase log4cxx_eos-devel -q -y
								fi	
								
								./rpms/s3/buildrpm.sh -P $PWD
							'''
					}
				}
				
				stage('Build s3iamcli RPM') {
					steps {
						script { build_stage = env.STAGE_NAME }
								sh label: '', script: '''
								export build_number=${BUILD_ID}
								./rpms/s3iamcli/buildrpm.sh -P $PWD
							'''
					}
				}

				stage ('Copy RPMS') {
					steps {
						script { build_stage = env.STAGE_NAME }
						sh label: 'Copy RPMS', script: '''	
							test -d $component_dir/$BUILD_NUMBER && rm -rf $component_dir/$BUILD_NUMBER
							mkdir -p $component_dir/$BUILD_NUMBER
							cp /root/rpmbuild/RPMS/x86_64/*.rpm $component_dir/$BUILD_NUMBER
							cp /root/rpmbuild/RPMS/noarch/*.rpm $component_dir/$BUILD_NUMBER
						'''
					}
				}
				
				
				stage ('Repo Creation') {
					steps {
						script { build_stage = env.STAGE_NAME }
						sh label: 'Repo Creation', script: '''pushd $component_dir/$BUILD_NUMBER
							rpm -qi createrepo || yum install -y createrepo
							createrepo .
							popd
						'''
					}
				}
				
				stage ('Tag last_successful') {
					steps {
						script { build_stage = env.STAGE_NAME }
						sh label: 'Tag last_successful', script: '''pushd  $component_dir
							test -L  $component_dir/last_successful && rm -f last_successful
							ln -s $component_dir/$BUILD_NUMBER last_successful
							popd
						'''
					}
				}
			}	
		}
    }
}