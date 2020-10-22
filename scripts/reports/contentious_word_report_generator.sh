#!/bin/bash
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
set +x

REPORT_HEADER="Contentious Word Reference"

if [ -z "$GITHUB_TOKEN" ]
  then
    echo "No argument supplied. Please provide argument 'bash word_search.sh GITHUB_TOKEN REPORT_HEADER (optional)'"
    exit 1
fi


PRODUCT_KEYWORDS=("xyratex" "mero" "eos" "clovis" "udx" "pods" "5u84" "ees" "ecs" "WD" "Fujitsu" "Samsung" "Western Digital" "snowflake")
COMMON_KEYWORDS=("master" "slave" "white" "black" "whitelist" "blacklist" "white list" "black List" "hack" "trash" "garbage" "rubbish" "junk" "crap"  "hate" "meh"  "shit" "damn" "love" "gay" "fag"  "fuck"  "ass"   "bitch" "dick" "bastard" "nigga" "nigger" "dyke" "goddamn" "motherfucker" "cunt" "whore" "retard" "bastard" "idiot")

FULL_SEARCH_KEYWORDS=("whitelist" "blacklist" "clovis" "mero")

GITUB_REPO_QUERY_API="https://api.github.com/orgs/seagate/repos?access_token=${GITHUB_TOKEN}&per_page=100&page=1"

GITHUB_REPOS=(  "Motr:cortx-motr"
                "S3Server:cortx-s3server"
                "Hare:cortx-hare"
                "HA:cortx-ha"
                "CSM:cortx-csm-web,cortx-csm-agent,statsd-utils,cortx-py-utils"
                "NFS:cortx-posix,cortx-fs,cortx-utils,cortx-nsal,cortx-dsal,cortx-fs-ganesha"
                "Provisioner:cortx-prvsnr"  
                "SSPL:cortx-sspl"
                "RE:cortx-re"
                "Motr-Test:castor-integration-tests,engservice-tools,xperior,xperior-perl-libs")

                
TABLE_HTML="<!DOCTYPE html><html><head><style>#search{font-family: 'Trebuchet MS', Arial, Helvetica, sans-serif;
border-collapse: collapse; width: 100%;}#search td, #search th{border: 1px solid #ddd; padding: 8px;}#search tr:nth-child(even)
{background-color: #f2f2f2;}#search tr:hover{background-color: #ddd;}#search th{padding-top: 12px; padding-bottom: 12px;
text-align: center; background-color: #4CAF50; color: white;}</style></head><body><h1>$REPORT_HEADER</h1><table id='search'> <tr> <th>Search Text</th>
<th>File Path</th><th>No of Occurrences</th></tr>TABLE_DATA_SECTION</table></body></html>"

SUMMARY_HTML="<!DOCTYPE html><html><head> <style>#search{font-family: 'Trebuchet MS', Arial, Helvetica, sans-serif; border-collapse: collapse;
width: 100%;}#search td, #search th{border: 1px solid #ddd; padding: 8px;}#search tr:nth-child(even){background-color: #f2f2f2;}#search
tr:hover{background-color: #ddd;}#search th{padding-top: 12px; padding-bottom: 12px; text-align: center; background-color: #4CAF50; color:
white;}</style></head><h1>$REPORT_HEADER Summary</h1><h3>TOTAL_KEYWORD_REF</h3><p>Report Generated on $(date)</p><p style='text-align:right;'>
<i>This stats based on case insensitive keyword search on Seagate org github repositories</i></p>
<body> <table id='search'> <tr> <th rowspan='2'>Component</th><th rowspan='2'>Repository</th>HEADER_SECTION</tr>SUMMARY_DATA_SECTION</table></body></html>"

summary_data=""
summary_total_keyword_count=0
summary_total_file_count=0

_clone_repo(){
    for repo in "${component_repos[@]}"
    do  
            git clone https://$GITHUB_TOKEN@github.com/Seagate/$repo.git
    done
}

_clean_repo(){
    for repo in "${all_repo[@]}"
    do
        rm -rf $repo
    done
}

ALL_KEYWORDS=()
_prepare_summary_report_header(){

    summary_header=""
    ALL_KEYWORDS=( "${PRODUCT_KEYWORDS[@]}" "${COMMON_KEYWORDS[@]}" )
    summary_header+="<th colspan='${#PRODUCT_KEYWORDS[@]}'>Product</th><th colspan='${#COMMON_KEYWORDS[@]}'>Contentious</th><th rowspan='2'>Total No of Occurrences</th><th rowspan='2'>Total Files</th></tr><tr>"
    for keyword in "${ALL_KEYWORDS[@]}"
    do
        summary_header+="<th>"$keyword"</th>" 
    done

    SUMMARY_HTML=${SUMMARY_HTML/HEADER_SECTION/$summary_header}
}

