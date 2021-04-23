README 
~~~~~~

Task Framework provides an infrastructure for maintaining information about 
various ongoing activities / tasks in the system and view them asynchronously. 

There are two types of clients to the task framework. 
1. Component which perform activities and record progress about activities
2. Component which are responsible to view various ongoing tasks and show 
   them to the user including their status. 

Task Framework Interfaces
~~~~~~~~~~~~~~~~~~~~~~~~~
It has following interfaces

1. Initialize Task with the backend store where it would store task information.
   Task.init(backend_kvstore_url)

2. Create Task for the given resource. Returns handle to task.
   t = Task.create(resource_path, description)

   Task ID can be known with t.id. 

3. Start the activity / task
   Task.start(t)

4. Update progress to a task
   Task.update(t, pct_complete, status)

5. Complete the task
   Task.finish(t)

6. Get the reference to a previously created task
   Task.get(t_id)


Task CLI
~~~~~~~~
Task CLI has the same set of 
   
1. Create task
   $ task url create resource_path task_description

   Example:
   $ task create "dir:///tmp" "123>1>2>sw>motr>pool1" "rebuild"
   123>1>2>sw>motr>pool1>121212.12122
   $

2. Start task
   $ task url start task_id

   Example:
   $ task "dir:///tmp" start "123>1>2>sw>motr>pool1>121212.12122"

3. Finish Task 
   $ task url finish task_id

   Example:
   $ task "dir:///tmp" finish "123>1>2>sw>motr>pool1>121212.12122"

4. Update Progress
   $ task url update task_id pct_complete status

   Example:
   $ task "dir:///tmp" update "123>1>2>sw>motr>pool1>121212.12122" 50 "reading.."

5. Dump Task Information
   $ task url show task_id

   Example:
   $ task "dir:///tmp" show "123>1>2>sw>motr>pool1>121212.12122"
