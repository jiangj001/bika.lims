"""The request for analysis by a client. It contains analysis instances.
"""
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import delete_objects
from DateTime import DateTime
from Products.ATContentTypes.content import schemata
from Products.ATExtensions.widget.records import RecordsWidget
from Products.Archetypes import atapi
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.public import *
from Products.Archetypes.references import HoldingReference
from Products.Archetypes.utils import shasattr
from Products.CMFCore import permissions
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone import PloneMessageFactory as _p
from Products.CMFPlone.utils import transaction_note
from Products.CMFPlone.utils import safe_unicode
from bika.lims.browser.fields import ARAnalysesField
from bika.lims.browser.widgets import DateTimeWidget
from bika.lims.config import PROJECTNAME, \
    ManageInvoices
from bika.lims.content.bikaschema import BikaSchema
from bika.lims.interfaces import IAnalysisRequest
from bika.lims.utils import sortable_title
from bika.lims.browser.widgets import ReferenceWidget
from decimal import Decimal
from email.Utils import formataddr
from types import ListType, TupleType
from zope.interface import implements
from bika.lims import bikaMessageFactory as _

import pkg_resources
import sys
import time

try:
    from zope.component.hooks import getSite
except:
    # Plone < 4.3
    from zope.app.component.hooks import getSite


