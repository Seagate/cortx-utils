pipeline {
    agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}
    
    environment {
        env = "dev"
		component = "cortx-ha"
        branch = "custom-ci" 
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
        component_dir = "$release_dir/components/github/$branch/$os_version/$env/$component/"
    }
	
	parameters {
		string(name: 'HA_URL', defaultValue: 'https://github.com/Seagate/cortx-ha', description: 'Repository URL to be used for cortx-ha build.')
		string(name: 'HA_BRANCH', defaultValue: 'stable', description: 'Branch to be used for cortx-ha build.')
	}
	
	
	options {
		timeout(time: 35, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')
		disableConcurrentBuilds()  
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
   				   ./jenkins/build.sh -b $BUILD_NUMBER
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
					mkdir -p $component_dir/$BUILD_NUMBER
					cp $WORKSPACE/cortx-ha/dist/rpmbuild/RPMS/x86_64/*.rpm $component_dir/$BUILD_NUMBER
				'''
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
				sh label: 'Tag last_successful', script: '''pushd $component_dir/
					test -L $component_dir/last_successful && rm -f last_successful
					ln -s $component_dir/$BUILD_NUMBER last_successful
					popd
				'''
			}
		}
	}
}