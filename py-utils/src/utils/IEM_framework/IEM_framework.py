class IEM:
    severity=" "
    source_id=" "
    component_id=None
    module_id=None
    event_id=None
    message=" "
    params={ }

    def __init__(self):
    
    def populate(self,severity:str, source_id:str, component_id, module_id, event_id, message:str,**params):
        self.severity=severity
        self.source_id=source_id
        self.component_id=component_id
        self.module_id=module_id
        self.event_id=event_id
    

