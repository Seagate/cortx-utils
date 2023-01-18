#!/bin/bash

#cd $CEPH_PATH/build

# INCASE USING CORTX , PASTE cortx-rgw PATH IN BASHRC AS CORTX_RGW
#cd $CORTX_RGW/build

# ======================================================================================================

# CREATE S3 USER AND EXTRACT ACCESS_KEY AND SECRET KEY

# IF RUNNING THE SCRIPT ON THE SAME MACHINE AGAIN , EITHER CHANGE -uid and --display-name OR COMMENT NEXT LINE
# WHILE CREATING A SECOND USER CHANGE BUCKET_NAME TO A NEW BUCKET (WILL RETURN ERROR IF AN EXISTING BUCKET NAME IS USED)
#bin/radosgw-admin user create --uid dragonuser --display-name dragonuser --no-mon-config > s3user.txt

#ACCESS_KEY="$(grep 'access_key' s3user.txt | cut -d '"' -f 4)"
#SECRET_KEY="$(grep 'secret_key' s3user.txt | cut -d '"' -f 4)"
ACCESS_KEY="MR3D8J7AMJJKW7GSN1AW"
SECRET_KEY="5LjN6dYMjrkbFR295QSkAVGvgvaOCg6sJK0s6pKc"
#echo $ACCESS_KEY
#echo $SECRET_KEY
BUCKET="dragonbucket5"
#echo $BUCKET
# ======================================================================================================

# EXTRACT ENDPOINT USING IFCONFIG (ETH0)
#IP="$(ifconfig | grep 'inet' | head -n 1 | cut -c9- | cut -d ' ' -f 2)"
#ENDPOINT="http://192.168.49.6:8000,http://192.168.48.74:8000,http://192.168.49.7:8000"
ENDPOINT="http://192.168.49.6:8000"
#echo $ENDPOINT

# ======================================================================================================
# DEFINE WORKLOAD SIZE AND LOOP COUNT (ITERATIONS FOR EACH WORKLOAD SIZE)
#OBJ_SIZE=("1Mb" "1Mb" "1Mb" "1Mb" "1Mb" "1Mb" "4Mb" "4Mb" "4Mb" "4Mb" "4Mb" "4Mb" "128Mb" "128Mb" "128Mb" "128Mb" "128Mb" "128Mb" "256Mb" "256Mb" "256Mb" "256Mb")
#SAMPLES=(1000 2000 3000 5000 7000 9999 1000 2000 3000 5000 7000 9999 100 200 300 500 700 999 100 200 300 500)
#CLIENTS=(30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30 30)


