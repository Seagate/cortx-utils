pipeline {
    agent {
        node {
            label 'docker-io-centos-7.8.2003-node'
        }
    }
    
    options {
		timeout(time: 120, unit: 'MINUTES')
		timestamps()
		disableConcurrentBuilds()
        buildDiscarder(logRotator(daysToKeepStr: '30', numToKeepStr: '30'))
		ansiColor('xterm')
	}

    environment {
        build_upload_dir = "/mnt/bigstorage/releases/cortx/third-party-deps/custom-deps/motr/libfabric/"
    }

    parameters {

        string(name: 'CORTX_RE_BRANCH', defaultValue: 'main', description: 'Branch or GitHash to build docker image', trim: true)
        string(name: 'CORTX_RE_REPO', defaultValue: 'https://github.com/Seagate/cortx-re', description: 'Repository to build docker image', trim: true)
        string(name: 'libfabric_release', defaultValue: 'v1.13.0', description: 'Libfaric Version. Refer - https://github.com/ofiwg/libfabric/releases/tag/v1.12.1', trim: true)
	}	

    stages {

        stage('Checkout Script') {
            steps {             
                script {
                    checkout([$class: 'GitSCM', branches: [[name: "${CORTX_RE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CORTX_RE_REPO}"]]])                
                }
            }
        }

        stage ('Build RPM') {
			steps {
				script { build_stage = env.STAGE_NAME }
				
				sh label: 'Install prerequisite', script: '''
				rm -rf /etc/yum.repos.d/CentOS-*
				yum install libibverbs librdmacm-devel -y
				'''
				
				sh label: 'Build RPM', script: '''
				
                git clone https://github.com/ofiwg/libfabric -b $libfabric_release
                pushd libfabric
                    ./autogen.sh
                    ./configure
                    make rpm
                popd    
				
		        '''
			}
		}

        stage ('Upload') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp /root/rpmbuild/RPMS/x86_64/libfabric*.rpm $build_upload_dir/$BUILD_NUMBER
                    createrepo -v $build_upload_dir/$BUILD_NUMBER
				'''
			}
		}

        stage ('Tag last_successful') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
					test -L $build_upload_dir/last_successful && rm -f last_successful
					ln -s $build_upload_dir/$BUILD_NUMBER last_successful
					popd
				'''
			}
		}

    }
}