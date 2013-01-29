from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import bikaMessageFactory as _
from bika.lims.browser import BrowserView
from bika.lims.browser.reports.selection_macros import SelectionMacrosView
from plone.app.layout.globals.interfaces import IViewView
from zope.interface import implements

class Report(BrowserView):
    implements(IViewView)
    default_template = ViewPageTemplateFile("templates/productivity.pt")
    template = ViewPageTemplateFile("templates/productivity_dailysamplesreceived.pt")

    def __init__(self, context, request, report=None):
        super(Report, self).__init__(context, request)
        self.report = report
        self.selection_macros = SelectionMacrosView(self.context, self.request)

    def __call__(self):
        
        parms = []
        titles = []
        
        self.contentFilter = {'portal_type': 'Sample',
                              'review_state': ['sample_received', 'expired', 'disposed'],
                              'sort_on': 'getDateReceived'}
               
        val = self.selection_macros.parse_daterange(self.request,
                                                    'getDateReceived',
                                                    _('Date Received'))        
        if val:
            self.contentFilter[val['contentFilter'][0]] = val['contentFilter'][1]
            parms.append(val['parms'])
            titles.append(val['titles'])
            
        # Query the catalog and store results in a dictionary             
        samples = self.bika_catalog(self.contentFilter)
        if not samples:
            message = _("No samples matched your query")
            self.context.plone_utils.addPortalMessage(message, "error")
            return self.default_template()
              
        datalines = {}
        analyses_count = 0  
        samples_count = 0      
        for sample in samples:
            countrysamples = []
            sample = sample.getObject()
            
            patient = sample.getPatient()
            country = patient.getPhysicalAddress().get('country',_('Unknown'))
            countryline = {'Country':country, 
                           'CountryName':country, 
                           'Samples':[], 
                           'AnalysesCount':0, 
                           'SamplesCount': 0 }
            if country in datalines:
                countryline = datalines[country]
            
            # For each sample, retrieve the analyses and generate
            # a data line for each one
            analyses = sample.getAnalyses({})
            for analysis in analyses:         
                analysis = analysis.getObject()    
                dataline = {'AnalysisKeyword': analysis.getKeyword(),
                             'AnalysisTitle': analysis.getServiceTitle(),
                             'SampleID': sample.getSampleID(),
                             'SampleType': sample.getSampleType().Title(),
                             'SampleDateReceived': self.ulocalized_time(sample.getDateReceived(), long_format=1),
                             'SampleSamplingDate': self.ulocalized_time(sample.getSamplingDate())}
                countryline['Samples'].append(dataline)
                countryline['AnalysesCount'] += 1
                if not (dataline['SampleID'] in countrysamples):
                    countrysamples.append(dataline['SampleID'])
                    countryline['SamplesCount'] += 1     
                    samples_count += 1   
                datalines[country]=countryline   
                analyses_count += 1  
            
        # Footer total data      
        footlines = []  
        footline = {'AnalysesCount': analyses_count, 'SamplesCount':samples_count}
        footlines.append(footline)
        
        self.report_data = {
            'parameters': parms,
            'datalines': datalines,
            'footlines': footlines }
        
        return {'report_title': _('Daily samples received'),
                'report_data': self.template()}
