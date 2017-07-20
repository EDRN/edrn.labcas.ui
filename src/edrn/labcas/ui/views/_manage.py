# encoding: utf-8

from edrn.labcas.ui import PACKAGE_NAME
from edrn.labcas.ui.interfaces import ILabCASSettings
from edrn.labcas.ui.utils import (
    LabCASWorkflow, DEFAULT_SITE_RDF_URL, DEFAULT_PROTOCOL_RDF_URL, DEFAULT_PEOPLE_RDF_URL, DEFAULT_ORGAN_RDF_URL,
    DEFAULT_DISCIPLINE_RDF_URL, DEFAULT_SPECIES_RDF_URL, DEFAULT_SUPER_GROUP
)
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
            default=u'EDRN',
            widget=deform.widget.RadioChoiceWidget(values=((u'EDRN', u'EDRN'), (u'MCL', u'MCL')), inline=True)
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='superGroup',
            title=u'Super Group',
            description=u'What the super group is.',
            default=DEFAULT_SUPER_GROUP,
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='disciplineRDFURL',
            title=u'Discipline RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of disciplines.',
            default=DEFAULT_DISCIPLINE_RDF_URL,
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='organRDFURL',
            title=u'Organ RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of organs (body systems).',
            default=DEFAULT_ORGAN_RDF_URL,
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='peopleRDFURL',
            title=u'People RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of people.',
            default=DEFAULT_PEOPLE_RDF_URL,
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='protocolRDFURL',
            title=u'Protocol RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of protocols.',
            default=DEFAULT_PROTOCOL_RDF_URL,
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='siteRDFURL',
            title=u'Site RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of sites.',
            default=DEFAULT_PROTOCOL_RDF_URL,
        ))
        schema.add(colander.SchemaNode(
            colander.String(),
            name='speciesRDFURL',
            title=u'Species RDF URL',
            description=u'URL to the Resource Description Framework knowledge source of species, like left sharks.',
            default=DEFAULT_SPECIES_RDF_URL,
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
                if program != settings.getProgram() \
                    or peopleRDFURL != settings.getPeopleRDFURL() \
                    or protocolRDFURL != settings.getProtocolRDFURL() \
                    or siteRDFURL != settings.getSiteRDFURL() \
                    or organRDFURL != settings.getOrganRDFURL() \
                    or disciplineRDFURL != settings.getDisciplineRDFURL() \
                    or speciesRDFURL != settings.getSpeciesRDFURL() \
                    or superGroup != settings.getSuperGroup():
                    settings.setProgram(program)
                    settings.setPeopleRDFURL(peopleRDFURL)
                    settings.setProtocolRDFURL(protocolRDFURL)
                    settings.setSiteRDFURL(siteRDFURL)
                    settings.setOrganRDFURL(organRDFURL)
                    settings.setDisciplineRDFURL(disciplineRDFURL)
                    settings.setSpeciesRDFURL(speciesRDFURL)
                    settings.setSuperGroup(superGroup)
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
            'widgetResources': form.get_widget_resources()
        }
