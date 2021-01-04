pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
    
    triggers {
        pollSCM 'H/5 * * * *'
    }

    parameters {
        string(name: 'branch', defaultValue: 'main', description: 'Branch Name')
    }
	
	environment {      
        env = "dev"
		component = "cortx-utils"
        os_version = "centos-7.8.2003"
        pipeline_group = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "${release_dir}/components/github/${pipeline_group}/${os_version}/${env}/${component}"

        // Param hack for initial config
        branch="${branch != null ? branch : 'main'}"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps ()
        ansiColor('xterm')
        disableConcurrentBuilds()
	}

	stages {
		stage('Checkout py-utils') {
			steps {
                checkout([$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-utils']]])
			}
		}
        
		stage('Build') {
			steps {
				sh label: 'Build', script: '''
				yum install python36-devel -y
				pushd py-utils
				python3 setup.py bdist_rpm --post-install utils-post-install --pre-uninstall utils-pre-uninstall --release="${BUILD_NUMBER}_$(git rev-parse --short HEAD)"
				popd
				
				./statsd-utils/jenkins/build.sh -b $BUILD_NUMBER
	        '''	
			}
		}	
        
        
        stage ('Upload') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script: '''
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    shopt -s extglob
					cp ./py-utils/dist/!(*.src.rpm|*.tar.gz) $build_upload_dir/$BUILD_NUMBER
					cp ./statsd-utils/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
                '''
                sh label: 'Repo Creation', script: '''
                    pushd $build_upload_dir/$BUILD_NUMBER
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
                 sh label: 'Tag last_successful', script: '''
                    pushd $build_upload_dir/
                    test -L $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
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