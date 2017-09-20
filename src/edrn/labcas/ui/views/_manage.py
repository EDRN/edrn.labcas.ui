# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import ILabCASSettings
from pyramid.view import view_config, view_defaults
from zope.component import getUtility
import colander, deform


@view_defaults(renderer=PACKAGE_NAME + ':templates/manage.pt')
class ManageView(object):
    def __init__(self, request):
        self.request = request
    @view_config(route_name='manage', permission='manage')
    def __call__(self):
        settings = getUtility(ILabCASSettings)
        schema = colander.SchemaNode(colander.Mapping())
        schema.add(colander.SchemaNode(
            colander.String(),
            name='program',
            title=u'Program',
            description=u'Which program this LabCAS installation is for.',
            default=getUtility(ILabCASSettings).getProgram(),
            widget=deform.widget.RadioChoiceWidget(values=((u'EDRN', u'EDRN'), (u'MCL', u'MCL')), inline=True)
        ))
        schema.add(colander.SchemaNode(
            colander.Integer(),
            name='zipFileLimit',
            title=u'Zip File Limit',
            description=u'Megabyte limit before we disable download of multiple files in a Zip archive.',
            default=getUtility(ILabCASSettings).getZipFileLimit()
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='tmpDir',
            title=u'Temporary Directory',
            description=u'Where on the server we can create temporary files.',
            default=getUtility(ILabCASSettings).getTmpDir(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='superGroup',
            title=u'Super Group',
            description=u'What the super group is.',
            default=getUtility(ILabCASSettings).getSuperGroup(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='disciplineRDFURL',
            title=u'Discipline RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of disciplines.',
            default=getUtility(ILabCASSettings).getDisciplineRDFURL(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='organRDFURL',
            title=u'Organ RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of organs (body systems).',
            default=getUtility(ILabCASSettings).getOrganRDFURL(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='peopleRDFURL',
            title=u'People RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of people.',
            default=getUtility(ILabCASSettings).getPeopleRDFURL(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='protocolRDFURL',
            title=u'Protocol RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of protocols.',
            default=getUtility(ILabCASSettings).getProtocolRDFURL(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='siteRDFURL',
            title=u'Site RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of sites.',
            default=getUtility(ILabCASSettings).getSiteRDFURL(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='speciesRDFURL',
            title=u'Species RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of species, like left sharks.',
            default=getUtility(ILabCASSettings).getSpeciesRDFURL(),
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='analytics',
            title=u'Analytics',
            description=u'JavaScript to append to the bottom of each page for analytics purposes.',
            default=getUtility(ILabCASSettings).getAnalytics(),
            missing=u'',
            widget=deform.widget.TextAreaWidget(rows=6)
        ))
        form = deform.Form(schema, buttons=('submit',))
        if 'submit' in self.request.params:
            try:
                metadataAppstruct = form.validate(self.request.POST.items())
                program           = metadataAppstruct['program']
                superGroup        = metadataAppstruct['superGroup']
                disciplineRDFURL  = metadataAppstruct['disciplineRDFURL']
                organRDFURL       = metadataAppstruct['organRDFURL']
                peopleRDFURL      = metadataAppstruct['peopleRDFURL']
                protocolRDFURL    = metadataAppstruct['protocolRDFURL']
                siteRDFURL        = metadataAppstruct['siteRDFURL']
                speciesRDFURL     = metadataAppstruct['speciesRDFURL']
                zipFileLimit      = metadataAppstruct['zipFileLimit']
                tmpDir            = metadataAppstruct['tmpDir']
                analytics         = metadataAppstruct['analytics']
                if program != settings.getProgram() \
                    or peopleRDFURL != settings.getPeopleRDFURL() \
                    or protocolRDFURL != settings.getProtocolRDFURL() \
                    or siteRDFURL != settings.getSiteRDFURL() \
                    or organRDFURL != settings.getOrganRDFURL() \
                    or disciplineRDFURL != settings.getDisciplineRDFURL() \
                    or speciesRDFURL != settings.getSpeciesRDFURL() \
                    or superGroup != settings.getSuperGroup() \
                    or zipFileLimit != settings.getZipFileLimit() \
                    or tmpDir != settings.getTmpDir() \
                    or analytics != settings.getAnalytics():
                    settings.setProgram(program)
                    settings.setPeopleRDFURL(peopleRDFURL)
                    settings.setProtocolRDFURL(protocolRDFURL)
                    settings.setSiteRDFURL(siteRDFURL)
                    settings.setOrganRDFURL(organRDFURL)
                    settings.setDisciplineRDFURL(disciplineRDFURL)
                    settings.setSpeciesRDFURL(speciesRDFURL)
                    settings.setSuperGroup(superGroup)
                    settings.setZipFileLimit(zipFileLimit)
                    settings.setTmpDir(tmpDir)
                    settings.setAnalytics(analytics)
                    self.request.session.flash(u'Changes saved.', 'info')
                else:
                    self.request.session.flash(u'No changes made.', 'info')
            except deform.ValidationFailure as ex:
                self.request.session.flash(u"Some required fields are missing or don't make sense.", 'info')
                return {
                    'form': ex.render(),
                    'widgetResources': form.get_widget_resources()
                }
        return {
            'form': form.render(),
            'widgetResources': form.get_widget_resources(),
            'pageTitle': u'Manage LabCAS'
        }
