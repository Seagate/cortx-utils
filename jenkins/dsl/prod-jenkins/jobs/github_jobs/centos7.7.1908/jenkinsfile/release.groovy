#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-rhel7.7-prvsnr-github-node'
		}
	}
	
	environment {
        env="dev"
        branch="github"
        os_version="rhel-7.7.1908"
        release_dir="/mnt/bigstorage/releases/eos"
        component_dir="$release_dir/components/$branch/$os_version/$env"
        build_upload_dir="$release_dir/$branch/$os_version"
    }
	
	options {
		timeout(time: 60, unit: 'MINUTES') 
        ansiColor('xterm') 
        disableConcurrentBuilds()  
	}
		
	stages {			
        
        stage('Checkout Release scripts') {
			steps {
                script { build_stage=env.STAGE_NAME }
				checkout([$class: 'GitSCM', branches: [[name: '*/EOS-8683']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: '1f8776fd-39de-4356-ba0a-a40895719a3d', url: 'http://gitlab.mero.colo.seagate.com/eos/re/rpm-signing.git']]])
			}
		}

		stage ('Integrate Component RPM') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Copy RPMS', script:'''
                    set +x
                    pushd $component_dir
                    test -d $build_upload_dir/$BUILD_NUMBER && rm -rf $build_upload_dir/$BUILD_NUMBER
                    mkdir -p $build_upload_dir/$BUILD_NUMBER
                    for component in `ls -1`
                    do
                        echo "\033[1;33m Processing $component RPM \033[0m "
                        component_last_successful_dir=$component/last_successful
                        if [[ -L $component_last_successful_dir && -d "$(readlink $component_last_successful_dir )" ]]; then
                            component_real_build_path=$(readlink -f $component_last_successful_dir)
                            ln -s $component_real_build_path $build_upload_dir/$BUILD_NUMBER/$component
                        else
                            echo "\033[1;31m [ $component ] : last_successful symlink or directory does not exist \033[0m"
                        fi 
                    done
                    popd
                '''

                sh label: 'Repo Creation', script: '''
                    pushd $build_upload_dir/$BUILD_NUMBER
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
			}
		}

        stage('Validate RPM') {
            when { expression { false } }
			steps {
                script { build_stage=env.STAGE_NAME }
				sh label: 'Validate RPMS for Mero Dependency', script:''' pushd $build_upload_dir/$BUILD_NUMBER
                    set +x
                    mero_rpm=$(ls -1 | grep "eos-core" | grep -E -v "eos-core-debuginfo|eos-core-devel|eos-core-tests")
                    mero_rpm_release=`rpm -qp ${mero_rpm} --qf '%{RELEASE}' | tr -d '\040\011\012\015'`
                    mero_rpm_version=`rpm -qp ${mero_rpm} --qf '%{VERSION}' | tr -d '\040\011\012\015'`
                    mero_rpm_release_version="${mero_rpm_version}-${mero_rpm_release}"
                    for component in `ls -1`
                    do
                        mero_dep=`echo $(rpm -qpR ${component} | grep -E "eos-core = |mero =") | cut -d= -f2 | tr -d '\040\011\012\015'`
                        if [ -z "$mero_dep" ]
                        then
                            echo "\033[1;33m $component has no dependency to mero - Validation Success \033[0m "
                        else
                            if [ "$mero_dep" = "$mero_rpm_release_version" ]; then
                                echo "\033[1;32m $component mero version matches with integration mero rpm($mero_rpm_release_version) Good to Go - Validation Success \033[0m "
                            else
                                echo "\033[1;31m $component mero version mismatchs with integration mero rpm($mero_rpm_release_version) - Validation Failed \033[0m"
                                
                                mv "$build_upload_dir/$BUILD_NUMBER" "$build_upload_dir/${BUILD_NUMBER}-do-not-use"
                                exit 1
                            fi
                        fi
                    done
                    popd
                '''
			}
		}
	
		stage ('Build MANIFEST') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Build MANIFEST', script: '''
                    sh build_manifest.sh $build_upload_dir/$BUILD_NUMBER/
                    sh build_readme.sh $build_upload_dir/$BUILD_NUMBER/
                '''
			}
		}
		
		stage ('Tag last_successful') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Tag last_successful', script: '''
                    pushd $build_upload_dir/
                    test -d $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$BUILD_NUMBER last_successful
                    popd
                '''
			}
		}
	}
    
    post {
		always {
            script {
                	
                currentBuild.upstreamBuilds?.each { b -> env.upstream_project = "${b.getProjectName()}";env.upstream_build = "${b.getId()}" }
                env.release_build_location = "http://ci-storage.mero.colo.seagate.com/releases/eos/$branch/$os_version/${env.BUILD_NUMBER}"
                env.release_build = "${env.BUILD_NUMBER}"
                env.build_stage = "${build_stage}"

                def mailRecipients = "gowthaman.chinnathambi@seagate.com"

                emailext ( 
                    body: '''${SCRIPT, template="release-email.template"}''',
                    mimeType: 'text/html',
                    subject: "GitHub Release # ${env.BUILD_NUMBER} - ${currentBuild.currentResult}",
                    attachLog: true,
                    to: "${mailRecipients}",
                )
            }
        }
    }
}	
