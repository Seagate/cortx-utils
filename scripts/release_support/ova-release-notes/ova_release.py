#
# Copyright (c) 2020 Seagate Technology LLC and/or its Affiliates
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# For any questions about this software or licensing,
# please email opensource@seagate.com or cortx-questions@seagate.com.
#

from jira import JIRA
from github_release import gh_release_create
import subprocess
import datetime
import urllib.request
import re
import time
import shutil
import os
import argparse
import sys

#parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('-u', dest='username', type=str, help='JIRA username')
parser.add_argument('-p', dest='password', type=str, help='JIRA password')
parser.add_argument('--build', dest='ova_build_number', type=str, help='OVA build number')
parser.add_argument('--sourceBuild', dest='source_build_number', type=str, help='Source CORTX build number')
parser.add_argument('--targetBuild', dest='target_build_number', type=str, help='Target CORTX build number')
parser.add_argument('--release', dest='github_release', type=str, help='GitHub release number')
parser.add_argument('--highlight', dest='highlight', nargs='+', default=[])
args = parser.parse_args()

#variables
sem_ver = args.github_release
release_repository = 'gauravchaudhari02/release-notes-testing'
jira_base_url = 'https://jts.seagate.com'
jira_issue_base_url = jira_base_url+'/browse/'
releases_url="http://cortx-storage.colo.seagate.com/releases/cortx/github/cortx-1.0/centos-7.8.2003/"
old_ova_path = '/mnt/bigstorage/releases/opensource_builds/ova/cortx-ova-build-'+ args.ova_build_number +'.ova'
new_ova_path = '/mnt/bigstorage/releases/opensource_builds/ova/cortx-va-'+sem_ver+'.ova'
highlight_issues = args.highlight
releasenotes = ""
startReleaseDate = ""
endReleaseDate = ""

#functions
def getReleaseDates():
   url = releases_url + str(args.source_build_number) + '/dev/RELEASE.INFO'
   urllib.request.urlretrieve(url, 'start_build_file.txt')
   url = releases_url + str(args.target_build_number) + '/dev/RELEASE.INFO'
   urllib.request.urlretrieve(url, 'target_build_file.txt')
   startDate = subprocess.getoutput('cat start_build_file.txt | grep DATETIME | awk -F\' \' \'{ print $2 }\' | tr -d \'"\'')
   endDate = subprocess.getoutput('cat target_build_file.txt | grep DATETIME | awk -F\' \' \'{ print $2 }\' | tr -d \'"\'')
   global startReleaseDate 
   startReleaseDate = datetime.datetime.strptime(startDate, "%d-%b-%Y").strftime("%Y-%m-%d %H:%M")
   global endReleaseDate 
   endReleaseDate = datetime.datetime.strptime(endDate, "%d-%b-%Y").strftime("%Y-%m-%d %H:%M")

#collect jira issues data and create release-notes
jira = JIRA(basic_auth=(args.username,args.password), options={'server':jira_base_url})

getReleaseDates()
jql = "project = EOS AND (resolutiondate >= '{}' AND resolutiondate <= '{}') ORDER BY component".format(startReleaseDate,endReleaseDate)
print(jql)
block_num = 0
block_size = 500
#loop over issues
while True:

    start_idx = block_num * block_size
    if block_num == 0:
        issues = jira.search_issues(jql, start_idx, block_size)
    else:
        more_issue = jira.search_issues(jql, start_idx, block_size)
        if len(more_issue)>0:
            for x in more_issue:
                issues.append(x)
        else:
            break
    if len(issues) == 0:
        # Retrieve issues until there are no more to come
        break
    block_num += 1

print(len(issues))

releasenotes = "## Features\n\n"
for issue in issues:
   if issue.fields.issuetype.name in ['Task','Story'] and issue.key not in highlight_issues and issue.fields.components:
      releasenotes+=str("- {} : {} [[{}]]({})\n".format(issue.fields.components[0],issue.fields.summary,issue.key,"https://jts.seagate.com/browse/"+issue.key))

releasenotes+="\n"
releasenotes+="## Bugfixes\n\n"
for issue in issues:
   if issue.fields.issuetype.name in ['Bug'] and issue.key not in highlight_issues and issue.fields.components:
      releasenotes+=str("- {} : {} [[{}]]({})\n".format(issue.fields.components[0].name,issue.fields.summary,issue.key,"https://jts.seagate.com/browse/"+issue.key))

if highlight_issues:
   releasenotes+="\n"
   releasenotes+="## Highlights\n\n"
   for issue_id in highlight_issues:
       for issue in issues:
          if issue_id == issue.key and issue.fields.components:
             releasenotes+=str("- {} : {} [[{}]]({})\n".format(issue.fields.components[0].name,issue.fields.summary,issue.key,jira_issue_base_url+issue.key))

releasenotes+="\n"
releasenotes+="## General\n\n"
subprocess.Popen(['../changelog.sh %s %s %s' %(args.source_build_number,args.target_build_number,releases_url)], shell = True)
time.sleep(60)
with open('/root/git_build_checkin_stats/clone/git-build-checkin-report.txt') as f:
    for line in f:
        if re.match(r'^\b[0-9a-f]{7,40}\b', line) and not re.search(r'eos', line, re.IGNORECASE):
               releasenotes+=str("- {}\n".format(line.split('|')[2]))

print(releasenotes)
#publish ova release with release-notes if required ova file is present
if os.path.isfile(old_ova_path):
   shutil.copyfile(old_ova_path,new_ova_path)
   gh_release_create(release_repository,"VA-"+sem_ver,publish=True,body=releasenotes,name="Virtual Appliance "+sem_ver,asset_pattern=new_ova_path)
else:
   sys.exit("ERROR: Required OVA build is not available")
