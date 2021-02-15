pipeline {

	agent {
		node {
			label 'docker-cp-centos-7.8.2003-node'
		}
	}
	environment {
		SPACE = sh(script: "df -h | grep /mnt/data1/releases", , returnStdout: true).trim()
	}
	 triggers {
         cron('0 */6 * * *')
    }
	stages {
		stage ('CheckMount') {
		    steps {
				sh label: 'CheckMount', script: '''#!/bin/bash
		        	mount="cortx-storage.colo.seagate.com:/mnt/data1/releases"
				if grep -qs "$mount" /proc/mounts;then
				echo "cortx-storage.colo.seagate.com:/mnt/data1/releases is mounted."
				else
				echo "cortx-storage.colo.seagate.com:/mnt/data1/releases is not mounted."
				mount -t nfs4 "$mount" /mnt/data1/releases
					if [ $? -eq 0 ]; then
					echo "Mount success!"
					else
					echo "Something went wrong with the mount..."
					currentBuild.result = 'ABORTED'
					fi
				fi
			'''	
		}
	}
		
		stage ('Threshold alert') {
					steps {
						sh label: 'Threshold alert', script: '''#!/bin/bash
						CURRENT=$(df -h | grep /mnt/data1/releases | awk '{print $5}' | sed 's/%//g')
					        THRESHOLD=70
						echo "The Current disk space is $CURRENT "
						if [ "$CURRENT" -gt "$THRESHOLD" ] ; then
						echo Your /mnt/data1/releases partition remaining free space is critically low. Used: $CURRENT%. Threshold: $THRESHOLD%  So, 30 days older files will be deleted $(date)
						fpath=/mnt/data1/releases
						source /mnt/data1/releases/exclude_build.txt
						
						#Backup of exclude builds
						find $build -path $path1 -path $path2 -prune -false -o -name '*' -exec cp {} /mnt/data1/releases/backups/cortx_build_backup/custom_build_backup \\;
						
						find $fpath -maxdepth 1 ! -type l -print | cut -c1- | grep -v "\\#" &&  find $build -path $path1 -path $path2 -prune -false -o -name '*' && find $fpath ! -name '*.INFO*' && find $fpath -type f -mtime +30  -exec rm -rf {} \\;
						
						fi
					'''
				}
			}
		}
	post {
		always {
			script {
			        emailext (
					body: "Current Disk Space is ${env.SPACE} : Job ${env.JOB_NAME} : Build URL ${env.BUILD_URL}",
					subject: "[Jenkins Build ${currentBuild.currentResult}] : ${env.JOB_NAME} : build ${env.BUILD_NUMBER}",
					to: 'CORTX.DevOps.RE@seagate.com',
					)
			}
		}
	}
}