schema = BikaSchema.copy() + Schema((
    StringField(
        'RequestID',
        required=1,
        searchable=True,
        widget=StringWidget(
            label=_('Request ID'),
            description=_("The ID assigned to the client's request by the lab"),
            visible={'edit': 'invisible', 'view': 'visible', 'add': 'invisible'},
        ),
    ),
    ReferenceField(
        'Contact',
        required=1,
        vocabulary='getContacts',
        default_method='getContactUIDForUser',
        vocabulary_display_path_bound=sys.maxint,
        allowed_types=('Contact',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestContact',
        widget=ReferenceWidget(
            label=_("Contact"),
            # we let this one alone, template does it separately.
            visible={'edit': 'invisible', 'view': 'invisible', 'add': 'invisible'},
            catalog_name='bika_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    ReferenceField(
        'CCContact',
        multiValued=1,
        vocabulary='getContacts',
        vocabulary_display_path_bound=sys.maxint,
        allowed_types=('Contact',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestCCContact',
    ),
    StringField(
        'CCEmails',
        widget=StringWidget(
            label=_('CC Emails')
        ),
    ),
    ReferenceField(
        'Client',
        required=1,
        allowed_types=('Client',),
        relationship='AnalysisRequestClient',
        widget=ReferenceWidget(
            label=_("Client"),
            description=_("You must assign this request to a client"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    ReferenceField(
        'Batch',
        allowed_types=('Batch',),
        relationship='AnalysisRequestBatch',
        widget=ReferenceWidget(
            label=_("Batch"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
            catalog_name='bika_catalog',
            base_query={'review_state': 'open',
                        'cancelled_state': 'active'},
            showOn=True,
        ),
    ),
    ComputedField(
        'BatchUID',
        expression='context.getBatch() and context.getBatch().UID() or None',
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ReferenceField(
        'Template',
        allowed_types=('ARTemplate',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestARTemplate',
        widget=ReferenceWidget(
            label=_("Template"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    ReferenceField(
        'Profile',
        allowed_types=('AnalysisProfile',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestAnalysisProfile',
        widget=ReferenceWidget(
            label=_("Analysis Profile"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    ReferenceField(
        'Sample',
        vocabulary_display_path_bound=sys.maxint,
        allowed_types=('Sample',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestSample',
        widget=ReferenceWidget(
            label=_("Sample"),
            description=_("Select a sample to create a secondary AR"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
            catalog_name='bika_catalog',
            base_query={'cancelled_state': 'active'},
            showOn=True,
        ),
    ),
    # SamplingDate is set by the sample
    # It's listed here so that it can be accessed from ar add.
    DateTimeField(
        'SamplingDate',
        required=1,
        widget = DateTimeWidget(
            label=_("Sampling Date"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    ReferenceField(
        'SampleType',
        required=1,
        allowed_types='SampleType',
        relationship='AnalysisRequestSampleType',
        widget=ReferenceWidget(
            label=_("Sample Type"),
            description=_("Create a new sample of this type"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    ReferenceField(
        'SamplePoint',
        allowed_types='SamplePoint',
        relationship='AnalysisRequestSamplePoint',
        widget=ReferenceWidget(
            label=_("Sample Point"),
            description=_("Location where sample was taken"),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    StringField(
        'ClientOrderNumber',
        searchable=True,
        widget=StringWidget(
            label=_('Client Order Number'),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    StringField(
        'ClientReference',
        searchable=True,
        widget=StringWidget(
            label=_('Client Reference'),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    StringField(
        'ClientSampleID',
        searchable=True,
        widget=StringWidget(
            label=_('Client Sample ID'),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    ReferenceField('SamplingDeviation',
        allowed_types = ('SamplingDeviation',),
        relationship = 'AnalysisRequestSamplingDeviation',
        referenceClass = HoldingReference,
        widget=ReferenceWidget(
            label=_('Sampling Deviation'),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    ReferenceField('SampleCondition',
        allowed_types = ('SampleCondition',),
        relationship = 'AnalysisRequestSampleCondition',
        referenceClass = HoldingReference,
        widget=ReferenceWidget(
            label=_('Sample condition'),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    ReferenceField('DefaultContainerType',
        allowed_types = ('ContainerType',),
        relationship = 'AnalysisRequestContainerType',
        referenceClass = HoldingReference,
        widget=ReferenceWidget(
            label=_('Default Container'),
            description=_('Default container for new sample partitions'),
            size=12,
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
            catalog_name='bika_setup_catalog',
            base_query={'inactive_state': 'active'},
            showOn=True,
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    BooleanField('AdHoc',
        default=False,
        widget=BooleanWidget(
            label=_("Ad-Hoc"),
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
        ),
    ),
    # A sample field, listed here so that it can be accessed from ar add.
    BooleanField('Composite',
        default=False,
        widget=BooleanWidget(
            label=_("Composite"),
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible',
                     'secondary': 'invisible'},
        ),
    ),
    BooleanField(
        'ReportDryMatter',
        default=False,
        widget=BooleanWidget(
            label=_('Report as Dry Matter'),
            render_own_label=True,
            description=_('These results can be reported as dry matter'),
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
        ),
    ),
    BooleanField(
        'InvoiceExclude',
        default=False,
        widget=BooleanWidget(
            label=_('Invoice Exclude'),
            description=_('Select if analyses to be excluded from invoice'),
            render_own_label=True,
            visible={'edit': 'visible', 'view': 'visible', 'add': 'visible'},
        ),
    ),
    ARAnalysesField(
        'Analyses',
        required=1,
    ),
    ReferenceField(
        'Attachment',
        multiValued=1,
        allowed_types=('Attachment',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestAttachment',
    ),
    ReferenceField(
        'Invoice',
        vocabulary_display_path_bound=sys.maxint,
        allowed_types=('Invoice',),
        referenceClass=HoldingReference,
        relationship='AnalysisRequestInvoice',
    ),
    DateTimeField(
        'DateReceived',
        widget=DateTimeWidget(
            label=_('Date Received'),
            visible={'edit': 'invisible', 'view': 'visible',
                'add': 'invisible'},
        ),
    ),
    DateTimeField(
        'DatePublished',
        widget=DateTimeWidget(
            label=_('Date Published'),
            visible={'edit': 'invisible', 'view': 'visible',
                'add': 'invisible'},
        ),
    ),
    TextField(
        'Remarks',
        searchable=True,
        default_content_type='text/x-web-intelligent',
        allowable_content_types=('text/x-web-intelligent',),
        default_output_type="text/html",
        widget=TextAreaWidget(
            macro="bika_widgets/remarks",
            label=_('Remarks'),
            append_only=True,
        ),
    ),
    FixedPointField(
        'MemberDiscount',
        default_method='getDefaultMemberDiscount',
        widget=DecimalWidget(
            label=_('Member discount %'),
            description=_('Enter percentage value eg. 33.0'),
        ),
    ),
    ComputedField(
        'ClientUID',
        searchable=True,
        expression='here.aq_parent.UID()',
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ComputedField(
        'SampleTypeTitle',
        searchable=True,
        expression="here.getSample() and here.getSample().getSampleType() and here.getSample().getSampleType().Title() or ''",
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ComputedField(
        'SamplePointTitle',
        searchable=True,
        expression="here.getSample() and here.getSample().getSamplePoint() and here.getSample().getSamplePoint().Title() or ''",
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ComputedField(
        'SampleUID',
        expression='here.getSample() and here.getSample().UID()',
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ComputedField(
        'ContactUID',
        expression='here.getContact() and here.getContact().UID()',
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ComputedField(
        'ProfileUID',
        expression='here.getProfile() and here.getProfile().UID()',
        widget=ComputedWidget(
            visible=False,
        ),
    ),
    ComputedField(
        'Invoiced',
        expression='here.getInvoice() and True or False',
        default=False,
        widget=ComputedWidget(
            visible=False,
        ),
    ),
)
)

schema['title'].required = False


class AnalysisRequest(BaseFolder):
    implements(IAnalysisRequest)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True

    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def _getCatalogTool(self):
        from bika.lims.catalog import getCatalog
        return getCatalog(self)

    def Title(self):
        """ Return the Request ID as title """
        return safe_unicode(self.getRequestID()).encode('utf-8')

    def Description(self):
        """ Return searchable data as Description """
        descr = " ".join((self.getRequestID(), self.aq_parent.Title()))
        return safe_unicode(descr).encode('utf-8')

    def getClient(self):
        if self.aq_parent.portal_type == 'Client':
            return self.aq_parent

    def getBatch(self):
        # The parent type may be "Batch" during ar_add.
        # This function fills the hidden field in ar_add.pt
        if self.aq_parent.portal_type == 'Batch':
            return self.aq_parent
        else:
            return self.Schema()['Batch'].get(self)

    def getDefaultMemberDiscount(self):
        """ compute default member discount if it applies """
        if hasattr(self, 'getMemberDiscountApplies'):
            if self.getMemberDiscountApplies():
                plone = getSite()
                settings = plone.bika_setup
                return settings.getMemberDiscount()
            else:
                return "0.00"

    security.declareProtected(View, 'getResponsible')

    def getResponsible(self):
        """ Return all manager info of responsible departments """
        managers = {}
        departments = []
        for analysis in self.objectValues('Analysis'):
            department = analysis.getService().getDepartment()
            if department is None:
                continue
            department_id = department.getId()
            if department_id in departments:
                continue
            departments.append(department_id)
            manager = department.getManager()
            if manager is None:
                continue
            manager_id = manager.getId()
            if manager_id not in managers:
                managers[manager_id] = {}
                managers[manager_id]['name'] = manager.getFullname()
                managers[manager_id]['email'] = manager.getEmailAddress()
                managers[manager_id]['phone'] = manager.getBusinessPhone()
                managers[manager_id][
                    'signature'] = '%s/Signature' % manager.absolute_url()
                managers[manager_id]['dept'] = ''
            mngr_dept = managers[manager_id]['dept']
            if mngr_dept:
                mngr_dept += ', '
            mngr_dept += department.Title()
            managers[manager_id]['dept'] = mngr_dept
        mngr_keys = managers.keys()
        mngr_info = {}
        mngr_info['ids'] = mngr_keys
        mngr_info['dict'] = managers

        return mngr_info

    security.declareProtected(View, 'getResponsible')

    def getManagers(self):
        """ Return all managers of responsible departments """
        manager_ids = []
        manager_list = []
        departments = []
        for analysis in self.objectValues('Analysis'):
            department = analysis.getService().getDepartment()
            if department is None:
                continue
            department_id = department.getId()
            if department_id in departments:
                continue
            departments.append(department_id)
            manager = department.getManager()
            if manager is None:
                continue
            manager_id = manager.getId()
            if not manager_id in manager_ids:
                manager_ids.append(manager_id)
                manager_list.append(manager)

        return manager_list

    security.declareProtected(View, 'getLate')

    def getLate(self):
        """ return True if any analyses are late """
        workflow = getToolByName(self, 'portal_workflow')
        review_state = workflow.getInfoFor(self, 'review_state', '')
        if review_state in ['to_be_sampled', 'to_be_preserved',
                            'sample_due', 'published']:
            return False

        now = DateTime()
        for analysis in self.objectValues('Analysis'):
            review_state = workflow.getInfoFor(analysis, 'review_state', '')
            if review_state == 'published':
                continue
            if analysis.getDueDate() < analysis.getResultCaptureDate():
                return True
        return False

    security.declareProtected(View, 'getBillableItems')

    def getBillableItems(self):
        """ Return all items except those in 'not_requested' state """
        workflow = getToolByName(self, 'portal_workflow')
        items = []
        for analysis in self.objectValues('Analysis'):
            review_state = workflow.getInfoFor(analysis, 'review_state', '')
            if review_state != 'not_requested':
                items.append(analysis)
        return items

    security.declareProtected(View, 'getSubtotal')

    def getSubtotal(self):
        """ Compute Subtotal
        """
        return sum(
            [Decimal(obj.getService() and obj.getService().getPrice() or 0)
            for obj in self.getBillableItems()])

    security.declareProtected(View, 'getVAT')

    def getVAT(self):
        """ Compute VAT """
        return Decimal(self.getTotalPrice()) - Decimal(self.getSubtotal())

    security.declareProtected(View, 'getTotalPrice')

    def getTotalPrice(self):
        """ Compute TotalPrice """
        billable = self.getBillableItems()
        TotalPrice = Decimal(0, 2)
        for item in billable:
            service = item.getService()
            if not service:
                return Decimal(0, 2)
            itemPrice = Decimal(service.getPrice() or 0)
            VAT = Decimal(service.getVAT() or 0)
            TotalPrice += Decimal(itemPrice) * (Decimal(1, 2) + VAT)
        return TotalPrice
    getTotal = getTotalPrice

    security.declareProtected(ManageInvoices, 'issueInvoice')

    def issueInvoice(self, REQUEST=None, RESPONSE=None):
        """ issue invoice
        """
        # check for an adhoc invoice batch for this month
        now = DateTime()
        batch_month = now.strftime('%b %Y')
        batch_title = '%s - %s' % (batch_month, 'ad hoc')
        invoice_batch = None
        for b_proxy in self.portal_catalog(portal_type='InvoiceBatch',
                                           Title=batch_title):
            invoice_batch = b_proxy.getObject()
        if not invoice_batch:
            first_day = DateTime(now.year(), now.month(), 1)
            start_of_month = first_day.earliestTime()
            last_day = first_day + 31
            while last_day.month() != now.month():
                last_day = last_day - 1
            end_of_month = last_day.latestTime()

            invoices = self.invoices
            batch_id = invoices.generateUniqueId('InvoiceBatch')
            invoices.invokeFactory(id=batch_id, type_name='InvoiceBatch')
            invoice_batch = invoices._getOb(batch_id)
            invoice_batch.edit(
                title=batch_title,
                BatchStartDate=start_of_month,
                BatchEndDate=end_of_month,
            )
            invoice_batch.processForm()

        client_uid = self.getClientUID()
        invoice_batch.createInvoice(client_uid, [self, ])

        RESPONSE.redirect(
            '%s/analysisrequest_invoice' % self.absolute_url())

    security.declarePublic('printInvoice')

    def printInvoice(self, REQUEST=None, RESPONSE=None):
        """ print invoice
        """
        invoice = self.getInvoice()
        invoice_url = invoice.absolute_url()
        RESPONSE.redirect('%s/invoice_print' % invoice_url)

    def addARAttachment(self, REQUEST=None, RESPONSE=None):
        """ Add the file as an attachment
        """
        workflow = getToolByName(self, 'portal_workflow')

        this_file = self.REQUEST.form['AttachmentFile_file']
        if 'Analysis' in self.REQUEST.form:
            analysis_uid = self.REQUEST.form['Analysis']
        else:
            analysis_uid = None

        attachmentid = self.generateUniqueId('Attachment')
        self.aq_parent.invokeFactory(id=attachmentid, type_name="Attachment")
        attachment = self.aq_parent._getOb(attachmentid)
        attachment.edit(
            AttachmentFile=this_file,
            AttachmentType=self.REQUEST.form['AttachmentType'],
            AttachmentKeys=self.REQUEST.form['AttachmentKeys'])
        attachment.processForm()
        attachment.reindexObject()

        if analysis_uid:
            tool = getToolByName(self, REFERENCE_CATALOG)
            analysis = tool.lookupObject(analysis_uid)
            others = analysis.getAttachment()
            attachments = []
            for other in others:
                attachments.append(other.UID())
            attachments.append(attachment.UID())
            analysis.setAttachment(attachments)
            if workflow.getInfoFor(analysis, 'review_state') == 'attachment_due':
                workflow.doActionFor(analysis, 'attach')
        else:
            others = self.getAttachment()
            attachments = []
            for other in others:
                attachments.append(other.UID())
            attachments.append(attachment.UID())

            self.setAttachment(attachments)

        RESPONSE.redirect(
            '%s/manage_results' % self.absolute_url())

    def delARAttachment(self, REQUEST=None, RESPONSE=None):
        """ delete the attachment """
        tool = getToolByName(self, REFERENCE_CATALOG)
        if 'ARAttachment' in self.REQUEST.form:
            attachment_uid = self.REQUEST.form['ARAttachment']
            attachment = tool.lookupObject(attachment_uid)
            parent = attachment.getRequest()
        elif 'AnalysisAttachment' in self.REQUEST.form:
            attachment_uid = self.REQUEST.form['AnalysisAttachment']
            attachment = tool.lookupObject(attachment_uid)
            parent = attachment.getAnalysis()

        others = parent.getAttachment()
        attachments = []
        for other in others:
            if not other.UID() == attachment_uid:
                attachments.append(other.UID())
        parent.setAttachment(attachments)
        client = attachment.aq_parent
        ids = [attachment.getId(), ]
        BaseFolder.manage_delObjects(client, ids, REQUEST)

        RESPONSE.redirect(
            '%s/manage_results' % self.absolute_url())

    security.declarePublic('get_verifier')

    def get_verifier(self):
        wtool = getToolByName(self, 'portal_workflow')
        mtool = getToolByName(self, 'portal_membership')

        verifier = None
        try:
            review_history = wtool.getInfoFor(self, 'review_history')
        except:
            return 'access denied'

        if not review_history:
            return 'no history'
        for items in review_history:
            action = items.get('action')
            if action != 'verify':
                continue
            actor = items.get('actor')
            member = mtool.getMemberById(actor)
            verifier = member.getProperty('fullname')
            if verifier is None or verifier == '':
                verifier = actor
        return verifier

    security.declarePublic('getContactUIDForUser')

    def getContactUIDForUser(self):
        """ get the UID of the contact associated with the authenticated
            user
        """
        user = self.REQUEST.AUTHENTICATED_USER
        user_id = user.getUserName()
        pc = getToolByName(self, 'portal_catalog')
        r = pc(portal_type='Contact',
               getUsername=user_id)
        if len(r) == 1:
            return r[0].UID

    security.declarePublic('current_date')

    def current_date(self):
        """ return current date """
        return DateTime()

    def getQCAnalyses(self, qctype=None):
        """ return the QC analyses performed in the worksheet in which, at
            least, one sample of this AR is present.
            Depending on qctype value, returns the analyses of:
            - 'b': all Blank Reference Samples used in related worksheet/s
            - 'c': all Control Reference Samples used in related worksheet/s
            - 'd': duplicates only for samples contained in this AR
            If qctype==None, returns all type of qc analyses mentioned above
        """
        qcanalyses = []
        suids = []
        ans = self.getAnalyses()
        for an in ans:
            an = an.getObject()
            if an.getServiceUID() not in suids:
                suids.append(an.getServiceUID())

        for an in ans:
            an = an.getObject()
            br = an.getBackReferences('WorksheetAnalysis')
            if (len(br) > 0):
                ws = br[0]
                was = ws.getAnalyses()
                for wa in was:
                    if wa.portal_type == 'DuplicateAnalysis' \
                        and wa.getRequestID() == self.id \
                        and wa not in qcanalyses \
                            and (qctype is None or wa.getReferenceType() == qctype):
                        qcanalyses.append(wa)

                    elif wa.portal_type == 'ReferenceAnalysis' \
                        and wa.getServiceUID() in suids \
                        and wa not in qcanalyses \
                            and (qctype is None or wa.getReferenceType() == qctype):
                        qcanalyses.append(wa)

        return qcanalyses

atapi.registerType(AnalysisRequest, PROJECTNAME)
