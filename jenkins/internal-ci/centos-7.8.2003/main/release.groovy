#!/usr/bin/env groovy
pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}	

    	parameters {
        	string(name: 'release_component', defaultValue: 'dry_run', description: 'Component name that triggers this release')
	        string(name: 'release_build', defaultValue: '1', description: 'Component build number that triggers this release')
    	}
	
	environment {

        	version = "1.0.0"
		thrid_party_version = "1.0.0-1"
	        release_component = "${release_component != null ? release_component : 'dry_run'}"
        	release_build = "${release_build != null ? release_build : BUILD_NUMBER}"
	        env = "dev"
        	pipeline_group = "main"
	        os_version = "centos-7.8.2003"
        	release_dir = "/mnt/bigstorage/releases/cortx"
	        integration_dir = "$release_dir/github/$pipeline_group/$os_version"
	        components_dir = "$release_dir/components/github/$pipeline_group/$os_version"
	        release_tag = "$BUILD_NUMBER"
        	BUILD_TO_DELETE = ""
	        premerge_component_dir = "$release_dir/components/github/$pipeline_group/$os_version/$env"
        	master_component_dir = "$release_dir/components/github/stable/centos-7.8.2003/$env"
        
	        release_name = "${release_component}_${release_build}"
        	passphrase = credentials('rpm-sign-passphrase')
        
	        token = credentials('shailesh-github-token')
        	// Used in Changelog generation
	        ARTIFACT_LOCATION = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$pipeline_group/centos-7.8.2003"
		githubrelease_repo = "Seagate/cortx"
        	thrid_party_dir = "$release_dir/third-party-deps/centos/centos-7.8.2003-$thrid_party_version/"
		python_deps = "/mnt/bigstorage/releases/cortx/third-party-deps/python-packages"
	        cortx_os_iso = "/mnt/bigstorage/releases/cortx_builds/custom-os-iso/cortx-os-1.0.0-23.iso"
		iso_location = "$release_dir/github/$pipeline_group/iso/$os_version"
		cortx_build_dir = "$release_dir/github/$pipeline_group/$os_version/cortx_builds"
    	}
	
	options {
		timeout(time: 60, unit: 'MINUTES') 
        ansiColor('xterm') 
        	disableConcurrentBuilds()  
	}
		
	stages {

        	stage('Install Dependecies') {
			steps {
                	script { build_stage = env.STAGE_NAME }
	                sh label: 'Installed Dependecies', script: '''
        	            yum install -y expect rpm-sign rng-tools genisoimage python3-pip
			    pip3 install githubrelease
                	    systemctl start rngd
                	'''	
			}
		}			
        
	        stage('Checkout Release scripts') {
			steps {
        	        script { build_stage = env.STAGE_NAME }
                		checkout([$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
			}
		}

	        stage ('Integrate Component RPM') {
			steps {
        	        script { build_stage = env.STAGE_NAME }
                	sh label: 'Copy RPMS', script:'''
	                    # Create Release Dir
        	            test -d $integration_dir/$release_name && rm -rf $integration_dir/$release_name   
                    
                	    mkdir -p $integration_dir/$release_name/cortx_build_temp/dev
	                    mkdir -p $integration_dir/$release_name/cortx_build_temp/prod


        	            premerge_comp="${release_component}"
                	    if  [ "${release_component}" == "motr" ] ; then
                        	premerge_comp="motr|s3server|hare"
                    	    fi

	                    # Push Premerge Buil RPM of release component
        	            pushd $premerge_component_dir
                	        for component in $(echo $premerge_comp | tr "|" "\n"); do 
                        	    component_real_build_path=$(readlink -f "${premerge_component_dir}/${component}/last_successful")
	                            cp -R $component_real_build_path/*.rpm $integration_dir/$release_name/cortx_build_temp/dev
        	                    cp -R $component_real_build_path/*.rpm $integration_dir/$release_name/cortx_build_temp/prod
                	        done    
	                    popd

        	            # Push master Build RPM of other component
                	    pushd $master_component_dir
                        	echo "Pre-merge  : $premerge_comp"
	                        for component in `ls -1 | grep -E -v "$premerge_comp" | grep -Evx  'mero|csm|luster|halon|integration|nightly|centos-7.6.1810'`
        	                do
                	            echo "\033[1;33m Processing $component RPM \033[0m "
                        	    component_last_successful_dir=$component/last_successful
	                            if [[ -L $component_last_successful_dir ]]; then
        	                        component_real_build_path=$(readlink -f $component_last_successful_dir)
                	                cp -R $component_real_build_path/*.rpm $integration_dir/$release_name/cortx_build_temp/dev
                        	        cp -R $component_real_build_path/*.rpm $integration_dir/$release_name/cortx_build_temp/prod
	                            else
        	                        echo "\033[1;31m [ $component ] : last_successful symlink or directory does not exist \033[0m"
                	            fi 
                        	done
	                    popd
        	            pushd $integration_dir/$release_name/cortx_build_temp/prod
                	        rm -f *-debuginfo-*.rpm
	                    popd
        		'''
			}
		}

	        stage('RPM Validation') {
			steps {
        	        script { build_stage = env.STAGE_NAME }
				sh label: 'Validate RPMS for Motr Dependency', script:''' 
                		    for env in "dev" "prod";
		                    do
                        
                	            set +x
		                    pushd $integration_dir/$release_name/cortx_build_temp/$env
                		    motr_rpm=$(ls -1 | grep "cortx-motr" | grep -E -v "cortx-motr-debuginfo|cortx-motr-devel|cortx-motr-tests")
		                    motr_rpm_release=`rpm -qp ${motr_rpm} --qf '%{RELEASE}' | tr -d '\040\011\012\015'`
                		    motr_rpm_version=`rpm -qp ${motr_rpm} --qf '%{VERSION}' | tr -d '\040\011\012\015'`
	                            motr_rpm_release_version="${motr_rpm_version}-${motr_rpm_release}"
            		            for component in `ls -1`
                        	    do
		                            motr_dep=`echo $(rpm -qpR ${component} | grep -E "cortx-motr =") | cut -d= -f2 | tr -d '\040\011\012\015'`
                		            if [ -z "$motr_dep" ]
		                            then
                		                echo "\033[1;33m $component has no dependency to motr - Validation Success \033[0m "
		                            else
                		            if [ "$motr_dep" = "$motr_rpm_release_version" ]; then
                                		echo "\033[1;32m $component motr version  ( $motr_dep ) matches with integration motr rpm ( $motr_rpm_release_version ) Good to Go - Validation Success \033[0m "
                                	    else
                                                echo "\033[1;31m $component motr version ( $motr_dep ) mismatchs with integration motr rpm ( $motr_rpm_release_version ) - Validation Failed \033[0m"
                                    
            		                    mv "$integration_dir/$release_name" "$integration_dir/${release_name}-do-not-use"
                        	            exit 1
                                	    fi
                            		    fi
	                           done
           	                   popd
                    		   done
                		   '''
			}
		}

		stage ('Sign rpm') {
			steps {
                	script { build_stage = env.STAGE_NAME }

	                sh label: 'Preparation', script: '''
        	            pushd scripts/rpm-signing
                            cat gpgoptions >>  ~/.rpmmacros
                            sed -i 's/passphrase/'${passphrase}'/g' genkey-batch
                            gpg --batch --gen-key genkey-batch
 	                    popd
                            gpg --export -a 'Seagate'  > RPM-GPG-KEY-Seagate
            	            rpm --import RPM-GPG-KEY-Seagate
		 	'''

                	sh label: 'Sign rpm', script: '''
	                    cp RPM-GPG-KEY-Seagate $integration_dir/$release_name/cortx_build_temp/dev
        	            cp RPM-GPG-KEY-Seagate $integration_dir/$release_name/cortx_build_temp/prod
                	    pushd scripts/rpm-signing
                        	chmod +x rpm-sign.sh
	                        for rpm in `ls -1 $integration_dir/$release_name/cortx_build_temp/dev/*.rpm`
        	                do
                	            ./rpm-sign.sh ${passphrase} $rpm
                        	done

	                        for rpm in `ls -1 $integration_dir/$release_name/cortx_build_temp/prod/*.rpm`
        	                do
                	            ./rpm-sign.sh ${passphrase} $rpm
                        	done
	                    popd
        	        '''
			}
		}

	        stage ('Host RRPM (Create Repo)') {
			steps {
        	        script { build_stage = env.STAGE_NAME }
                	sh label: 'Repo Creation', script: '''
	                    pushd $integration_dir/$release_name/cortx_build_temp/dev
        	            rpm -qi createrepo || yum install -y createrepo
                	    createrepo .
	                    popd	
        	            pushd $integration_dir/$release_name/cortx_build_temp/prod
                	    rpm -qi createrepo || yum install -y createrepo
	                    createrepo .
        	            popd
                	'''		
            		}
		}

        
	        stage ('Release cortx_build') {
        	    steps {
                	script { build_stage = env.STAGE_NAME }
	                sh label: 'Release cortx_build', script: '''
				mkdir -p $cortx_build_dir
	                        pushd $cortx_build_dir
                                test -d $release_name && rm -f $release_name
                                mkdir $release_name && pushd $release_name
                                ln -s $integration_dir/$release_name/cortx_build_temp/prod cortx_iso
                                ln -s $thrid_party_dir 3rd_party
				ln -s $python_deps python_deps
                        	popd
	                        popd
            	    '''
			}
        	}

		stage ('Build RELEASE.INFO') {
			steps {
                	script { build_stage = env.STAGE_NAME }
	                sh label: 'Build MANIFEST', script: """
                    
        	            pushd scripts/release_support

                            sh build_release_info.sh $integration_dir/$release_name/cortx_build_temp/dev                    
                    	    sh build_readme.sh $integration_dir/$release_name
                            sh build-3rdParty-release-info.sh $cortx_build_dir/$release_name/3rd_party
                    
                    	    popd

	                    cp $integration_dir/$release_name/README.txt .
        	            cp $integration_dir/$release_name/cortx_build_temp/dev/RELEASE.INFO .
                	"""		
	                 withCredentials([string(credentialsId: 'shailesh-github-token', variable: 'ACCESS_TOKEN')]) {
        	            sh label: 'Generate Changelog', script: """
				    pushd scripts/release_support
        	                    sh +x changelog.sh ${currentBuild.previousBuild.getNumber()} ${currentBuild.number} ${ARTIFACT_LOCATION} ${ACCESS_TOKEN}
       				    popd
				    cp /root/git_build_checkin_stats/clone/git-build-checkin-report.txt CHANGESET.txt 
	                            cp CHANGESET.txt $integration_dir/$release_name/cortx_build_temp/dev
            	        	    cp CHANGESET.txt $integration_dir/$release_name/cortx_build_temp/prod
                	    """	
             		}
            		}
		}
		
		
	        stage ('Generate ISO Image') {
		    steps {
		        sh label: 'Generate ISO Image', script:'''
		        rpm -q genisoimage || yum install genisoimage -y
        	        mkdir $integration_dir/$release_name/prod && pushd $integration_dir/$release_name/prod
				genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o cortx-$version-$BUILD_NUMBER.iso $integration_dir/$release_name/cortx_build_temp/prod
				
				genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o cortx-$version-$BUILD_NUMBER-single.iso $cortx_build_dir/$release_name
				
                
                	cortx_prvsnr_preq=$(ls "$cortx_build_dir/$release_name/cortx_iso" | grep "python36-cortx-prvsnr" | cut -d- -f5 | cut -d_ -f2 | cut -d. -f1 | sed s/"git"//)
	                wget -O cortx-prep-$version-$BUILD_NUMBER.sh https://raw.githubusercontent.com/Seagate/cortx-prvsnr/$cortx_prvsnr_preq/cli/src/cortx_prep.sh
        	        popd
                
	                cp -r $integration_dir/$release_name/cortx_build_temp/dev $integration_dir/$release_name/dev
	                ln -s $cortx_os_iso $integration_dir/$release_name/prod/$(basename $cortx_os_iso)

        	        cp $cortx_build_dir/$release_name/3rd_party/THIRD_PARTY_RELEASE.INFO $integration_dir/$release_name
			cp $integration_dir/$release_name/dev/RELEASE.INFO $integration_dir/$release_name
			sed -i '/BUILD/d' $cortx_build_dir/$release_name/3rd_party/THIRD_PARTY_RELEASE.INFO
				
	
			mv $cortx_build_dir/$release_name/ $cortx_build_dir/$release_tag-to-be-deleted
			rm -rf $integration_dir/$release_name/cortx_build_temp
		        '''
		    }
		}
		stage ('Tag last_successful') {
			steps {
                	script { build_stage = env.STAGE_NAME }
	                sh label: 'Tag last_successful', script: '''
	                    pushd $integration_dir/
	                    test -d $integration_dir/${release_component}_last_successful && rm -f ${release_component}_last_successful
        	            ln -s $integration_dir/$release_name/dev ${release_component}_last_successful
                	    popd
	                '''
			}
		}


		
        	stage ("Deploy") {
	            when { expression { false } }
        	    steps {
                	script { build_stage = env.STAGE_NAME }
				script {
                			build job: 'Release_Engineering/automated-vm-deployment', wait: false, propagate: false, parameters: [string(name: 'build', value: "${release_name}")]
             		}
        	    	}
	        }	
	}
    
    post {
	always {
            script {
                	
                currentBuild.upstreamBuilds?.each { b -> env.upstream_project = "${b.getProjectName()}";env.upstream_build = "${b.getId()}" }
                env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$pipeline_group/$os_version/$release_name"
                env.release_build = "${env.release_name}"
                env.build_stage = "${build_stage}"

                def mailRecipients = ""
                emailext ( 
                    body: '''${SCRIPT, template="release-email.template"}''',
                    mimeType: 'text/html',
                    subject: "Main Release # ${env.release_name} - ${currentBuild.currentResult}",
                    //attachmentsPattern: 'CHANGESET.txt',
                    attachLog: true,
                    to: "${mailRecipients}",
                )

                archiveArtifacts artifacts: "README.txt, RELEASE.INFO", onlyIfSuccessful: false, allowEmptyArchive: true
            }
        }
    }
}
