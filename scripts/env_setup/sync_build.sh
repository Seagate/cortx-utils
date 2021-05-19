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

#!/bin/bash
helpFunction()
{
   echo ""
   echo "Usage: $0 -s source -d destination -c retention"
   echo -e "\t-s Remote build path"
   echo -e "\t-d Local build path"
   echo -e "\t-c Specify number artifacts for the sync"
   exit 1 # Exit script after printing help
}

while getopts "s:d:c:" opt
do
   case "$opt" in
      s ) source="$OPTARG" ;;
      d ) destination="$OPTARG" ;;
      c ) count="$OPTARG" ;;
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

supported_path=("/mnt/cortx/cortx/third-party-deps/python-packages" "/mnt/cortx/cortx/third-party-deps/centos" \
        "/mnt/cortx/cortx/github/cortx-1.0/centos-7.8.2003" "/mnt/cortx/cortx_builds/centos-7.8.2003")

# todo (need to support stable and main branch)
if [[ ! " ${supported_path[@]} " =~ " ${source} " ]]; then
    echo "Sync will support only cortx-1.0 branch.."
    echo "Supported paths are ${supported_path[@]}"
    exit 1
fi

# Print helpFunction in case parameters are empty
if [ -z "$source" ] || [ -z "$destination" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

if [ ! -d "$source" ]; then
   echo "Error: Remote path '$source' is NOT found."
   exit 1
fi

if [ ! -d "$destination" ]; then
   echo "Warning: Local path '$destination' is NOT found."
   echo "Creating the local path '$destination'..."
   mkdir -p "$destination"
fi

if [ -z $count ]; then
   echo "Syncing the folder $source..."
   echo "Syncing might take time...Please wait....."
   rsync -av --ignore-existing "$source" "$destination"
else
   pushd "$source"
   echo "searching for files to sync"
   #only find last updated artifacts
   folder_list=($(ls -1t | head -n "$count"))
   echo "Folders List: $folder_list"

   for i in "${folder_list[@]}"
   do
     directory=$(echo "$i" | xargs)
     echo "syncing folder $directory, this may take a while"
     rsync -av --ignore-existing ./"$directory" "$destination"
     # rsync -av --update ./"$i" "$DESTDIR" --delete
   done
fi
