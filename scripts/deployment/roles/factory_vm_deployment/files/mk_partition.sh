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
if [ $# -eq 0 ]
then
  echo "No device provided. Please provide a device need to be partitioned."
  echo "Usage :"
  echo "        $0 /dev/sdx"
  exit
fi

NUM_PARTITIONS=4
PARTITION_SIZE="+12G"

SED_STRING="o"
TAIL="p
w
q
"

NEW_LINE="
"
LETTER_n="n"
LETTER_p="p"
EXTENDED_PART_NUM=4
TGTDEV="$1"

SED_STRING="$SED_STRING$NEW_LINE"
for i in $(seq $NUM_PARTITIONS)
do
  if [ "$i" -lt "$EXTENDED_PART_NUM" ]
  then
    SED_STRING="$SED_STRING$LETTER_n$NEW_LINE$NEW_LINE$NEW_LINE$NEW_LINE$PARTITION_SIZE$NEW_LINE"
  fi
  if [ "$i" -eq "$EXTENDED_PART_NUM" ]
  then
    SED_STRING="$SED_STRING$LETTER_n$NEW_LINE$LETTER_p$NEW_LINE$NEW_LINE$PARTITION_SIZE$NEW_LINE"
  fi
  if [ "$i" -gt "$EXTENDED_PART_NUM" ]
  then
    SED_STRING="$SED_STRING$LETTER_n$NEW_LINE$NEW_LINE$PARTITION_SIZE$NEW_LINE"
  fi
done
SED_STRING="$SED_STRING$TAIL"

sed -e 's/\s*\([\+0-9a-zA-Z]*\).*/\1/' << EOF | fdisk "${TGTDEV}"
  $SED_STRING
EOF