_generate_search_report(){
    
    total_occurrences_count=0
    total_occurrences_file_count=0

    # Generate Repository Report
    for repo_name in ${component_repos[@]}
    do           
        result_html=""
        default_git_branch=$(cd $repo_name && git symbolic-ref --short HEAD)
        git_repo=$(cd $repo_name && git config --get remote.origin.url)
        for keywords in "${ALL_KEYWORDS[@]}"
        do

            GREP_EXTRA_ARG="w"
            for fullsearch_word in "${FULL_SEARCH_KEYWORDS[@]}"
            do
                if [ "$fullsearch_word" == "$keywords" ] ; then
                    GREP_EXTRA_ARG=""
                fi
            done

            echo "Searching for Keyword [ $keywords ] in branch [ $default_git_branch ] with GREP_EXTRA_ARG=$GREP_EXTRA_ARG"
            echo "------------------------------------"
            search_occurrences_count=$(grep -rIio$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | wc -l)
            search_occurrences_file_count=$(grep -rIil$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | wc -l)
            search_result=$(grep -rIil$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | sed "s|.*|<a href=\"$git_repo\/&\" target=\"_blank\">&<\/a>|")
            search_result=$(echo -e ${search_result//$'\n'/<br />})
            search_result=$(echo -e ${search_result} | sed -e "s=/$repo_name.git/$repo_name=/$repo_name/blob/$default_git_branch=g")
            
            occurrences_text="-"
            if [[ $search_occurrences_count -ne 0 ]];
            then 
                occurrences_text="Found $search_occurrences_count occurrences in $search_occurrences_file_count Files"
            fi

            result_html+="<tr class='repo'><td>${keywords}</td><td>$search_result</td><td>$occurrences_text</td></tr>"
            
            echo -e "\t Found $search_occurrences_count in $search_occurrences_file_count file for $keywords in $repo_name"
            echo "------------------------------------"

        done
        
        local_html=${TABLE_HTML/$REPORT_HEADER/$REPORT_HEADER in $repo_name}
        echo ${local_html/TABLE_DATA_SECTION/$result_html} > $repo_name.html
        
        component_cell=""
    done
}

_calculate_summary(){
    
    # Generate Summary Report
    total_search_occurrences_count=0
    total_search_occurrences_file_count=0
    summary_data+="<tr><td>$component_name</td><td>$(printf '%s\n' "${component_repos[@]}" | sed 's/.*/<a href=&.html target="_blank">&<\/a><br \/>/')</td>"
    for keywords in "${ALL_KEYWORDS[@]}"
    do

        GREP_EXTRA_ARG="w"
        for fullsearch_word in "${FULL_SEARCH_KEYWORDS[@]}"
        do
            if [ "$fullsearch_word" == "$keywords" ] ; then
                GREP_EXTRA_ARG=""
            fi
        done

        search_occurrences_count=0
        search_occurrences_file_count=0
        for repo_name in ${component_repos[@]}
        do
            local_search_occurrences_count=0
            local_search_occurrences_file_count=0
            local_search_occurrences_count=$(grep -rIio$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | wc -l)
            local_search_occurrences_file_count=$(grep -rIil$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | wc -l)

            search_occurrences_count=$((search_occurrences_count + local_search_occurrences_count))
            search_occurrences_file_count=$((search_occurrences_file_count + local_search_occurrences_file_count))
        done
        
        summary_data+="<td>$search_occurrences_count</td>"

        total_search_occurrences_count=$((search_occurrences_count + total_search_occurrences_count))
        total_search_occurrences_file_count=$((search_occurrences_file_count + total_search_occurrences_file_count))
    
    done
   
    summary_total_keyword_count=$((summary_total_keyword_count + total_search_occurrences_count))
    summary_total_file_count=$((summary_total_file_count + total_search_occurrences_file_count))
    summary_data+="<td>$total_search_occurrences_count</td><td>$total_search_occurrences_file_count</td></tr>"
}

_generate_summary_report(){
        
    # Generate Summary Report
    total_search_occurrences_count=0
    total_search_occurrences_file_count=0
    summary_data+="<tr><td>Total</td><td>-</td>"
    for keywords in "${ALL_KEYWORDS[@]}"
    do

        GREP_EXTRA_ARG="w"
        for fullsearch_word in "${FULL_SEARCH_KEYWORDS[@]}"
        do
            if [ "$fullsearch_word" == "$keywords" ] ; then
                GREP_EXTRA_ARG=""
            fi
        done

        search_occurrences_count=0
        search_occurrences_file_count=0
        for repo_name in ${all_Repo[@]}
        do
            local_search_occurrences_count=$(grep -rIio$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | wc -l)
            local_search_occurrences_file_count=$(grep -rIil$GREP_EXTRA_ARG "$keywords" "$repo_name" --exclude-dir=".git" | wc -l)

            search_occurrences_count=$((search_occurrences_count + local_search_occurrences_count))
            search_occurrences_file_count=$((search_occurrences_file_count + local_search_occurrences_file_count))

        done

        summary_data+="<td>$search_occurrences_count</td>"
    
    done
    
    summary_data+="<td>$summary_total_keyword_count</td><td>$summary_total_file_count</td></tr>"

    summary_data=${SUMMARY_HTML/SUMMARY_DATA_SECTION/$summary_data}
    echo ${summary_data/TOTAL_KEYWORD_REF/Found $summary_total_keyword_count occurrences in $summary_total_file_count file } > summary.html

}

_prepare_summary_report_header
all_Repo=()
for component_repo_group in ${GITHUB_REPOS[@]}
do
    unset component_repos
    unset component_name
    if [[ $component_repo_group == *":"* ]]
    then
        tmp_component_repo_group=(${component_repo_group//:/ })
        component_name=${tmp_component_repo_group[0]}
        component_repos=${tmp_component_repo_group[1]}
        component_repos=(${component_repos//,/ })

        _clone_repo

        _generate_search_report

        _calculate_summary

        all_Repo=("${all_Repo[@]}" "${component_repos[@]}")

    fi
done

_generate_summary_report

_clean_repo
