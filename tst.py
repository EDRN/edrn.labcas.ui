# encoding: utf-8

import xmlrpclib, time, solr


def waitForComp(server, workflowID):
    runningStatus = ('CREATED', 'QUEUED', 'STARTED', 'PAUSED')
    pgeTaskStatus = ('STAGING INPUT', 'BUILDING CONFIG FILE', 'PGE EXEC', 'CRAWLING')
    doneStatus = ('FINISHED', 'ERROR')
    while True:
        time.sleep(1)
        print 'getting workflow instance'
        response = server.workflowmgr.getWorkflowInstanceById(workflowID)
        print response
        status = response['status']
        if status in runningStatus or status in pgeTaskStatus:
            print 'Workflow {} running (status {})'.format(workflowID, status)
        elif status in doneStatus:
            print 'Workflow {} ended with status {}'.format(workflowID, status)
            return response
        else:
            print 'Unknown workflow status: {}'.format(status)


def printResult(result):
    '''Utility function to print out a few fields of a result.'''
    print "\nFile id=%s" % result['id']             # single-valued field
    print "File name=%s" % result['Filename'][0]    # multi-valued field
    print "File size=%s" % result['FileSize'][0]    # multi-valued field
    print "File location=%s" % result['CAS.ReferenceDatastore'][0]  # multi-valued field
    print "File version=%s" % result['Version'][0]  # multi-valued field


def printProductType(ptd):
    print 'PRODUCT TYPE: {}'.format(ptd['name'])
    for key, value in ptd.iteritems():
        print '\t{} = {}'.format(key, value)


def main():
    # server = xmlrpclib.ServerProxy('http://localhost:9001/')
    # response = server.workflowmgr.getRegisteredEvents()
    # response = server.workflowmgr.getWorkflows()
    # print '\n'.join([repr(i['tasks']) for i in response])

    # response = server.workflowmgr.executeDynamicWorkflow(
    #     ['urn:edrn:LabcasUploadInitTask', 'urn:edrn:LabcasUploadExecuteTask'],
    #     {'Dataset': 't3'}
    # )
    # print response
    # waitForComp(server, response)

    # response = server.workflowmgr.executeDynamicWorkflow(
    #     ['urn:edrn:LabcasUpdateTask'],
    #     {'Dataset': 't1'}
    # )
    # print response
    # waitForComp(server, response)

    server = solr.SolrConnection('http://localhost:8983/solr/oodt-fm')
    # response = server.query('*:*', fq=['OwnerGroup:cn=Crichton*'], start=0)
    # for result in response.results:
    #     printResult(result)

    # response = server.query('*:*', fq=['Dataset:FHCRCHanashAnnexinLamr'], start=0, rows=0, facet='true', facet_field='Version')
    response = server.query('*:*', fq=['DatasetId:FHCRCHanashAnnexinLamr'], start=0)
    import pdb;pdb.set_trace()
    versions = response.facet_counts['facet_fields']['Version']
    lastVersion = 0
    for key, value in versions.items():
        print 'Version {} has {} files'.format(key, value)
        if int(key) > lastVersion:
            lastVersion = int(key)

    # response = server.query('*:*', fq=['Dataset:t1', 'Version:%s'.format(lastVersion)], start=0)
    # print 'Latest version {} # of files {}'.format(lastVersion, response.numFound)
    # for result in response.results:
    #     printResult(result)

    # server = xmlrpclib.ServerProxy('http://localhost:9000/')
    # productTypes = server.filemgr.getProductTypes()
    # import pdb;pdb.set_trace()
    # for ptd in productTypes:
    #     printProductType(ptd)

    # server = xmlrpclib.ServerProxy('http://localhost:9000/')
    # product = server.filemgr.getProductTypeById('urn:edrn:t3')
    # import pdb;pdb.set_trace()
    # printProductType(product)


if __name__ == '__main__':
    main()