OBJ_SIZE=("4Kb" "4Kb" "1Mb" "1Mb" "4Mb" "4Mb" "64Mb" "64Mb" "128Mb" "128Mb")
SAMPLES=(2000 2000 2000 2000 2000 2000 2000 2000 2000 2000)
CLIENTS=(1 30 1 30 1 30 1 30 1 30)
LOOP_COUNT=3
ARR_SIZE=${#OBJ_SIZE[*]}

# ======================================================================================================
# RUN S3BENCH WITH -skipCleanup INITIALLY FOR REUSING THE SAME BUCKET
# THIS RUN ISNT COUNTED IN PERFORMANCE STATS

mkdir s3tests
cd s3tests
mkdir perf-reports

echo "Starting Initial Run"

s3bench -accessKey $ACCESS_KEY -accessSecret $SECRET_KEY -bucket $BUCKET -endpoint $ENDPOINT -numClients 1 -numSamples 1 -objectNamePrefix=initworkload -objectSize 1Kb -region us-east-1 -skipCleanup > init_run.log

echo "Initial Run Completed!!!"

# ======================================================================================================
# CREATING LOG FILES WITH ORDER TO READ METRICS


FILE_NAME="$(date +"perf-%Y-%m-%d-%T")"
echo "  Operation       Throughput      RPS     TTFB    " > perf-reports/$FILE_NAME.log
# init write/read files for updated output
echo "" > write_thr.log
echo "" > read_thr.log
echo "" > write_error.log
echo "" > read_error.log
echo "Object,Clients,Samples,Write(MB/s),Read(MB/s),WriteErr,ReadErr" > perf-reports/new-perf.csv

#echo "Object,Clients,Write(MB/s),Read(MB/s)" > perf-reports/new-perf.csv

# ======================================================================================================


for ((i=0;i<$ARR_SIZE;i++));
do
        echo -e  "\n\nIO Tests for Object Size:" ${OBJ_SIZE[i]} " Samples:" ${SAMPLES[i]} " Clients:" ${CLIENTS[i]}  >>  perf-reports/$FILE_NAME.log
        echo "IO Tests for Object Size :" ${OBJ_SIZE[i]} " Samples:" ${SAMPLES[i]} " Clients:" ${CLIENTS[i]} #display in terminal
        for ((j=1;j<=$LOOP_COUNT;j++));
        do
                echo "Iteration : " $j >>  perf-reports/$FILE_NAME.log
                echo "Iteration : " $j #display in terminal

                s3bench -accessKey $ACCESS_KEY -accessSecret $SECRET_KEY -bucket $BUCKET -endpoint $ENDPOINT -numClients ${CLIENTS[i]} -numSamples ${SAMPLES[i]} -objectNamePrefix=s3workload -objectSize ${OBJ_SIZE[i]}  -region us-east-1 > tmp.log
                grep 'Total Throughput' tmp.log > throughput.log
                grep 'RPS' tmp.log > RPS.log
                grep 'Ttfb Avg' tmp.log > ttfb.log
                grep 'Errors Count' tmp.log > error.log

		#this version of s3bench gives report format in log too so write throughput is on line 2 instead of 1
                WRITE_THROUGHPUT="$(sed -n '2p' throughput.log | grep -Eo "[0-9]+\.[0-9]+")"
                WRITE_RPS="$(sed -n '2p' RPS.log | grep -Eo "[0-9]+\.[0-9]+")"
                WRITE_TTFB="$(sed -n '2p' ttfb.log | grep -Eo "[0-9]+\.[0-9]+")"
                WRITE_ERROR="$(sed -n '2p' error.log | cut -d ':' -f 2)"

		#read thr on line 3 instead of 2
                READ_THROUGHPUT="$(sed -n '3p' throughput.log | grep -Eo "[0-9]+\.[0-9]+")"
                READ_RPS="$(sed -n '3p' RPS.log | grep -Eo "[0-9]+\.[0-9]+")"
                READ_TTFB="$(sed -n '3p' ttfb.log | grep -Eo "[0-9]+\.[0-9]+")"
                READ_ERROR="$(sed -n '3p' error.log | cut -d ':' -f 2)"

                #VALIDATE_THROUGHPUT="$(sed -n '3p' throughput.log | grep -Eo "[0-9]+\.[0-9]+")"
                #VALIDATE_RPS="$(sed -n '3p' RPS.log | grep -Eo "[0-9]+\.[0-9]+")"
                #VALIDATE_TTFB="$(sed -n '3p' ttfb.log | grep -Eo "[0-9]+\.[0-9]+")"

                echo "  Write            $WRITE_THROUGHPUT        $WRITE_RPS    $WRITE_TTFB       " >>  perf-reports/$FILE_NAME.log
                echo "  Read             $READ_THROUGHPUT        $READ_RPS    $READ_TTFB       " >>  perf-reports/$FILE_NAME.log
                #echo "  VALIDATE         $VALIDATE_THROUGHPUT        $VALIDATE_RPS    $VALIDATE_TTFB       " >>  perf-reports/$FILE_NAME.log


                echo $WRITE_THROUGHPUT >> write_thr.log
                echo $READ_THROUGHPUT >> read_thr.log
                echo $WRITE_ERROR >> write_error.log
                echo $READ_ERROR >> read_error.log






                #grep 'Delete Objs' tmp.log > del.log
                #grep -o -E '[0-9]+' del.log > del1.log
                echo "Completed!!" #display in terminal
        done
done




# ========================================================================================================
# ========================================================================================================

# experimental block for csv

COUNTER=2
#LINE_NUMBER="${COUNTER}p"

                for ((k=0;k<$ARR_SIZE;k++));
                do

                        for ((l=0;l<$LOOP_COUNT;l++));
                        do
                                LINE_NUMBER="${COUNTER}p"
                                #echo $LINE_NUMBER
                                WRITE_THR="$(sed -n $LINE_NUMBER write_thr.log | grep -Eo "[0-9]+\.[0-9]+")"
                                READ_THR="$(sed -n $LINE_NUMBER read_thr.log | grep -Eo "[0-9]+\.[0-9]+")"
                                WRITE_ERR="$(sed -n $LINE_NUMBER write_error.log)"
                                READ_ERR="$(sed -n $LINE_NUMBER read_error.log)"




                                #echo $WRITE_THR
                                #echo $READ_THR
                                #echo  ${OBJ_SIZE[k]} "," ${CLIENTS[k]} "," $WRITE_THR "," $READ_THR >> perf-reports/new-perf.csv

                                echo  ${OBJ_SIZE[k]} "," ${CLIENTS[k]} "," ${SAMPLES[k]}  "," $WRITE_THR "," $READ_THR "," $WRITE_ERR "," $READ_ERR >> perf-reports/new-perf.csv


                                #echo $l

                                let COUNTER+=1
                                #let COUNTER=$COUNTER+1
                                #echo $COUNTER
                        done


                done






# ==========================================================================================================
# CLEANING TEMMP FILES
rm -f init_run.log
#rm -f throughput.log
rm -f RPS.log
rm -f ttfb.log
#rm -f tmp.log


