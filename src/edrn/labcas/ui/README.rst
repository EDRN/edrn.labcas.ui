LabCAS User Interface
=====================

The EDRN_ Laboratory Catalog and Archive Service (LabCAS) user interface
is a web-based application implemented in the Plone_ content management
system atop the Zope_ application server, written in Python_.

To demonstrate it, we'll need a test browser::

    >>> app = layer['app']
    >>> from plone.testing.z2 import Browser
    >>> from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
    >>> browser = Browser(app)
    >>> browser.handleErrors = False
    >>> browser.addHeader('Authorization', 'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD))
    >>> portal = layer['portal']    
    >>> portalURL = portal.absolute_url()

This browser has full manager permissions, but we'll need a plain browser to
test some of the more user-level functions::

    >>> userBrowser = Browser(app)

Let's go.


LabCAS Instances
----------------

A user interface for LabCAS starts with an instance of a LabCAS object.  These
may be created anywhere in a Plone portal::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-labcas-ui-labcas')
    >>> l.url.endswith('++add++edrn.labcas.ui.labcas')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'My Mad Science'
    >>> browser.getControl(name='form.widgets.description').value = u'To keep my mad discoveries safe.'
    >>> browser.getControl(name='form.widgets.dataDeliveryURL').value = u'testscheme://localhost/fmprod/data'
    >>> browser.getControl(name='form.widgets.solrURL').value = u'testscheme://localhost/solr'
    >>> browser.getControl(name='form.widgets.curatorServiceURL').value = u'testscheme://localhost/curator/services'
    >>> browser.getControl(name='form.widgets.curatorServiceUsername').value = u'curator'
    >>> browser.getControl(name='form.widgets.curatorServicePassword').value = u's3cr3t'
    >>> import tempfile
    >>> path = tempfile.mkdtemp('.d')
    >>> path += 'foo'
    >>> import os.path
    >>> os.path.isdir(path)
    False
    >>> browser.getControl(name='form.widgets.stagingDir').value = unicode(path)
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'my-mad-science' in portal.keys()
    True
    >>> labcas = portal['my-mad-science']
    >>> labcas.title
    u'My Mad Science'
    >>> labcas.description
    u'To keep my mad discoveries safe.'
    >>> labcas.dataDeliveryURL
    u'testscheme://localhost/fmprod/data'
    >>> labcas.solrURL
    u'testscheme://localhost/solr'
    >>> labcas.curatorServiceURL
    u'testscheme://localhost/curator/services'
    >>> labcas.curatorServiceUsername
    u'curator'
    >>> labcas.curatorServicePassword
    u's3cr3t'

Notice also that we got a free staging directory out of it::

    >>> os.path.isdir(path)
    True


Datasets
--------

Datasets go into LabCAS instances and ONLY into LabCAS instances::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-labcas-ui-dataset')
    Traceback (most recent call last):
    ...
    LinkNotFoundError
    >>> browser.open(portalURL + '/my-mad-science')
    >>> l = browser.getLink(id='edrn-labcas-ui-dataset')
    >>> l.url.endswith('++add++edrn.labcas.ui.dataset')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = u'Toxic Plasma'
    >>> browser.getControl(name='form.widgets.description').value = u'This stuff really works.'
    >>> browser.getControl(name='form.widgets.datasetDate-day').value = u'9'
    >>> browser.getControl(name='form.widgets.datasetDate-month').displayValue = [u'May']
    >>> browser.getControl(name='form.widgets.datasetDate-year').value = u'2015'
    >>> browser.getControl(name='form.widgets.leadPI').value = u'Doctor Evil'
    >>> browser.getControl(name='form.widgets.specimenType').value = u'Sticky'
    >>> browser.getControl(name='form.widgets.accessControl').value = u'Me.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'toxic-plasma' in labcas.keys()
    True
    >>> dataset = labcas['toxic-plasma']
    >>> dataset.title
    u'Toxic Plasma'
    >>> dataset.description
    u'This stuff really works.'
    >>> dataset.datasetDate
    datetime.date(2015, 5, 9)
    >>> dataset.leadPI
    u'Doctor Evil'
    >>> dataset.specimenType
    u'Sticky'
    >>> dataset.accessControl
    u'Me.'

This also created a staging directory for uploaded datasets and an OODT CAS
metadata file::

    >>> stagingDir = os.path.join(dataset.stagingDir, dataset.id)
    >>> os.path.isdir(stagingDir)
    True
    >>> metadataFile = os.path.join(stagingDir, dataset.id + u'.xml')
    >>> os.path.isfile(metadataFile)
    True
    >>> with open(metadataFile, 'r') as infile: print infile.read()
    <?xml version='1.0' encoding='UTF-8'?>
    <metadata xmlns="http://oodt.jpl.nasa.gov/1.0/cas">
      <keyval>
        <key>DatasetId</key>
        <val>doctor_evil|toxic_plasma</val>
      </keyval>
      <keyval>
        <key>DatasetName</key>
        <val>Toxic Plasma</val>
      </keyval>
      <keyval>
        <key>DatasetDate</key>
        <val>2015-05-09</val>
      </keyval>
      <keyval>
        <key>LeadPI</key>
        <val>Doctor Evil</val>
      </keyval>
      <keyval>
        <key>SpecimenType</key>
        <val>Sticky</val>
      </keyval>
      <keyval>
        <key>UploadedBy</key>
        <val>admin</val>
      </keyval>
    </metadata>
    <BLANKLINE>

Whew!  

.. References:
.. _EDRN: http://edrn.nci.nih.gov/
