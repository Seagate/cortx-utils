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

pushd "$source"
if [ -z $count ]; then
   rsync -av --ignore-existing ./"$source" "$destination"
   exit 1
else
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
