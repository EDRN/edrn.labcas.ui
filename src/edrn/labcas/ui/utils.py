# Copyright 2015 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

import os, os.path


SUPER_GROUP = u'cn=Super User,dc=edrn,dc=jpl,dc=nasa,dc=gov'


class LabCASFile(object):
    u'''A file stored in a LabCASProduct'''
    def __init__(self, name, physicalLocation):
        self.name, self.physicalLocation = name, physicalLocation
        self.size = os.stat(physicalLocation).st_size
    def __cmp__(self, other):
        return cmp(self.name, other.name)


class LabCASProduct(object):
    u'''A product stored within LabCAS.'''
    def __init__(self, identifier, name, files):
        self.identifier, self.name = identifier, name
        self.files = {}
        for i in files:
            self.files[i.name] = i
    def getFiles(self):
        files = self.files.values()
        files.sort()
        return files
    def __cmp__(self, other):
        return cmp(self.name, other.name)
    @staticmethod
    def new(product, principals):
        typeMetadata = product.get('typeMetadata', {})
        owners = frozenset(typeMetadata.get('OwnerGroup', []))
        if SUPER_GROUP in principals or not principals.isdisjoint(owners):
            name, productID = product.get('name'), product.get('id')
            if not name or not productID: return None
            repository = product.get('repositoryPath')
            if not repository: return None
            if not repository.startswith(u'file:///'): return None
            d = os.path.join(repository[7:], name, u'1')
            if not os.path.isdir(d): return None
            files = [LabCASFile(i, os.path.join(d, i)) for i in os.listdir(d)]
            return LabCASProduct(productID, name, files)
        else:
            return None


class LabCASWorkflow(object):
    u'''A workflow we can execute within LabCAS.'''
    def __init__(self, identifier, name, conditions, tasks):
        self.identifier, self.name, self.conditions, self.tasks = identifier, name, conditions, tasks
    def __cmp__(self, other):
        return cmp(self.identifier, other.identifier)
    def __hash__(self):
        return hash(self.identifier)


# Lame
def guessContentType(name):
    if name.endswith('.xml'):
        return 'text/xml'
    elif name.endswith('.txt'):
        return 'text/plain'
    elif name.endswith('.csv'):
        return 'text/csv'
    elif name.endswith('.docx'):
        return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    elif name.endswith('.sas7bdat'):
        return 'application/x-sas-data'
    elif name.endswith('.pdf'):
        return 'application/pdf'
    elif name.endswith('.xls'):
        return 'application/vnd.ms-excel'
    else:
        return 'application/octet-stream'
