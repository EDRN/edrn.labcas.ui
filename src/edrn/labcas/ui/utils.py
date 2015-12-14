# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.


class LabCASProduct(object):
    def __init__(self, identifier, name):
        self.identifier, self.name = identifier, name
    def __cmp__(self, other):
        return cmp(self.name, other.name)
