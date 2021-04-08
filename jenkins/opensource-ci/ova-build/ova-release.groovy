pipeline {
	 	 
    agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	
    parameters {  
		string(name: 'LDR_RELEASE_BUILD', defaultValue: 'http://cortx-storage.colo.seagate.com/releases/cortx_builds/centos-7.8.2003/531/', description: 'LDR Relase build URL.')
	}	

    environment {
		version="1.0.1"
		thrid_party_version = "1.0.0-1"
		os_version="centos-7.8.2003"
		branch="cortx-1.0"
        release_dir="/mnt/bigstorage/releases/cortx"
        integration_dir="/mnt/bigstorage/releases/opensource_builds/ova_builds/$os_version"
        release_tag="ova-build-$BUILD_NUMBER"
        BUILD_TO_DELETE=""
        passphrase = credentials('rpm-sign-passphrase')
        token = credentials('shailesh-github-token')
        ARTIFACT_LOCATION="http://cortx-storage.colo.seagate.com/releases/opensource_builds/ova_builds/$os_version"
		githubrelease_repo="Seagate/cortx"
        thrid_party_dir="$release_dir/third-party-deps/centos/centos-7.8.2003-$thrid_party_version/"
		python_deps="/mnt/bigstorage/releases/cortx/third-party-deps/python-packages"
        cortx_os_iso="/mnt/bigstorage/releases/cortx_builds/custom-os-iso/cortx-os-1.0.0-23.iso"
		iso_location="$release_dir/github/$branch/iso/$os_version"
        csm_web_dir="$release_dir/components/github/ova/$os_version/dev/csm-web/"
    }
	
	options {
		timeout(time: 120, unit: 'MINUTES')
		timestamps()
        ansiColor('xterm')
		disableConcurrentBuilds()  
	}
		
	stages {	

       stage ("Trigger CSM Web job") {
            steps {
				script {
                    def CSM_WEB_HASH = sh(script: '''wget $LDR_RELEASE_BUILD/RELEASE.INFO && grep cortx-csm_web RELEASE.INFO | awk -F['_'] '{print $3}' |  cut -d. -f1''', returnStdout: true).trim()
                
                    def csm_web_build = build job: 'csm-web-ova', wait: true,
                    parameters: [
                        string(name: 'CSM_WEB_BRANCH', value: "${CSM_WEB_HASH}")
                    ]
				}
            }
        }

        stage('Install Dependecies') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Installed Dependecies', script: '''
                    yum install -y expect rpm-sign rng-tools genisoimage python3-pip
					pip3 install githubrelease
                    systemctl start rngd
                '''	
			}
		}

			
		stage ('Collect Component RPMS') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Copy RPMS', script:'''
                    LDR_BUID_PATH=$(sed \'s/http\\:\\/\\/cortx-storage.colo.seagate.com/\\/mnt\\/bigstorage/g\' <<< $LDR_RELEASE_BUILD)
                    mkdir -p $integration_dir/$release_tag/cortx_iso
                    shopt -s extglob
                    cp $LDR_BUID_PATH/cortx_iso/!(ud*|cortx-csm_web*).rpm $integration_dir/$release_tag/cortx_iso
                    cp $csm_web_dir/last_successful/*.rpm $integration_dir/$release_tag/cortx_iso
                '''
			}
		}

        stage('RPM Validation') {
			steps {
                script { build_stage=env.STAGE_NAME }
				sh label: 'Validate RPMS for Motr Dependency', script:'''
                    set +x
                    echo "VALIDATING $env RPM'S................"
                    echo "-------------------------------------"
                    pushd $integration_dir/$release_tag/cortx_iso
                    motr_rpm=$(ls -1 | grep "cortx-motr" | grep -E -v "cortx-motr-debuginfo|cortx-motr-devel|cortx-motr-tests")
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
                '''
			}
		}
		
		stage ('Sign rpm') {
			steps {
                script { build_stage=env.STAGE_NAME }
                
                checkout([$class: 'GitSCM', branches: [[name: '*/main']], doGenerateSubmoduleConfigurations: false, extensions: [[$class: 'AuthorInChangelog']], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'cortx-admin-github', url: 'https://github.com/Seagate/cortx-re']]])
                
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
                        cp RPM-GPG-KEY-Seagate $integration_dir/$release_tag/cortx_iso
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
                script { build_stage=env.STAGE_NAME }
        
                sh label: 'Repo Creation', script: '''
                    pushd $integration_dir/$release_tag/cortx_iso
                    rpm -qi createrepo || yum install -y createrepo
                    createrepo .
                    popd
                '''
			}
		}	

		
		stage ('Tag last_successful') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Tag last_successful', script: '''
                    pushd $integration_dir
                    test -d last_successful && rm -f last_successful
                    ln -s $integration_dir/$release_tag/ last_successful
                    popd
                '''
			}
		}

        stage('Release cortx_build'){
            steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Release cortx_build', script: '''
					pushd $integration_dir/$release_tag
                            ln -s $thrid_party_dir 3rd_party
							ln -s $python_deps python_deps
                    popd
                '''
			}
        }
		
		stage ('Build Release Info') {
			steps {
                script { build_stage=env.STAGE_NAME }
                sh label: 'Build Release Info', script: """
				    pushd scripts/release_support
                        sh build_release_info.sh -b $branch -v $version -l $integration_dir/$release_tag/cortx_iso -t $integration_dir/$release_tag/3rd_party
                        sh build_readme.sh $integration_dir/$release_tag
					popd
					
					cp $integration_dir/$release_tag/README.txt .
                    cp $integration_dir/$release_tag/cortx_iso/RELEASE.INFO .
					
                """
                withCredentials([string(credentialsId: 'shailesh-github-token', variable: 'ACCESS_TOKEN')]) {
                    sh label: 'Generate Changelog', script: """
					    pushd scripts/release_support
                            sh +x changelog.sh ${currentBuild.previousBuild.getNumber()} ${currentBuild.number} ${ARTIFACT_LOCATION} ${ACCESS_TOKEN}
						popd
						cp /root/git_build_checkin_stats/clone/git-build-checkin-report.txt CHANGESET.txt 
                        cp CHANGESET.txt $integration_dir/$release_tag/cortx_iso
                    """
                } 
			}
		}
		
				
		stage ('Generate ISO Image') {
		    steps {
		        sh label: 'Generate ISO Image',script:'''
		        rpm -q genisoimage || yum install genisoimage -y
                mkdir -p $iso_location
		        pushd $iso_location
					genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o $branch-$BUILD_NUMBER.iso $integration_dir/$release_tag/cortx_iso
				popd
				
				genisoimage -input-charset iso8859-1 -f -J -joliet-long -r -allow-lowercase -allow-multidot -publisher Seagate -o cortx-$version-$BUILD_NUMBER-single.iso $integration_dir/$release_tag
				
                mkdir $integration_dir/$release_tag/iso
                ln -s $cortx_os_iso $integration_dir/$release_tag/iso/$(basename $cortx_os_iso)

                cortx_prvsnr_preq=$(ls "$integration_dir/$release_tag/cortx_iso" | grep "python36-cortx-prvsnr" | cut -d- -f5 | cut -d_ -f2 | cut -d. -f1 | sed s/"git"//)
                wget -O $integration_dir/$release_tag/iso/cortx-prep-$version-$BUILD_NUMBER.sh https://raw.githubusercontent.com/Seagate/cortx-prvsnr/$cortx_prvsnr_preq/cli/src/cortx_prep.sh
            
				cp cortx-$version-$BUILD_NUMBER-single.iso $integration_dir/$release_tag/iso
				
				ls $integration_dir/$release_tag/3rd_party/THIRD_PARTY_RELEASE.INFO
				ls $integration_dir/$release_tag/cortx_iso/RELEASE.INFO
				
				cp $integration_dir/$release_tag/3rd_party/THIRD_PARTY_RELEASE.INFO $integration_dir/$release_tag
				cp $integration_dir/$release_tag/cortx_iso/RELEASE.INFO $integration_dir/$release_tag
				sed -i '/BUILD/d' $integration_dir/$release_tag/3rd_party/THIRD_PARTY_RELEASE.INFO
		        '''
		    }
		}


	}
	
	post {
	
		always {
            script {
                	
                currentBuild.upstreamBuilds?.each { b -> env.upstream_project = "${b.getProjectName()}";env.upstream_build = "${b.getId()}" }
                env.release_build_location = "http://cortx-storage.colo.seagate.com/releases/opensource_builds/ova_builds/${os_version}/${env.release_tag}"
                env.release_build = "${env.release_tag}"
                env.build_stage = "${build_stage}"

                def toEmail = "shailesh.vaidya@seagate.com"
                emailext ( 
                    body: '''${SCRIPT, template="release-email.template"}''',
                    mimeType: 'text/html',
                    subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME}",
                    attachLog: true,
                    to: toEmail,
                )

				archiveArtifacts artifacts: "README.txt, RELEASE.INFO, CHANGESET.txt", onlyIfSuccessful: false, allowEmptyArchive: true
            }
        }
    }
}