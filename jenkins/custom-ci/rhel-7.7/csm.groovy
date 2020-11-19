pipeline {
	agent {
		node {
			label 'docker-rhel7.7.1908-csm-cortx-node'
		}
	}
	
	environment {      
        env = "dev"
		component = "csm"
        branch = "custom-ci"
        os_version = "rhel-7.7.1908"
        release_dir = "/mnt/bigstorage/releases/cortx"
        build_upload_dir = "$release_dir/components/github/$branch/$os_version/$env/$component/"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps ()
        ansiColor('xterm')
        disableConcurrentBuilds()
	}
	
	parameters {  
        string(name: 'CSM_URL', defaultValue: 'https://github.com/Seagate/cortx-csm.git', description: 'Branch for cortx-csm build.')
		string(name: 'CSM_BRANCH', defaultValue: 'stable', description: 'Branch for cortx-csm build.')
	}	


	stages {

		stage('Checkout') {
			steps {
				script { build_stage = env.STAGE_NAME }

				checkout([$class: 'GitSCM', branches: [[name: "${CSM_BRANCH}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${CSM_URL}"]]])
			}
		}
		
		stage('Install Dependencies') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Install Dependencies', script: '''
					if [ "${CSM_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
						yum install -y eos-py-utils
						pip3.6 install  pyinstaller==3.5
					else
						yum install -y eos-py-utils cortx-prvsnr
						pip3.6 install  pyinstaller==3.5
					fi
				'''
			}
		}	
		
		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', script: '''
					BUILD=$(git rev-parse --short HEAD)
					VERSION=$(cat $WORKSPACE/VERSION)
					echo "Executing build script"
					echo "VERSION:$VERSION"
					echo "Python:$(python --version)"
					./jenkins/build.sh -v $VERSION -b $BUILD_NUMBER -t -i -q
				'''	
			}
		}
		
		stage ('Upload') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp ./dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
				'''
				sh label: 'Repo Creation', script: '''pushd $build_upload_dir/$BUILD_NUMBER
					rpm -qi createrepo || yum install -y createrepo
					createrepo .
					popd
				'''
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
					test -d $build_upload_dir/last_successful && rm -f last_successful
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
