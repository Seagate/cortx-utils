pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	
    parameters {  
		string(name: 'CSM_WEB_BRANCH', defaultValue: 'stable', description: 'Branch/Hash for cortx-management-web build.')
	}	

	environment {
		version="1.0.1"    
        env="dev"
		component="csm-web"
        branch="cortx-1.0"
        os_version="centos-7.8.2003"
        release_dir="/mnt/bigstorage/releases/cortx"
        build_upload_dir="$release_dir/components/github/ova/$os_version/$env/$component"
    }

	options {
		timeout(time: 60, unit: 'MINUTES')
		timestamps ()
        ansiColor('xterm')
        disableConcurrentBuilds()
	}
	
	stages {

		stage('Checkout') {
			steps {
				script { build_stage=env.STAGE_NAME }
				dir('cortx-management-portal'){
				    checkout([$class: 'GitSCM', branches: [[name: "${CSM_WEB_BRANCH}"]], doGenerateSubmoduleConfigurations: false,  extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-management-portal']]])
				}
			}
		}
		
		stage('Install Dependencies') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: '', script: '''
					yum install -y cortx-py-utils cortx-prvsnr
					pip3.6 install  pyinstaller==3.5
				'''
			}
		}	
		
		stage('Build') {
			steps {
				script { build_stage=env.STAGE_NAME }
				
				sh label: 'Build', returnStatus: true, script: '''
				    pushd cortx-management-portal
					BUILD=$(git rev-parse --short HEAD)
					popd
					echo "Python:$(python --version)"
					./cortx-management-portal/cicd/build.sh -v $version -b $BUILD_NUMBER -t -i
				'''	
			}
		}
		
		stage ('Upload') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp ./cortx-management-portal/dist/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
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
				script { build_stage=env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
					test -d $build_upload_dir/last_successful && rm -f last_successful
					ln -s $build_upload_dir/$BUILD_NUMBER last_successful
					popd
				'''
			}
		}
	}
	
	post {
		always {
			script{
            	
				echo 'Cleanup Workspace.'
				deleteDir() /* clean up our workspace */

				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).toUpperCase()
				env.build_stage = "${build_stage}"

				
				toEmail="shailesh.vaidya@seagate.com"
				emailext (
					body: '''${SCRIPT, template="component-email.template"}''',
					mimeType: 'text/html',
				    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
					attachLog: true,
					to: toEmail
				)
			}
		}
    }
}