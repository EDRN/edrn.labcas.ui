User interface for the Early Detection Research Network (EDRN_) Laboratory
Catalog and Archive System (LabCAS_).  Developed by the EDRN Informatics Center
(IC_), operated by the Jet Propulsion Laboratory (JPL_), which itself is
operated by the California Institute of Technology (CalTech_).


Docker Composition
==================

1. Copy ``env.in`` to ``.env`` and set the values appropriately
2. ``docker-compose build``
3. ``docker-compose up``


What are the Appropriate Values?
--------------------------------

For EDRN:

• LabCAS_LDAP_User_Base: dc=edrn,dc=jpl,dc=nasa,dc=gov
• LabCAS_LDAP_Group_Base: dc=edrn,dc=jpl,dc=nasa,dc=gov
• LabCAS_LDAP_Super_Group: cn=Super User,dc=edrn,dc=jpl,dc=nasa,dc=gov
• LabCAS_LDAP_Manager_DN: uid=admin,ou=system
• LabCAS_LDAP_Manager_Auth: REDACTED
• LabCAS_ZIP_File_Limit: Say 200–500 MiB or so
• LabCAS_TMP_Dir: /data/tmp
• LabCAS_Program: EDRN

For MCL:

• LabCAS_LDAP_User_Base: ou=users,o=MCL
• LabCAS_LDAP_Group_Base: ou=groups,o=MCL
• LabCAS_LDAP_Super_Group: cn=Super User,ou=groups,o=MCL
• LabCAS_LDAP_Manager_DN: uid=admin,ou=system
• LabCAS_LDAP_Manager_Auth: REDACTED
• LabCAS_ZIP_File_Limit: Say 200–500 MiB or so
• LabCAS_TMP_Dir: /data/tmp
• LabCAS_Program: MCL


Running a Development Instance
==============================

This doesn't work anymore since we've Dockerized. Leaving it for posterity.
.. 
.. Easy.  First copy ``dev.cfg.in`` to ``dev.cfg`` and set the
.. ``ldap-manager-password`` in the ``[secrets]`` section.  Then::
.. 
..     ssh -L 9000:localhost:9000 -L 9001:localhost:9001 -L 9002:localhost:9002 -L 8080:localhost:8080 -L 8983:localhost:8983 labcas-dev.jpl.nasa.gov
..     python2.7 bootstrap.py -c dev.cfg
..     bin/buildout -c dev.cfg
..     bin/pserve --reload parts/templates/paste-dev.cfg 
.. 
.. Then visit http://localhost:6543/ with a browser.


.. _EDRN: http://edrn.nci.nih.gov/
.. _LabCAS: http://cancer.jpl.nasa.gov/documents/applications/laboratory-catalog-and-archive-service-labcas
.. _IC: http://cancer.jpl.nasa.gov/
.. _JPL: http://www.jpl.nasa.gov/
.. _CalTech: http://www.caltech.edu/

