pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}

	environment {   
        env = "dev"
		component = "sspl"
        branch = "custom-ci"
        os_version = "centos-7.8.2003"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "$release_dir/components/github/$branch/$os_version/$env/$component/"
    }

	options {
		timeout(time: 30, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')  
        disableConcurrentBuilds()  
	}
	
	parameters {  
        string(name: 'SSPL_URL', defaultValue: 'https://github.com/Seagate/cortx-monitor.git', description: 'Repository URL for cortx-monitor.')
		string(name: 'SSPL_BRANCH', defaultValue: 'stable', description: 'Branch for cortx-monitor.')
	}	


	stages {
		stage('Checkout') {
			steps {
				script { build_stage = env.STAGE_NAME }
				dir ('cortx-sspl') {
					checkout([$class: 'GitSCM', branches: [[name: "${SSPL_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${SSPL_URL}"]]])
				}
				script {
					version =  sh (script: 'cat ./cortx-sspl/VERSION', returnStdout: true).trim()
					env.version = version
				}
			}
		}
		
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: '', script: '''
				echo $version
				echo ${version}
				
				echo "VERSION: $version"
				if [ "$version" == "1.0.0" ]; then
					yum-config-manager --disable cortx-C7.7.1908
				fi	
					yum clean all && rm -rf /var/chache/yum 
					yum install sudo python-Levenshtein libtool doxygen python-pep8 openssl-devel graphviz check-devel -y
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', returnStatus: true, script: '''
					set -xe
					if [ "${SSPL_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
						mv cortx-sspl sspl
						pushd sspl
					else
						pushd cortx-sspl
					fi
						export build_number=${BUILD_ID}
						./jenkins/build.sh -v $version -l DEBUG 
					popd
				'''	
			}
		}
		
		stage ('Upload') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
					cp /root/rpmbuild/RPMS/noarch/*.rpm $build_upload_dir/$BUILD_NUMBER
				'''
				sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
					rpm -qi createrepo || yum install -y createrepo
					createrepo .
					popd
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