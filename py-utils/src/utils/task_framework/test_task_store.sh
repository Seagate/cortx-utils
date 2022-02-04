#!/bin/env bash

SCRIPT_DIR=$(dirname $0)
cd $SCRIPT_DIR
PY_UTILS_ROOT="../../.."
export PYTHONPATH=$PY_UTILS_ROOT

[ -L $PY_UTILS_ROOT/cortx ] || ln -s $PY_UTILS_ROOT/src $PY_UTILS_ROOT/cortx

# Create Task
echo "Creating task ..."
task_id=$(./task_cli.py "dir:///tmp" create "123>1>3" "desc")
echo "Task $task_id created !!"

# Show Task 
echo "Task Information"
./task_cli.py "dir:///tmp" show "$task_id"

# Start Task
echo "Staring Task"
./task_cli.py "dir:///tmp" start "$task_id"

# Update Progress
echo "Updating progress of the Task"
./task_cli.py "dir:///tmp" update "$task_id" 50 "creating backup..."

# Update Progress
echo "Updating progress of the Task, again"
./task_cli.py "dir:///tmp" update "$task_id" 80 "winding up..."

# Finish Task
echo "Finishing Task"
./task_cli.py "dir:///tmp" finish "$task_id"

# Show Task
echo "Task Information"
./task_cli.py "dir:///tmp" show "$task_id"

# Search Task
echo "Searching for completed task"
./task_cli.py "dir:///tmp" search "123>1>3" "pct_complete==100"
