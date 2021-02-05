pipeline {

	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}

	environment {
		version = "2.0.0"
		branch = "custom-ci"
		os_version = "centos-7.8.2003"
		thrid_party_version = "2.0.0-1"
		release_dir = "/mnt/bigstorage/releases/cortx"
		integration_dir = "$release_dir/github/integration-custom-ci/release/$os_version"
		components_dir = "$release_dir/components/github/$branch/$os_version"
		release_tag = "custom-build-$BUILD_ID"
		passphrase = credentials('rpm-sign-passphrase')
		thrid_party_dir = "$release_dir/third-party-deps/centos/centos-7.8.2003-$thrid_party_version/"
		python_deps = "$release_dir/third-party-deps/python-packages"
		cortx_os_iso = "/mnt/bigstorage/releases/cortx_builds/custom-os-iso/cortx-os-1.0.0-23.iso"
	}

	options {
		timeout(time: 120, unit: 'MINUTES')
		timestamps()
		disableConcurrentBuilds()
		ansiColor('xterm')
		parallelsAlwaysFailFast()
	}

	parameters {
		string(name: 'CSM_AGENT_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for CSM Agent', trim: true)
		string(name: 'CSM_AGENT_URL', defaultValue: 'https://github.com/Seagate/cortx-manager', description: 'CSM_AGENT Repository URL', trim: true)
		string(name: 'CSM_WEB_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for CSM Web', trim: true)
		string(name: 'CSM_WEB_URL', defaultValue: 'https://github.com/Seagate/cortx-management-portal', description: 'CSM WEB Repository URL', trim: true)
		string(name: 'HARE_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for Hare', trim: true)
		string(name: 'HARE_URL', defaultValue: 'https://github.com/Seagate/cortx-hare', description: 'Hare Repository URL', trim: true)
		string(name: 'HA_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for Cortx-HA', trim: true)
		string(name: 'HA_URL', defaultValue: 'https://github.com/Seagate/cortx-ha.git', description: 'Cortx-HA Repository URL', trim: true)
		string(name: 'MOTR_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for Motr', trim: true)
		string(name: 'MOTR_URL', defaultValue: 'https://github.com/Seagate/cortx-motr.git', description: 'Motr Repository URL', trim: true)
		string(name: 'PRVSNR_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for Provisioner', trim: true)
		string(name: 'PRVSNR_URL', defaultValue: 'https://github.com/Seagate/cortx-prvsnr.git', description: 'Provisioner Repository URL', trim: true)
		string(name: 'S3_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for S3Server', trim: true)
		string(name: 'S3_URL', defaultValue: 'https://github.com/Seagate/cortx-s3server.git', description: 'S3Server Repository URL', trim: true)
		string(name: 'SSPL_BRANCH', defaultValue: 'main', description: 'Branch or GitHash for SSPL', trim: true)
		string(name: 'SSPL_URL', defaultValue: 'https://github.com/Seagate/cortx-monitor.git', description: 'SSPL Repository URL', trim: true)

		choice(
			name: 'OTHER_COMPONENT_BRANCH',
			choices: ['main', 'stable', 'cortx-1.0'],
			description: 'Branch name to pick-up other components rpms'
		)
	}

	stages {

		stage ("Trigger Component Jobs") {
			parallel {
				stage ("Build Mero, Hare and S3Server") {
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							try {
								def motrbuild = build job: 'motr-custom-build', wait: true,
										parameters: [
														string(name: 'MOTR_URL', value: "${MOTR_URL}"),
														string(name: 'MOTR_BRANCH', value: "${MOTR_BRANCH}"),
														string(name: 'S3_URL', value: "${S3_URL}"),
														string(name: 'S3_BRANCH', value: "${S3_BRANCH}"),
														string(name: 'HARE_URL', value: "${HARE_URL}"),
														string(name: 'HARE_BRANCH', value: "${HARE_BRANCH}")
                                            		]
							} catch (err) {
								build_stage = env.STAGE_NAME 			
								error "Failed to Build Motr, Hare and S3Server"
							}
						}										
					}
				}

				stage ("Build Provisioner") {
					steps {
						script { build_stage = env.STAGE_NAME }
                                                script {
                                                        try {
								def prvsnrbuild = build job: 'prvsnr-custom-build', wait: true,
								                  parameters: [
									          	string(name: 'PRVSNR_URL', value: "${PRVSNR_URL}"),
											string(name: 'PRVSNR_BRANCH', value: "${PRVSNR_BRANCH}")
							        	          ]
							} catch (err) {
								build_stage = env.STAGE_NAME
								error "Failed to Build Provisioner"
							}
						}
					}
				}

				stage ("Build HA") {
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							try {					
								sh label: 'Copy RPMS', script:'''
								if [ "$HA_BRANCH" == "Cortx-v1.0.0_Beta"  ]; then
									echo "cortx-ha does not have Cortx-v1.0.0_Beta branch."
									exit 1
								fi
								'''
								def habuild = build job: 'cortx-ha', wait: true,
									      parameters: [
									      	  string(name: 'HA_URL', value: "${HA_URL}"),
									      	  string(name: 'HA_BRANCH', value: "${HA_BRANCH}")
									      ]
							} catch (err) {
								build_stage = env.STAGE_NAME
								error "Failed to Build HA"
							}
						}
					}
				}

				stage ("Build CSM Agent") {
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							try {
								def csm_agent_build = build job: 'custom-csm-agent-build', wait: true,
										      parameters: [
										      	  	string(name: 'CSM_AGENT_URL', value: "${CSM_AGENT_URL}"),
						                        	string(name: 'CSM_AGENT_BRANCH', value: "${CSM_AGENT_BRANCH}")
										      ]
							} catch (err) {
								build_stage = env.STAGE_NAME
								error "Failed to Build CSM Agent"
							}
						}                        
					}
				}	
					
				stage ("Build CSM Web") {
					steps {
						script { build_stage = env.STAGE_NAME }	
						script {
							try {	
								def csm_web_build = build job: 'custom-csm-web-build', wait: true,
										    parameters: [
										        string(name: 'CSM_WEB_URL', value: "${CSM_WEB_URL}"),
												string(name: 'CSM_WEB_BRANCH', value: "${CSM_WEB_BRANCH}")
										    ]
							} catch (err) {
								build_stage = env.STAGE_NAME
								error "Failed to Build CSM Web"
							}
						}
					}
				}

				stage ("Build SSPL") {
					steps {
						script { build_stage = env.STAGE_NAME }
						script {
							try {	
								def ssplbuild = build job: 'sspl-custom-build', wait: true,
										parameters: [
											string(name: 'SSPL_URL', value: "${SSPL_URL}"),
											string(name: 'SSPL_BRANCH', value: "${SSPL_BRANCH}")
										]
							} catch (err) {
								build_stage = env.STAGE_NAME
								 error "Failed to Build SSPL"
							}
						}
					}
				}
			}
		}

		stage('Install Dependecies') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Installed Dependecies', script: '''
					yum install -y expect rpm-sign rng-tools genisoimage
					systemctl start rngd
					'''
				}
		}

		stage ('Collect Component RPMS') {
			steps {
				script { build_stage = env.STAGE_NAME }
				sh label: 'Copy RPMS', script:'''
					if [ "$OTHER_COMPONENT_BRANCH" == "stable"  ]; then
						RPM_COPY_PATH="/mnt/bigstorage/releases/cortx/components/github/stable/$os_version/dev/"
					elif [ "$OTHER_COMPONENT_BRANCH" == "main"  ]; then
						RPM_COPY_PATH="/mnt/bigstorage/releases/cortx/components/github/main/$os_version/dev/"
					elif [ "$OTHER_COMPONENT_BRANCH" == "Cortx-v1.0.0_Beta"  ]; then
						RPM_COPY_PATH="/mnt/bigstorage/releases/cortx/components/github/Cortx-v1.0.0_Beta/$os_version/dev/"
					elif [ "$OTHER_COMPONENT_BRANCH" == "cortx-1.0"  ]; then
						RPM_COPY_PATH="/mnt/bigstorage/releases/cortx/components/github/cortx-1.0/$os_version/dev/"
					else
						RPM_COPY_PATH="/mnt/bigstorage/releases/cortx/components/github/custom-ci/release/$os_version/dev"
					fi

					if [ "$CSM_BRANCH" == ""Cortx-v1.0.0_Beta"" ]; then
						CUSTOM_COMPONENT_NAME="motr|s3server|hare|cortx-ha|provisioner|csm|sspl"
					else
						CUSTOM_COMPONENT_NAME="motr|s3server|hare|cortx-ha|provisioner|csm-agent|csm-web|sspl"
					fi

					for env in "dev" ;
                    do
						test -d $integration_dir/$release_tag/cortx_iso/ && rm -rf $integration_dir/$release_tag/cortx_iso/
						mkdir -p $integration_dir/$release_tag/cortx_iso/
						pushd $components_dir/$env
							echo $CUSTOM_COMPONENT_NAME
							echo $CUSTOM_COMPONENT_NAME | tr "|" "\n"
							for component in $(echo $CUSTOM_COMPONENT_NAME | tr "|" "\n")
								do
								echo -e "Copying RPM's for $component"
								if ls $component/last_successful/*.rpm 1> /dev/null 2>&1; then
									mv $component/last_successful/*.rpm $integration_dir/$release_tag/cortx_iso/
									rm -rf $(readlink $component/last_successful)
									rm -f $component/last_successful
								else
									echo "Packages not available for $component. Exiting"
								exit 1							   
								fi
							done
						popd


						pushd $RPM_COPY_PATH
						for component in `ls -1 | grep -E -v "$CUSTOM_COMPONENT_NAME" | grep -E -v 'luster|halon|mero|motr|csm|cortx-extension'`
						do
							echo -e "Copying RPM's for $component"
							if ls $component/last_successful/*.rpm 1> /dev/null 2>&1; then
								cp $component/last_successful/*.rpm $integration_dir/$release_tag/cortx_iso/
							else
								echo "Packages not available for $component. Exiting"
							exit 1	
							fi
						done
                    done
				'''
			}
		}

		stage('RPM Validation') {
			steps {
                script { build_stage = env.STAGE_NAME }
				sh label: 'Validate RPMS for Motr Dependency', script:'''
                for env in "dev" ;
                do
                    set +x
                    echo "VALIDATING $env RPM'S................"
                    echo "-------------------------------------"
                    pushd $integration_dir/$release_tag/cortx_iso/
					if [ "${CSM_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${HARE_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${MOTR_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${PRVSNR_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${S3_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${SSPL_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
						mero_rpm=$(ls -1 | grep "eos-core" | grep -E -v "eos-core-debuginfo|eos-core-devel|eos-core-tests")
					else
						mero_rpm=$(ls -1 | grep "cortx-motr" | grep -E -v "cortx-motr-debuginfo|cortx-motr-devel|cortx-motr-tests")
					fi
                    mero_rpm_release=`rpm -qp ${mero_rpm} --qf '%{RELEASE}' | tr -d '\040\011\012\015'`
                    mero_rpm_version=`rpm -qp ${mero_rpm} --qf '%{VERSION}' | tr -d '\040\011\012\015'`
                    mero_rpm_release_version="${mero_rpm_version}-${mero_rpm_release}"
                    for component in `ls -1`
                    do
						if [ "${CSM_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${HARE_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${MOTR_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${PRVSNR_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${S3_BRANCH}" == "Cortx-v1.0.0_Beta" ] || [ "${SSPL_BRANCH}" == "Cortx-v1.0.0_Beta" ]; then
							 mero_dep=`echo $(rpm -qpR ${component} | grep -E "eos-core = |mero =") | cut -d= -f2 | tr -d '\040\011\012\015'`
						else	 
							mero_dep=`echo $(rpm -qpR ${component} | grep -E "cortx-motr = |mero =") | cut -d= -f2 | tr -d '\040\011\012\015'`
						fi
                        if [ -z "$mero_dep" ]
                        then
                            echo "\033[1;33m $component has no dependency to mero - Validation Success \033[0m "
                        else
                            if [ "$mero_dep" = "$mero_rpm_release_version" ]; then
                                echo "\033[1;32m $component mero version matches with integration mero rpm($mero_rpm_release_version) Good to Go - Validation Success \033[0m "
                            else
                                echo "\033[1;31m $component mero version mismatchs with integration mero rpm($mero_rpm_release_version) - Validation Failed \033[0m"
                                exit 1
                            fi
                        fi
                    done
                done
                '''
			}
		}

		stage ('Sign rpm') {
			steps {
                script { build_stage = env.STAGE_NAME }
                
				checkout([$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                
                sh label: 'Generate Key', script: '''
                    set +x
					pushd scripts/rpm-signing
                    cat gpgoptions >>  ~/.rpmmacros
                    sed -i 's/passphrase/'${passphrase}'/g' genkey-batch
                    gpg --batch --gen-key genkey-batch
                    gpg --export -a 'Seagate'  > RPM-GPG-KEY-Seagate
                    rpm --import RPM-GPG-KEY-Seagate
					popd
				'''
                sh label: 'Sign RPM', script: '''
                    set +x
					pushd scripts/rpm-signing
                    chmod +x rpm-sign.sh
                    cp RPM-GPG-KEY-Seagate $integration_dir/$release_tag/cortx_iso/
                    
                    for rpm in `ls -1 $integration_dir/$release_tag/cortx_iso/*.rpm`
                    do
                    ./rpm-sign.sh ${passphrase} $rpm
                    done
					popd

                '''
			}
		}
		
		stage ('Repo Creation') {
			steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Repo Creation', script: '''
                    pushd $integration_dir/$release_tag/cortx_iso/
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
			}
		}

		stage ('Link 3rd_party and python_deps') {
			steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Tag Release', script: '''
                    pushd $release_dir/github/integration-custom-ci/release/$os_version/$release_tag
							ln -s $thrid_party_dir 3rd_party
							ln -s $python_deps python_deps
                    popd
                '''
			}
		}

		stage ('Build MANIFEST') {
			steps {
                script { build_stage = env.STAGE_NAME }

                sh label: 'Build MANIFEST', script: """
					pushd scripts/release_support
                    sh build_release_info.sh -v $version -b $integration_dir/$release_tag/cortx_iso/
					sh build-3rdParty-release-info.sh $integration_dir/$release_tag/3rd_party
					sh build_readme.sh $integration_dir/$release_tag
					popd
					
                    cp $integration_dir/$release_tag/README.txt .
                    cp $integration_dir/$release_tag/cortx_iso/RELEASE.INFO .
					cp $integration_dir/$release_tag/3rd_party/THIRD_PARTY_RELEASE.INFO $integration_dir/$release_tag
					cp $integration_dir/$release_tag/cortx_iso/RELEASE.INFO $integration_dir/$release_tag
                """
			}
		}
		
		stage ('Generate ISO Image') {
		    steps {
				
				sh label: 'Generate Single ISO Image', script:'''
		        mkdir $integration_dir/$release_tag/iso && pushd $integration_dir/$release_tag/iso
					genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o cortx-$release_tag-single.iso $integration_dir/$release_tag/
					sed -i '/BUILD/d' $integration_dir/$release_tag/3rd_party/THIRD_PARTY_RELEASE.INFO

					ln -s $cortx_os_iso $(basename $cortx_os_iso)
					cortx_prvsnr_preq=$(ls "$integration_dir/$release_tag/cortx_iso" | grep "python36-cortx-prvsnr" | cut -d- -f5 | cut -d_ -f2 | cut -d. -f1 | sed s/"git"//)
                	wget -O cortx-prep-$release_tag.sh https://raw.githubusercontent.com/Seagate/cortx-prvsnr/$cortx_prvsnr_preq/cli/src/cortx_prep.sh
			
				popd
				'''
				sh label: 'Generate ISO Image', script:'''
		         pushd $integration_dir/$release_tag/iso
					genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o $release_tag.iso $integration_dir/$release_tag/cortx_iso/
				popd
				'''			

				sh label: 'Print Release Build and ISO location', script:'''
				echo "Custom Release Build and ISO is available at,"
					echo "http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/release/$os_version/$release_tag/"
					echo "http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/release/$os_version/$release_tag/iso/$release_tag.iso"
					echo "http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/release/$os_version/$release_tag/iso/$release_tag-single.iso"
		        '''
		    }
		}
	}

	post {

		success {
				sh label: 'Delete Old Builds', script: '''
				set +x
				find /mnt/bigstorage/releases/cortx/github/integration-custom-ci/release/centos-7.8.2003/* -maxdepth 0 -mtime +30 -type d -exec rm -rf {} \\;
				'''
		}
	
		always {
			script {
				env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/integration-custom-ci/release/${env.os_version}/${env.release_tag}"
				env.release_build = "${env.release_tag}"
				env.build_stage = "${build_stage}"
				def recipientProvidersClass = [[$class: 'RequesterRecipientProvider']]
                
                def mailRecipients = "shailesh.vaidya@seagate.com"
                emailext ( 
                    body: '''${SCRIPT, template="release-email.template"}''',
                    mimeType: 'text/html',
                    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
                    attachLog: true,
                    to: "${mailRecipients}",
					recipientProviders: recipientProvidersClass
                )
            }
        }
    }
}
