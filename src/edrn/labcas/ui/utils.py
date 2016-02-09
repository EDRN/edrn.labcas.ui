# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.


class LabCASProduct(object):
    u'''A product stored within LabCAS.'''
    def __init__(self, identifier, name):
        self.identifier, self.name = identifier, name
    def __cmp__(self, other):
        return cmp(self.name, other.name)


class LabCASWorkflow(object):
    u'''A workflow we can execute within LabCAS.'''
    def __init__(self, identifier, name, conditions, tasks):
        self.identifier, self.name, self.conditions, self.tasks = identifier, name, conditions, tasks
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
