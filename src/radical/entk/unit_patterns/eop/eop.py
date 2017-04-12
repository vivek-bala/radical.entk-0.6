__author__    = "Vivek Balasubramanian <vivek.balasubramanian@rutgers.edu>"
__copyright__ = "Copyright 2016, http://radical.rutgers.edu"
__license__   = "MIT"

from radical.entk.exceptions import *
from radical.entk.execution_pattern import ExecutionPattern

import radical.utils as ru

class EoP(ExecutionPattern):

    def __init__(self, ensemble_size, pipeline_size, type='unit', iterations = False, name=None):

        self._ensemble_size = ensemble_size
        self._pipeline_size = pipeline_size
        self._type = 'unit'
        self._iterations = iterations
        self._total_iterations = 1


        self._cancel_all_tasks = False

        if name!=None:
            self._name = name
        else:
            self._name = "None"

        # Internal parameters
        self._next_stage = []
        for i in range(1, ensemble_size+1):
            self._next_stage.append(1)

        self._incremented_tasks = []
        for i in range(1, ensemble_size+1):
            self._incremented_tasks.append(0)

        self._incremented_monitors = []
        for i in range(1, ensemble_size+1):
            self._incremented_monitors.append(0)

        self._cur_iteration = []
        for i in range(1, ensemble_size+1):
            self._cur_iteration.append(1)

        self.kill_instances = None
        self._pattern_status = 'New'

        self._stage_change = False
        self._ensemble_size_change = False

        self._new_stage = None

        # Pattern specific dict
        self._pattern_dict = None

        self._logger = ru.get_logger("radical.entk.pattern.eop")
        self._reporter = self._logger.report

        # Perform sanity check -- perform before proceeding
        self.sanity_check()

        self._session_id = None


    def sanity_check(self):

        # Check type errors
        if type(self._ensemble_size) != int:
            raise TypeError(expected_type=int, actual_type=type(self._ensemble_size))

        if type(self._pipeline_size) != int:
            raise TypeError(expected_type=int, actual_type=type(self._pipeline_size))
        elif ((type(self._pipeline_size) != list) and (type(self._pipeline_size) != int)):
            raise TypeError(expected_type=list, actual_type=type(self._pipeline_size))

        if type(self._type) != str:
            raise TypeError(expected_type=str, actual_type=type(self._type))        

        if type(self._iterations) != bool:
            raise TypeError(expected_type=bool, actual_type=type(self._iterations))


        # Check value errors
        if ((self._type != 'unit') and (self._type != 'complex')):
            raise ValueError(expected_value=['unit','complex'], actual_value=self._type)

        # Check match errors


    @property
    def ensemble_size(self):
        return self._ensemble_size
    
    @property
    def pipeline_size(self):
        return self._pipeline_size

    @property
    def session_id(self):
        return self._session_id
    
    @session_id.setter
    def session_id(self, val):
        self._session_id = val

    @property
    def cur_iteration(self):
        return self._cur_iteration

    @cur_iteration.setter
    def cur_iteration(self, val):
        self._cur_iteration = val


    @property
    def total_iterations(self):
        return self._total_iterations

    @property
    def type(self):
        return self._type
    
    @property
    def name(self):
        return self._name
    

    @property
    def cancel_all_tasks(self):
        return self._cancel_all_tasks
    

    @cancel_all_tasks.setter
    def cancel_all_tasks(self, val):
        self._cancel_all_tasks = val

    @property
    def next_stage(self):
        return self._next_stage
    
    @next_stage.setter
    def next_stage(self, next_stage):
        self._next_stage = next_stage
    
    @property
    def type(self):
        return self._type

    @property
    def pattern_dict(self):
        return self._pattern_dict

    @pattern_dict.setter
    def pattern_dict(self, record):
        self._pattern_dict = record

    @property
    def new_stage(self):
        return self._new_stage

    @new_stage.setter
    def new_stage(self, val):
        self._new_stage = val

    @property
    def stage_change(self):
        return self._stage_change

    @stage_change.setter
    def stage_change(self, value):
        self._stage_change = value
    

    def set_next_stage(self, stage):

        try:
            if stage <= self._pipeline_size:
                self._stage_change = True
                self._new_stage = stage
            else:
                self._logger.error("Assigned next stage greater than total pipeline size")
                raise
        
        except Exception, ex:
            self._logger.error("Could not set next stage, error: %s"%(ex))
            raise


    def set_ensemble_size(self, size):

        try:

            self._ensemble_size_change = True
            self._ensemble_new_size = size

        except Exception, ex:

            self._logger.error("Could not set ensemble size, error: %s"%(ex))
            raise



    def get_stage(self, stage):

        try:
            stage_kernel = getattr(self, "stage_%s"%(stage), None)

            if stage_kernel == None:
                self._logger.error("Pattern does not have stage_%s"%(stage))
                raise

            return stage_kernel

        except Exception, ex:
            self._logger.error("Could not get stage, error: %s"%(ex))
            raise


    def get_branch(self, stage):

        try:
            branch = getattr(self, "branch_%s"%(stage), None)

            if branch == None:
                self._logger.error("Pattern does not have branch_%s"%(stage))
                raise
            
            return branch

        except Exception, ex:

            self._logger.error("Could not get branch, error: %s"%(ex))
            raise


    def get_monitor(self, stage):

        try:
            monitor = getattr(self, "monitor_%s"%(stage), None)

            if monitor == None:
                self._logger.error("Pattern does not have monitor_%s"%(stage))
                raise            
            return monitor

        except Exception, ex:

            self._logger.error("Could not get monitor, error: %s"%(ex))
            raise


    def get_output(self, stage, instance):
        try:
            return self._pattern_dict["iter_%s"%(self._cur_iteration[instance-1])]["stage_%s"%(stage)]["instance_%s"%(instance)]["output"]
        except Exception, ex:
            self._logger.error("Could not get output of stage: %s, instance: %s. Error: %s"%(stage, instance, ex))
            raise


    def get_file(self, stage, instance, filename, new_name=None):
        directory = self._pattern_dict["iter_%s"%(self._cur_iteration[instance-1])]["stage_%s"%(stage)]["instance_%s"%(instance)]["path"]
        file_url = directory + '/' + filename

        import saga,os
        remote_file = saga.filesystem.Directory(directory, session = self._session_id)
        if new_name is None:
            remote_file.copy(filename, os.getcwd())
        else:
            remote_file.copy(filename, os.getcwd() + '/' + new_name)



    def get_status(self, iteration=None, stage=None, instance=None):


        try:
            if stage == None:
                self._logger.error("Need to specify stage number")
                raise

            if instance==None:
                self._logger.error("Need to specify instance number")
                raise

            if iteration == None:
                iteration = self._cur_iteration[instance-1]

            return self._pattern_dict["iter_%s"%(iteration)]["stage_%s"%(stage)]["instance_%s"%(instance)]["status"]

        except Exception,ex:
            self._logger.error("Could not get status of stage: %s, instance: %s, iteration: %s, Error: %s"%(stage, instance, iteration, ex))
            raise


    def get_path(self, iteration, stage, task):

        try:

            if iteration == None:
                iteration = self._cur_iteration[task-1]

            if stage == None:
                self._logger.error('Parameter stage cannot be None')

            if task == None:
                self._logger.error('Parameter task cannot be None')

            return self._pattern_dict['iter_%s'%iteration]['stage_%s'%stage]['instance_%s'%task]['path']

        except Exception,ex:
            self._logger.error("Could not get path of stage: %s, instance: %s, iteration: %s, Error: %s"%(stage, task, iteration, ex))
            raise