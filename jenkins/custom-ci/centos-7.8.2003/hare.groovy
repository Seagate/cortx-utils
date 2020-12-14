pipeline {
	
    agent {
		node {
			label 'docker-io-centos-7.8.2003-node'
		}
	}

	parameters {  
	    string(name: 'HARE_URL', defaultValue: 'https://github.com/Seagate/cortx-hare/', description: 'Repository URL for Hare build')
        string(name: 'HARE_BRANCH', defaultValue: 'stable', description: 'Branch for Hare build')
		
		choice(
            name: 'MOTR_BRANCH', 
            choices: ['custom-ci', 'stable', 'Cortx-v1.0.0_Beta'],
            description: 'Branch name to pick-up other components rpms'
        )
	}
	

   	environment {
     	release_dir = "/mnt/bigstorage/releases/cortx"
		branch = "custom-ci"
		os_version = "centos-7.8.2003"
		component = "hare"
		env = "dev"
		component_dir = "$release_dir/components/github/$branch/$os_version/$env/$component"
    }
	
	
	
	options {
		timeout(time: 35, unit: 'MINUTES')
		timestamps() 
	}

	stages {
	
		stage('Checkout hare') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh 'mkdir -p hare'
				dir ('hare') {
					checkout([$class: 'GitSCM', branches: [[name: "${HARE_BRANCH}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CloneOption', depth: 0, noTags: false, reference: '', shallow: false, timeout: 15], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: true, recursiveSubmodules: true, reference: '', trackingSubmodules: false, timeout: 15]], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: "${HARE_URL}"]]])
				}
			}
		}
	
		stage('Install Dependencies') {
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
					yum clean all
					rm -rf /var/cache/yum
					
					if [ "${HARE_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
					yum install eos-core{,-devel} -y
					else
					yum install cortx-motr{,-devel} -y
					fi
				'''
			}
		}

		stage('Build') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Build', returnStatus: true, script: '''
					set -xe
					pushd $component
					echo "Executing build script"
					export build_number=${BUILD_ID}
					make rpm
					popd
				'''	
			}
		}

        stage ('Copy RPMS') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					test -d /$BUILD_NUMBER && rm -rf $component_dir/$BUILD_NUMBER
					mkdir -p $component_dir/$BUILD_NUMBER
					cp /root/rpmbuild/RPMS/x86_64/*.rpm $component_dir/$BUILD_NUMBER
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
				sh label: 'Tag last_successful', script: '''pushd $component_dir
					test -L $component_dir/last_successful && rm -f last_successful
					ln -s $component_dir/$BUILD_NUMBER last_successful
					popd
				'''
			}
		}
	}
}