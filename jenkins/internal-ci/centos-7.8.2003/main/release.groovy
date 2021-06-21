#!/usr/bin/env groovy
pipeline {
	 	 
    agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	
    environment {
        version = "2.0.0"
        third_party_version = "2.0.0-latest"
        os_version = "centos-7.8.2003"
        branch = "main"
        release_dir = "/mnt/bigstorage/releases/cortx"
        integration_dir = "$release_dir/github/$branch/$os_version"
        components_dir = "$release_dir/components/github/$branch/$os_version"
        release_tag = "$BUILD_NUMBER"
        BUILD_TO_DELETE = ""
        passphrase = credentials('rpm-sign-passphrase')
        ARTIFACT_LOCATION = "http://cortx-storage.colo.seagate.com/releases/cortx/github/$branch/$os_version"
        third_party_dir = "$release_dir/third-party-deps/centos/centos-7.8.2003-$third_party_version/"
		python_deps = "$release_dir/third-party-deps/python-deps/python-packages-2.0.0-latest"
        cortx_os_iso = "/mnt/bigstorage/releases/cortx_builds/custom-os-iso/cortx-os-1.0.0-23.iso"
        // WARNING : 'rm' command where used in this dir path, be conscious while changing the value  
		cortx_build_dir = "$release_dir/github/$branch/$os_version/cortx_builds" 
    }
	
	options {
		timeout(time: 120, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')
		disableConcurrentBuilds()  
	}
		
	stages {	
	
		stage('Install Dependecies') {
			steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Installed Dependecies', script: '''
                    yum install -y expect rpm-sign rng-tools genisoimage python3-pip
                    systemctl start rngd
                '''	
			}
		}

        stage('Checkout Release scripts') {
			steps {
        	    script { build_stage = env.STAGE_NAME }
                checkout([$class: 'GitSCM', branches: [[name: 'main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re.git']]])
			}
		}
			
		stage ('Collect Component RPMS') {
			steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Copy RPMS', script:'''
                    for env in "dev";
                    do
                        mkdir -p $integration_dir/$release_tag/$env
                        pushd $components_dir/$env
                        for component in  `ls -1 | grep -Evx 'cortx-extension'`
                        do
                            echo -e "Copying RPM's for $component"
                            if ls $component/last_successful/*.rpm 1> /dev/null 2>&1; then
                                cp $component/last_successful/*.rpm $integration_dir/$release_tag/$env
                            fi
                        done
                        popd
                    done

                    mkdir -p $integration_dir/$release_tag/prod
                    cp -n -r $integration_dir/$release_tag/dev/* $integration_dir/$release_tag/prod/

                    pushd $integration_dir/$release_tag/prod
                        rm -f *-debuginfo-*.rpm 
                        rm -f cortx-s3iamcli*.rpm
                        rm -f cortx-s3-test*.rpm
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
                    echo "VALIDATING $env RPM'S................"
                    echo "-------------------------------------"
                    pushd $integration_dir/$release_tag/$env
                    motr_rpm=$(ls -1 | grep "cortx-motr-$version")
                    motr_rpm_release=`rpm -qp ${motr_rpm} --qf '%{RELEASE}' | tr -d '\040\011\012\015'`
                    motr_rpm_version=`rpm -qp ${motr_rpm} --qf '%{VERSION}' | tr -d '\040\011\012\015'`
                    motr_rpm_release_version="${motr_rpm_version}-${motr_rpm_release}"
                    for component in `ls -1`
                    do
                        motr_dep=`echo $(rpm -qpR ${component} | grep -E "cortx-motr =") | cut -d= -f2 | tr -d '\040\011\012\015'`
                        if [ -z "$motr_dep" ]
                        then
                            echo "\033[1;33m $component has no dependency to Motr - Validation Success \033[0m "
                        else
                            if [ "$motr_dep" = "$motr_rpm_release_version" ]; then
                                echo "\033[1;32m $component Motr version matches with integration Motr rpm ($motr_rpm_release_version) Good to Go - Validation Success \033[0m "
                            else
                                echo "\033[1;31m $component Motr version ( $motr_dep ) mismatchs with integration Motr rpm ( $motr_rpm_release_version ) - Validation Failed \033[0m"		
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
                    for env in "dev" "prod";
                    do
                        pushd scripts/rpm-signing
                            chmod +x rpm-sign.sh
                            cp RPM-GPG-KEY-Seagate $integration_dir/$release_tag/$env/
                            for rpm in `ls -1 $integration_dir/$release_tag/$env/*.rpm`
                            do
                            ./rpm-sign.sh ${passphrase} $rpm
                            done
					    popd
                    done    
                '''
			}
		}
				
		stage ('Repo Creation') {
			steps {
                script { build_stage = env.STAGE_NAME }
        
                sh label: 'Repo Creation', script: '''

                    for env in "dev" "prod";
                    do
                        pushd $integration_dir/$release_tag/$env/
                            rpm -qi createrepo || yum install -y createrepo
                            createrepo .
                        popd
                    done
                    
                '''
			}
		}	

        stage('Release cortx_build') {
            steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Release cortx_build', script: '''
					mkdir -p $cortx_build_dir
					pushd $cortx_build_dir
                        test -d $release_tag && rm -f $release_tag
                        mkdir $release_tag && pushd $release_tag
                            ln -s $(readlink -f $third_party_dir) 3rd_party
                            ln -s $(readlink -f $python_deps) python_deps
                        popd
                    popd
                '''
			}
        }
		
		stage ('Build Release Info') {
			steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Build Release Info', script: """
				    pushd scripts/release_support
                        sh build_release_info.sh -b $branch -v $version -l $integration_dir/$release_tag/dev -t $cortx_build_dir/$release_tag/3rd_party
                        sh build_release_info.sh -b $branch -v $version -l $integration_dir/$release_tag/prod -t $cortx_build_dir/$release_tag/3rd_party
						sh build_readme.sh $integration_dir/$release_tag
					popd
					
					cp $integration_dir/$release_tag/README.txt .
                    cp $integration_dir/$release_tag/dev/RELEASE.INFO .
					
                """
                sh label: 'Generate Changelog', script: """
                    pushd scripts/release_support
                        sh +x changelog.sh ${currentBuild.previousBuild.getNumber()} ${currentBuild.number} ${ARTIFACT_LOCATION}
                    popd
                    cp /root/git_build_checkin_stats/clone/git-build-checkin-report.txt CHANGESET.txt 
                    cp CHANGESET.txt $integration_dir/$release_tag/dev
                    cp CHANGESET.txt $integration_dir/$release_tag/prod
                """
			}
		}
		

		stage ('Generate Release ISO') {
		    steps {

                sh label: 'Release ISO', script: '''
				mkdir -p $cortx_build_dir/$release_tag/cortx_iso
		        mv $integration_dir/$release_tag/prod/* $cortx_build_dir/$release_tag/cortx_iso
                mkdir -p $integration_dir/$release_tag/prod/iso
                
                genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -hide-rr-moved -publisher Seagate -o $integration_dir/$release_tag/prod/iso/cortx-$version-$BUILD_NUMBER-single.iso $cortx_build_dir/$release_tag
                '''

                sh label: 'Upgrade ISO', script: '''
                #Create upgrade directorty structure
                mkdir -p $cortx_build_dir/$release_tag/sw_upgrade/{3rd_party,cortx_iso,python_deps}
                createrepo -v $cortx_build_dir/$release_tag/sw_upgrade/3rd_party/
                find $cortx_build_dir/$release_tag/3rd_party/ -not -path '*repodata*' -type d  -printf '%P\n' | xargs -t -I % sh -c '{ mkdir -p $cortx_build_dir/$release_tag/sw_upgrade/3rd_party/%; createrepo -v $cortx_build_dir/$release_tag/sw_upgrade/3rd_party/%; }'
		        
                #Copy all component packages
                cp -r $cortx_build_dir/$release_tag/cortx_iso/* $cortx_build_dir/$release_tag/sw_upgrade/cortx_iso
                
                #Copy RELEASE.INFO, Third Party RPM and Python index files.
                cp $cortx_build_dir/$release_tag/3rd_party/THIRD_PARTY_RELEASE.INFO $cortx_build_dir/$release_tag/sw_upgrade/3rd_party
                sed -i -e /tar/d -e /rpm/d -e /tgz/d $cortx_build_dir/$release_tag/sw_upgrade/3rd_party/THIRD_PARTY_RELEASE.INFO
				cp $cortx_build_dir/$release_tag/python_deps/index.html $cortx_build_dir/$release_tag/sw_upgrade/python_deps/index.html
				sed -i /href/d $cortx_build_dir/$release_tag/sw_upgrade/python_deps/index.html
				cp $cortx_build_dir/$release_tag/cortx_iso/RELEASE.INFO $cortx_build_dir/$release_tag/sw_upgrade/
                
                genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -hide-rr-moved -publisher Seagate -o $integration_dir/$release_tag/prod/iso/cortx-$version-$BUILD_NUMBER-upgrade.iso $cortx_build_dir/$release_tag/sw_upgrade
                rm -rf $cortx_build_dir/$release_tag/sw_upgrade
                
                '''
                sh label: "Sign ISO files", script: '''
                pushd scripts/rpm-signing
                    ./file-sign.sh ${passphrase} $integration_dir/$release_tag/prod/iso/cortx-$version-$BUILD_NUMBER-upgrade.iso
                    pkill gpg-agent
                    ./file-sign.sh ${passphrase} $integration_dir/$release_tag/prod/iso/cortx-$version-$BUILD_NUMBER-single.iso 
                popd
                '''

		        sh label: 'Additional Files', script:'''
                cortx_prvsnr_preq=$(ls "$cortx_build_dir/$release_tag/cortx_iso" | grep "python36-cortx-prvsnr" | cut -d- -f5 | cut -d_ -f2 | cut -d. -f1 | sed s/"git"//)
                    
                wget -O $integration_dir/$release_tag/prod/iso/cortx-prep-$version-$BUILD_NUMBER.sh https://raw.githubusercontent.com/Seagate/cortx-prvsnr/$cortx_prvsnr_preq/cli/src/cortx_prep.sh

                ln -s $cortx_os_iso $integration_dir/$release_tag/prod/iso/$(basename $cortx_os_iso)
 
                mv $cortx_build_dir/$release_tag/* $integration_dir/$release_tag/prod
                cp $integration_dir/$release_tag/prod/*/*.INFO $integration_dir/$release_tag/prod
                		
                rm -rf "$cortx_build_dir/$release_tag"
		        '''
		    }
		}
    		
		stage ('Tag last_successful') {
			steps {
                script { build_stage = env.STAGE_NAME }
                sh label: 'Tag last_successful', script: '''
                    pushd $integration_dir
                    test -L last_successful && rm -f last_successful
                    test -L last_successful_prod && rm -f last_successful_prod
                    ln -s $integration_dir/$release_tag/dev last_successful
                    ln -s $integration_dir/$release_tag/prod last_successful_prod
                    popd
                '''
			}
		}

        stage ("Deploy") {
            steps {
                script { build_stage = env.STAGE_NAME }
				script {
                    build job: 'Main Deploy 1N', propagate: false, wait: false, parameters: [
                            string(name: 'CORTX_BUILD', value: "http://cortx-storage.colo.seagate.com/releases/cortx/github/${branch}/${os_version}/${env.release_tag}/prod"),
                            booleanParam(name: 'CREATE_JIRA_ISSUE_ON_FAILURE', value: true),
                            booleanParam(name: 'AUTOMATED', value: true)
                        ]
                    build job: 'Main Deploy 3N', propagate: false, wait: false, parameters: [
                            string(name: 'CORTX_BUILD', value: "http://cortx-storage.colo.seagate.com/releases/cortx/github/${branch}/${os_version}/${env.release_tag}/prod"),
                            booleanParam(name: 'CREATE_JIRA_ISSUE_ON_FAILURE', value: true),
                            booleanParam(name: 'AUTOMATED', value: true)
                        ]         
				}
            }
        }
	}
	
	post {
	
		always {
            script {
                	
                currentBuild.upstreamBuilds?.each { b -> env.upstream_project = "${b.getProjectName()}";env.upstream_build = "${b.getId()}" }
                env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/cortx/github/${branch}/${os_version}/${env.release_tag}"
                env.release_build = "${env.release_tag}"
                env.build_stage = "${build_stage}"

                def toEmail = "shailesh.vaidya@seagate.com"
                
                emailext ( 
                        body: '''${SCRIPT, template="release-email.template"}''',
                        mimeType: 'text/html',
                        subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
                        attachLog: true,
                        to: toEmail,
                        attachmentsPattern: 'CHANGESET.txt'
                    )

				archiveArtifacts artifacts: "README.txt, RELEASE.INFO, CHANGESET.txt", onlyIfSuccessful: false, allowEmptyArchive: true
            }
        }
    }
}
