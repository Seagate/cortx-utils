#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-centos7.7.1908-nfs-premerge-node'
		}
	}

	parameters {
        string(name: 'branch', defaultValue: 'master', description: 'Branch Name')
    }
    
    environment { 
        env="dev"
		component="nfs"
        os_version="centos-7.7.1908"
		pipeline_group="pre-merge"
        release_dir="/mnt/bigstorage/releases/eos"
        build_upload_dir="${release_dir}/components/${pipeline_group}/${os_version}/${env}/${component}"

		// Param hack for initial config
        branch="${branch != null ? branch : 'master'}"
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
				script { build_stage=env.STAGE_NAME }
				dir ('eos-fs') {
					checkout([$class: 'GitSCM', branches: [[name: "*/${branch}"]], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: 'http://gitlab.mero.colo.seagate.com/eos/fs/eos-fs.git']]])
				}
                dir ('nfs-ganesha') {
                	checkout([$class: 'GitSCM', branches: [[name: '*/2.8-stable-eos']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'CheckoutOption'], [$class: 'SubmoduleOption', disableSubmodules: false, parentCredentials: false, recursiveSubmodules: true, reference: '', trackingSubmodules: false]], submoduleCfg: [], userRemoteConfigs: [[url: 'http://gitlab.mero.colo.seagate.com/eos/fs/nfs-ganesha.git']]])
				}
			}
		}

        stage('Install Dependencies') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: '', script: '''
					rm -rf /root/rpmbuild/RPMS/x86_64/*.rpm
					yum install userspace-rcu-devel dbus-devel eos-core{,-devel,-debuginfo} -y
		        '''
			}
		}
		
		stage('Build') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: 'Build', script: '''
					set -xe
					pushd eos-fs
					VERSION=$(cat VERSION)
					#Execute build script
					echo "Executing build script"
					echo "VERSION:$VERSION"
					./jenkins/build.sh -v $VERSION -b $BUILD_NUMBER -p ../nfs-ganesha/src/
					popd
				'''	
			}
		}

        stage ('Upload') {
			steps {
				script { build_stage=env.STAGE_NAME }
				sh label: 'Copy RPMS', script: '''
					mkdir -p $build_upload_dir/$BUILD_NUMBER
					cp /root/rpmbuild/RPMS/x86_64/*.rpm $build_upload_dir/$BUILD_NUMBER
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
				script { build_stage=env.STAGE_NAME }
				sh label: 'Tag last_successful', script: '''pushd $build_upload_dir/
					test -d $build_upload_dir/last_successful && rm -f last_successful
					ln -s $build_upload_dir/$BUILD_NUMBER last_successful
					popd
				'''
			}
		}

        stage ('Copy to New NFS') {
			steps {
                catchError(buildResult: 'SUCCESS') {
                    script { build_stage=env.STAGE_NAME }
                    sh label: 'copy_to_new_nfs', script: '''

                        nfs_upload_path=/mnt/data1/releases/eos/components/${pipeline_group}/${os_version}/${env}/${component}
                        mkdir -p $nfs_upload_path

                        pushd $nfs_upload_path
                            
                            test -d $nfs_upload_path/$BUILD_NUMBER && rm -f $nfs_upload_path/$BUILD_NUMBER
                            cp -R $build_upload_dir/$BUILD_NUMBER $nfs_upload_path/$BUILD_NUMBER
                            
                            test -d $nfs_upload_path/last_successful && rm -f last_successful
                            ln -s $nfs_upload_path/$BUILD_NUMBER last_successful
                        popd
                    '''
                }
			}
		}	

		stage ("Release") {
            steps {
                script { build_stage=env.STAGE_NAME }
				script {
                	def releaseBuild = build job: 'Pre-merge Release', propagate: false, parameters: [string(name: 'release_component', value: "${component}")]
				 	env.release_build = releaseBuild.number
                    env.release_build_location="http://cortx-storage.colo.seagate.com/releases/eos/$pipeline_group/$os_version/"+releaseBuild.number+"_${component}"
				}
            }
        } 
	}

	post {
		always{                
			script{
				env.release_build = (env.release_build != null) ? env.release_build : "" 
				env.release_build_location = (env.release_build_location != null) ? env.release_build_location : ""
				env.component = (env.component).capitalize()
				env.build_stage = "${build_stage}"

				def toEmail = "gowthaman.chinnathambi@seagate.com"
				emailext (
					body: '''${SCRIPT, template="component-email.template"}''',
					mimeType: 'text/html',
					subject: "${env.JOB_BASE_NAME} Pre-Merge Build ${currentBuild.currentResult}",
					attachLog: true,
					to: toEmail,
				)
			}
		}
	}
}	