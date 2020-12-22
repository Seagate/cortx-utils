pipeline {
	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	parameters {
        	string(name: 'os_version', defaultValue: 'centos-7.8.2003', description: 'Operating system for this build')
        }
	
	environment {
		RPM_LOCATION = sh(script: 'date +"%m-%d-%Y"', returnStdout: true).trim()
                version = "1.0.0"
	        thrid_party_version = "1.0.0-1"
                integration_dir = "/mnt/bigstorage/releases/cortx/github/stable"
                nightly_dir = "/mnt/bigstorage/releases/cortx/nightly/"
                cortx_build_dir = "/mnt/bigstorage/releases/cortx/cortx_builds_nightly"
                thrid_party_dir = "/mnt/bigstorage/releases/cortx/third-party-deps/centos/centos-7.8.2003-$thrid_party_version/"
	        python_deps = "/mnt/bigstorage/releases/cortx/third-party-deps/python-packages"
                cortx_os_iso = "/mnt/bigstorage/releases/cortx_builds/custom-os-iso/cortx-os-1.0.0-23.iso"
		
	}
	
	options {
		timeout(time: 60, unit: 'MINUTES') 
	}
		
	triggers { cron('30 19 * * *') }
		
		stages {	

			stage ('Create Dir Structure') {
				steps {
					sh label: 'Create Dir Structure', script: '''
                		        mkdir -p $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")
					'''
				}
			}

	       		stage('Checkout Release scripts') {
				steps {
		                    script { build_stage = env.STAGE_NAME }
                		    checkout([$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
				    }
		    	}

						
			stage ('Nightly Build') {
				steps {
					sh label: 'Copy RPMS', script: '''
                        		echo -e "Copying Integration Build $(readlink $integration_dir/$os_version/last_successful | awk  -F "/" '{print $NF}')"
		                        mkdir -p $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev
                		        cp $integration_dir/$os_version/last_successful/*.rpm $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev
		                        cp  $integration_dir/$os_version/last_successful/RELEASE.INFO  $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev
                		        cp  $integration_dir/$os_version/last_successful/RPM-GPG-KEY-Seagate $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev
		                        mkdir -p $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/prod
                		        cp -r $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev/. $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/prod/
		                        pushd $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/prod
                		        rm -f *-debuginfo-*.rpm
		                        popd
                		        '''
				}
			}
			
			stage ('Repo Creation') {
			    steps {
					sh label: 'Repo Creation', script: '''
                        		pushd $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev
		        	                rpm -qi createrepo || yum install -y createrepo
                			        createrepo .
				        popd
		                        pushd $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/prod
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
                        		    test -d B$BUILD_NUMBER-$(date +"%m-%d-%Y") && rm -f B$BUILD_NUMBER-$(date +"%m-%d-%Y")
		                            mkdir B$BUILD_NUMBER-$(date +"%m-%d-%Y") && pushd B$BUILD_NUMBER-$(date +"%m-%d-%Y")
                		            ln -s $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/prod cortx_iso
		                            ln -s $thrid_party_dir 3rd_party
		                            ln -s $python_deps python_deps
                            		popd
                        		popd
                    			'''
			    }
	            }	

        	    stage ('Generate ISO Image') {
		        steps {
		            sh label: 'Generate ISO Image', script:'''
		            rpm -q genisoimage || yum install genisoimage -y
                	    mkdir $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/prod && pushd $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/prod
	                    genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o cortx-$version-$BUILD_NUMBER.iso $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/prod
			    genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o cortx-$version-$BUILD_NUMBER-single.iso $cortx_build_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")
			    cortx_prvsnr_preq=$(ls "$cortx_build_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_iso" | grep "python36-cortx-prvsnr" | cut -d- -f5 | cut -d_ -f2 | cut -d. -f1 | sed s/"git"//)
        	            wget -O cortx-prep-$version-$BUILD_NUMBER.sh https://raw.githubusercontent.com/Seagate/cortx-prvsnr/$cortx_prvsnr_preq/cli/src/cortx_prep.sh
                	    popd
                
	                    cp -r $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp/dev $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/dev
        	            ln -s $cortx_os_iso $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/prod/$(basename $cortx_os_iso)


			    cp $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/dev/RELEASE.INFO $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")
				
	
			    mv $cortx_build_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/ $cortx_build_dir/$release_tag-to-be-deleted
    	 		    rm -rf $nightly_dir/B$BUILD_NUMBER-$(date +"%m-%d-%Y")/cortx_build_temp
			    '''	
		    }
		}

            
			
	       
	            stage ("Deploy Cortx Stack") {
        	        when { expression { false } }
                	steps {
    				script {
                    		build job: 'Release_Engineering/automated-vm-deployment', wait: false, propagate: false, parameters: [string(name: 'build', value: "B${env.BUILD_NUMBER}-${env.RPM_LOCATION}")]
                  	}
             	   	}
            	  }
        
		}
        post {
	    always {
	            echo 'Cleanup Workspace.'
        	    deleteDir() /* clean up our workspace */
	        }	
        
		success {
        	    emailext (
			subject: "SUCCESSFUL: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
			body: """
			<h><span style=color:green>SUCCESSFUL:</span> Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</h>
			<p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>
			<p>RPM's are located at http://cortx-storage.colo.seagate.com/releases/eos/nightly/B${env.BUILD_NUMBER}-${env.RPM_LOCATION}</p>
			""",
			to: 'eos.nightlybuild@seagate.com',
			recipientProviders: [[$class: 'DevelopersRecipientProvider'], [$class: 'RequesterRecipientProvider']]
			)
			
        	}
		
		failure {
	            emailext (
			subject: "FAILED: Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]'",
			body: """
			<h><span style=color:red>FAILED:</span> Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]':</h>
			<p>Check console output at "<a href="${env.BUILD_URL}">${env.JOB_NAME} [${env.BUILD_NUMBER}]</a>"</p>
			""",
			to: 'shailesh.vaidya@seagate.com',
		
			)
			
 	       }	
    	}
		
}
