#!/usr/bin/env groovy
pipeline {
    agent {
		node {
			label 'docker-centos7.7.1908-prvsnr-premerge-node'
		}
	}

    parameters {
        string(name: 'release_component', defaultValue: '', description: 'Component name that triggers this release')
        string(name: 'build_number', defaultValue: '', description: 'Build number for this release')
    }
	
	environment {

        release_component="${release_component != null ? release_component : 'dry_run'}"

        env="dev"
        pipeline_group="pre-merge"
        os_version="centos-7.7.1908"
        release_dir="/mnt/data1/releases/eos"
        premerge_component_dir="$release_dir/components/$pipeline_group/$os_version/$env"
        master_component_dir="$release_dir/components/dev/$os_version/"
        build_upload_dir="$release_dir/$pipeline_group/$os_version"
        release_name="${build_number}_${release_component}"
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
                    
                    # Create Release Dir
                    test -d $build_upload_dir/$release_name && rm -rf $build_upload_dir/$release_name
                    mkdir -p $build_upload_dir/$release_name

                    premerge_comp="${release_component}"
                    if  [ "${release_component}" == "mero" ] ; then
                        premerge_comp="${release_component} | s3server | hare"
                    fi

                    # Push Premerge Buil RPM of release component
                    pushd $premerge_component_dir
                        for component in $(echo $premerge_comp | tr "|" "\n"); do 
                            component_real_build_path=$(readlink -f "${premerge_component_dir}/${component}/last_successful")
                            ln -s $component_real_build_path $build_upload_dir/$release_name/$component
                        done    
                    popd

                    # Push master Build RPM of other component
                    pushd $master_component_dir
                        echo "Pre-merge  : $premerge_comp"
                        for component in `ls -1 | grep -E -v "$premerge_comp" | grep -E -v 'luster|halon|integration|nightly|centos-7.6.1810'`
                        do
                            echo "\033[1;33m Processing $component RPM \033[0m "
                            component_last_successful_dir=$component/last_successful
                            if [[ -L $component_last_successful_dir && -d "$(readlink $component_last_successful_dir )" ]]; then
                                component_real_build_path=$(readlink -f $component_last_successful_dir)
                                ln -s $component_real_build_path $build_upload_dir/$release_name/$component
                            else
                                echo "\033[1;31m [ $component ] : last_successful symlink or directory does not exist \033[0m"
                            fi 
                        done
                    popd
                '''

                sh label: 'Repo Creation', script: '''
                    pushd $build_upload_dir/$release_name
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
			}
		}

        stage('Validate RPM') {
            when { expression { false } }
			steps {
                catchError(buildResult: 'SUCCESS') {
                    script { build_stage=env.STAGE_NAME }
                    sh label: 'Validate RPMS for Mero Dependency', script:''' pushd $build_upload_dir/$release_name
                        set +x
                        
                        cd $build_upload_dir/$release_name/mero
                        mero_rpm=$(ls -1 | grep "eos-core" | grep -E -v "eos-core-debuginfo|eos-core-devel|eos-core-tests")
                        mero_rpm_release=`rpm -qp ${mero_rpm} --qf '%{RELEASE}' | tr -d '\040\011\012\015'`
                        mero_rpm_version=`rpm -qp ${mero_rpm} --qf '%{VERSION}' | tr -d '\040\011\012\015'`
                        mero_rpm_release_version="${mero_rpm_version}-${mero_rpm_release}"
                        cd $build_upload_dir/$release_name

                        for component_folder in `ls -1`
                        do
                            cd $build_upload_dir/$release_name/$component_folder

                            for component in `ls -1 | grep ".rpm"`
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
                                        
                                        mv "$build_upload_dir/$release_name" "$build_upload_dir/${release_name}-do-not-use"
                                        exit 1
                                    fi
                                fi
                            done
                        
                        done

                        popd
                    '''
                }
			}
		}
	
		stage ('Build MANIFEST') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Build MANIFEST', script: '''
                    sh build_manifest.sh $build_upload_dir/$release_name/
                    sh build_readme.sh $build_upload_dir/$release_name/
                '''
			}
		}
		
		stage ('Tag last_successful') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Tag last_successful', script: '''
                    pushd $build_upload_dir/
                    test -d $build_upload_dir/last_successful && rm -f last_successful
                    ln -s $build_upload_dir/$release_name last_successful
                    popd
                '''
			}
		}
	}
    
    post {
		always {
            script {
                	
                currentBuild.upstreamBuilds?.each { b -> env.upstream_project = "${b.getProjectName()}";env.upstream_build = "${b.getId()}" }
                env.release_build_location = "http://ssc-nfs-server1.colo.seagate.com/releases/eos/$pipeline_group/$os_version/$release_name"
                env.release_build = "${env.release_name}"
                env.build_stage = "${build_stage}"

                def mailRecipients = "gowthaman.chinnathambi@seagate.com"

                emailext ( 
                    body: '''${SCRIPT, template="release-email.template"}''',
                    mimeType: 'text/html',
                    subject: "Pre-Merge Release # ${env.release_name} - ${currentBuild.currentResult}",
                    attachLog: true,
                    to: "${mailRecipients}",
                )
            }
        }
    }
}	
