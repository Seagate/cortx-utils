#!/bin/env python3

from cortx.utils.task_store import Task

Task.init("dir:///tmp")
t = Task.create("cluster>site>rack>node>sw>motr>rebuild", "Rebuild")
Task.start(t)
Task.set_status(t, 50, "reading...")
Task.finish(t)
t_name = Task.search("cluster>site>rack>node>sw>motr>rebuild")
print(t_name)
