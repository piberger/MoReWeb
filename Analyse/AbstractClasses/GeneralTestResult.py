'''
Program : MORE-Web 
 Author : Esteban Marin - estebanmarin@gmx.ch
 Version    : 2.1
 Release Date   : 2013-05-30
'''

import os
import ROOT
import gzip
import sys
import datetime
import json
import traceback
import warnings
from sets import Set

class GeneralTestResult:
       
    nRows = 80
    nCols = 52
    nTotalChips = 16
    '''
        Initialization function
        @param ParentObject Reference to the Parent Object
        @param InitialModulePath Starting point of modules
    '''
    def __init__(self, TestResultEnvironmentObject, ParentObject = None, InitialModulePath = None, InitialFinalResultsStoragePath = None, InitialAttributes = None, Key = None, DisplayOptions = None):
        
        # Name of the Test Result, only a-zA-Z0-9_
        self.Name = ''
        
        # Name of the test result without prefixes
        self.NameSingle = ''
        self.Key = ''
        
        # Title displayed in HTML, etc
        self.Title = ''
        
        if Key:
            self.Key = Key
        
        # Attributes like Date, etc.
        self.Attributes = {
            # Date as UNIX timestamp, if 0, the date of the parent object is taken
            'TestDate':0,
            # Type of the tested object
            'TestedObjectType':'',
            # ID of the tested object
            'TestedObjectID':'',
            # Key for custom storage path
            'StorageKey':'',
            # subDirectory of the test result root-files
            'TestResultSubDirectory':'',
        }
        
        
        self.Show = True
        self.Enabled = True
        self.SavePlotFile = True
        self.GzipSVG = TestResultEnvironmentObject.Configuration['GzipSVG']
        self.DefaultImageFormat = TestResultEnvironmentObject.Configuration['DefaultImageFormat'].strip().lower()
        if  TestResultEnvironmentObject.Configuration.has_key('OverviewHTMLLink'):
            self.OverviewHTMLLink = TestResultEnvironmentObject.Configuration['OverviewHTMLLink']
        else:
            self.OverviewHTMLLink = None
        # Path for current test to folder with root-files
        self.RawTestSessionDataPath = ''
        
        # Path for current test result files (html, svg, etc)
        self.FinalResultsStoragePath = ''
        
        
        # File handle (might be used by sub results)
        self.FileHandle = 0
        
        # Reference to ROOT canvas
        self.Canvas = None
        
        # Display Properties as in the ResultData.SubTestResultDictList
        self.DisplayOptions = {
            'Order':0,
            'Width':1,
            'GroupWithNext':False,
        }
        
        
        # Result array
        self.ResultData = {
            # Key / ValueDict (dict with {Value, Unit, Label}, if Label not specified, the key is used as label) Pairs
            # 'KeyValueDictPairs':{
            #       'MyKey':{
            #           'Value':25,
            #           'Unit': 'kg',
            #           'Label': 'My Key'
            #       }
            #   }
            'KeyValueDictPairs':{},
            
            # List of keys for sorting
            'KeyList':[],
            # Plot data
            'Plot':{
                'Enabled':0,
                'ROOTObject':None,
                'Caption':'',
                'ImageFile':'',
                'Format':self.DefaultImageFormat #svg
            },
            # SubTest Results
            'SubTestResults':{},
            # List of {Key, Module} dict for sorting and special attributes
            'SubTestResultDictList':[],
            # 'SubTestResultDictList':{
            #   {
            #       'Key':'Noise'
            #       'Module':'Noise',
            #       'TestResultObject':object,
            #       'InitialAttributes':{'StorageKey':'Blub'},
            #       'DisplayOptions':{'Order':1, 'Width':1,'GroupWithNext':False},
            #   }
            # }
            
            # hidden data, might be needed by other test results but is not displayed
            'HiddenData':{},
            
            # a data table if needed
            'Table':{
                'HEADER':[],
                'BODY':[],
                'FOOTER':[],
            }
            
        }
    
        # Reference to parent object
        self.ParentObject = None
    
        
        
        # Reference to the Test Result Environment
        self.TestResultEnvironmentObject = None
        
        
        
        self.TestResultEnvironmentObject = TestResultEnvironmentObject
        self.Canvas = self.TestResultEnvironmentObject.Canvas
        self.RawTestSessionDataPath = self.TestResultEnvironmentObject.ModuleDataDirectory
        
        if ParentObject:
            self.ParentObject = ParentObject
            self.RawTestSessionDataPath = self.ParentObject.RawTestSessionDataPath
        
        if InitialAttributes:
            self.Attributes.update(InitialAttributes)
        
        if DisplayOptions:
            self.DisplayOptions.update(DisplayOptions)
        
        
        if self.Attributes['TestResultSubDirectory']:
            self.RawTestSessionDataPath += '/'+self.Attributes['TestResultSubDirectory']
        
        
        self.CustomInit();
        
        if not self.Title:
            self.Title = self.NameSingle
        
        # Module Path
        self.ModulePath = self.NameSingle
        
        if InitialModulePath:
            self.ModulePath = InitialModulePath
        
        if InitialFinalResultsStoragePath:
            self.FinalResultsStoragePath = InitialFinalResultsStoragePath
            
        self.RelativeFinalResultsStoragePath = ''
        
        
        if self.ParentObject:
            self.FinalResultsStoragePath = self.ParentObject.FinalResultsStoragePath
            self.RelativeFinalResultsStoragePath = self.ParentObject.RelativeFinalResultsStoragePath
            self.ModulePath = self.ParentObject.ModulePath + '.' + self.ModulePath
            
        
        if self.Attributes['StorageKey']:
            self.FinalResultsStoragePath += '/'+self.Attributes['StorageKey']
            self.RelativeFinalResultsStoragePath += '/'+self.Attributes['StorageKey']
        else:
            self.FinalResultsStoragePath += '/'+self.NameSingle
            self.RelativeFinalResultsStoragePath += '/'+self.NameSingle
        self.SetFinalResultsStoragePath()
        
        
        
        
        if not os.path.exists(self.FinalResultsStoragePath):
            os.makedirs(self.FinalResultsStoragePath)
        
        # Load all sub test results in correct order
        i2 = len(self.ResultData['SubTestResultDictList'])
        for i in self.ResultData['SubTestResultDictList']:
            if i.has_key('Module'):
                SubModule = i['Module']
            else:
                SubModule = i['Key']
                i['Module'] = SubModule
                
            if i.has_key('InitialAttributes'):
                pass
            else:
                i['InitialAttributes'] = {}
            
            # set the test date for all test results
            i['InitialAttributes'].update({
                    'TestDate':self.Attributes['TestDate']
            })
            
            # Ensure all keys of display properties are set
            DisplayOptions = {
                'Order':i2,
                'Width':1,
                'Show':True,
                'GroupWithNext':False,
            }
            
            if i.has_key('DisplayOptions'):
                DisplayOptions.update(i['DisplayOptions'])
            
            i['DisplayOptions'] = DisplayOptions
            
            f = __import__(self.ModulePath+'.'+SubModule+'.TestResult' ,fromlist=[''])
            
            self.ResultData['SubTestResults'][ i['Key'] ] = f.TestResult(
                self.TestResultEnvironmentObject, 
                self, 
                None, 
                None, 
                i['InitialAttributes'], 
                i['Key'],
                i['DisplayOptions']
            )
            
            i['TestResultObject'] = self.ResultData['SubTestResults'][ i['Key']]
            i2+= 1
            
        
            
    '''
        Populates all necessary data
        @final
    '''
    def PopulateAllData(self):
        self.OpenFileHandle();
        for i in self.ResultData['SubTestResultDictList']:
            if i['TestResultObject'].Enabled:
                self.SetCanvasSize()
                try:
                    i['TestResultObject'].PopulateAllData()
                except Exception as inst:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    # Start red color
                    sys.stdout.write("\x1b[31m")
                    sys.stdout.flush()
                    # Print error message
                    print '\x1b[31mException while processing', i['TestResultObject'].FinalResultsStoragePath
                    # Print traceback
                    traceback.print_exception(exc_type, exc_obj, exc_tb)
                    # Stop red color
                    sys.stdout.write("\x1b[0m")
                    sys.stdout.flush()

                    self.TestResultEnvironmentObject.ErrorList.append(
                                                                      {'ModulePath':i['TestResultObject'].ModulePath,
                                                                       'ErrorCode': inst,
                                                                       'FinalResultsStoragePath':i['TestResultObject'].FinalResultsStoragePath}
                                                                      )
                    #todo Felix: handel exceptions
                
        self.SetCanvasSize()
        try:
            self.PopulateResultData()
        except Exception as inst:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    # Start red color
                    sys.stdout.write("\x1b[31m")
                    sys.stdout.flush()
                    print '\x1b[31mException while processing', self.FinalResultsStoragePath
                    # Print traceback
                    traceback.print_exception(exc_type, exc_obj, exc_tb)
                    # Stop red color
                    sys.stdout.write("\x1b[0m")
                    sys.stdout.flush()

                    self.TestResultEnvironmentObject.ErrorList.append(
                                                                      {'ModulePath':self.ModulePath,
                                                                       'ErrorCode': inst,
                                                                       'FinalResultsStoragePath':self.FinalResultsStoragePath}
#                                                                        'FinalResultsStoragePath':i['TestResultObject'].FinalResultsStoragePath}
                                                                      )
    
    '''
        Manually close all file handles of the sub tests
        @final
    '''
    def CloseSubTestResultFileHandles(self, Level = 0):
        for i in self.ResultData['SubTestResultDictList']:
            if i['TestResultObject'].Enabled:
                i['TestResultObject'].CloseSubTestResultFileHandles(Level+1)
                
        if Level:
            if self.FileHandle:
                try:
                    self.FileHandle.close()
                except:
                    try:
                        self.FileHandle.Close()
                    except:
                        pass
    '''
        Reads all attributes and writes it to the memory
    '''
    def CustomInit(self):
        pass
    
    '''
        Opens a file handle just before populating data
    '''
    def OpenFileHandle(self):
        pass
    
    
    '''
        Create a unique ID for creating root histograms
    '''
    def GetUniqueID(self):
        return self.TestResultEnvironmentObject.GetUniqueID(self.NameSingle)
    
    '''
        Sets the storage path
    '''
    def SetFinalResultsStoragePath(self):
        pass
    
    def CanvasSize(self,canvas):
        canvas.SetCanvasSize(
            self.DisplayOptions['Width']*self.TestResultEnvironmentObject.Configuration['DefaultValues']['CanvasWidth'],
            self.TestResultEnvironmentObject.Configuration['DefaultValues']['CanvasHeight']
        )
        canvas.Draw()
        canvas.Update()
        return canvas
    '''
        Sets the canvas size
    '''
    def SetCanvasSize(self):
        self.Canvas = self.CanvasSize(self.Canvas)
#         self.Canvas.SetCanvasSize(
#             self.DisplayOptions['Width']*self.TestResultEnvironmentObject.Configuration['DefaultValues']['CanvasWidth'],
#             self.TestResultEnvironmentObject.Configuration['DefaultValues']['CanvasHeight']
#         )
#         self.Canvas.Draw()
#         self.Canvas.Update()
    
    
    '''
        Generate the filename including the full path to the plot file according to the format
    '''
    def GetPlotFileName(self):
        Suffix = self.ResultData['Plot']['Format']
        return self.FinalResultsStoragePath+'/'+self.NameSingle+'.'+Suffix
    
    '''
        Get the sub test result list in the display order
    '''
    def GetSortedSubTestResultDictList(self):
        # sort sub test results according to display order
        return sorted(
            self.ResultData['SubTestResultDictList'],
            key=lambda i: i['DisplayOptions']['Order']
        )
        
        
    '''
        Reads all test results and writes it to the memory
    '''
    def PopulateResultData(self):
        pass
    
    '''
        Generates all output files
    '''
    def GenerateFinalOutput(self):
        for i in self.ResultData['SubTestResults']:
            self.ResultData['SubTestResults'][i].GenerateFinalOutput()
            
        self.GenerateDataFiles()
    
    '''
        Generate files like Key/Value pairs in JSON format, ASCII-files, HTML-files, etc.
        @final
    '''
    def GenerateDataFiles(self):
        self.GenerateDataFileHTML()
        self.GenerateDataFileJSON()
    
    '''
        Generate HTML file
        @final
    '''
    def GenerateDataFileHTML(self):
        HtmlParser = self.TestResultEnvironmentObject.HtmlParser
        
        HTMLFileName = 'TestResult.html'
        
        FinalHTML = ''
        HTMLTemplate = self.TestResultEnvironmentObject.TestResultHTMLTemplate
        FinalHTML = HTMLTemplate
        Levels = self.ModulePath[:].split('.')
        
        # Stylesheet

        StylesheetHTMLTemplate = HtmlParser.getSubpart(HTMLTemplate, '###HEAD_STYLESHEET_TEMPLATE###')
        StylesheetHTML = HtmlParser.substituteMarkerArray(
            StylesheetHTMLTemplate,
            {
                '###STYLESHEET###':self.TestResultEnvironmentObject.MainStylesheet+
                    self.TestResultEnvironmentObject.TestResultStylesheet,
            }
        )
        FinalHTML = HtmlParser.substituteSubpart(
            FinalHTML, 
            '###HEAD_STYLESHEETS###', 
            StylesheetHTML
        )
        FinalHTML = HtmlParser.substituteSubpart(
            FinalHTML, 
            '###HEAD_STYLESHEET_TEMPLATE###', 
            ''
        )
        
        
        # Clickpath
        
        ClickPathEntries = []
        ClickPathEntryTemplate = HtmlParser.getSubpart(HTMLTemplate, '###CLICKPATH_ENTRY###')
        
        
        
        LevelPath = ''
        i = 0
        tmpTestResultObject = self
        
        
        for Level in Levels[2:]:
            LevelPath = '../'*i
            ClickPathEntries.append(HtmlParser.substituteMarkerArray(
                ClickPathEntryTemplate,
                {
                    '###URL###':HtmlParser.MaskHTML(LevelPath+HTMLFileName),
                    '###LABEL###':HtmlParser.MaskHTML(tmpTestResultObject.Title)                    
                }
            ))
            if self.ParentObject:
                tmpTestResultObject = tmpTestResultObject.ParentObject
            
            i+=1
        if not self.OverviewHTMLLink:
            OverviewHTMLLink = os.path.relpath(self.TestResultEnvironmentObject.GlobalOverviewPath+'/Overview.html',self.FinalResultsStoragePath)        
        else:
            OverviewHTMLLink = self.OverviewHTMLLink
        ClickPathEntries.append(HtmlParser.substituteMarkerArray(
                ClickPathEntryTemplate,
                {
                    '###URL###':HtmlParser.MaskHTML(OverviewHTMLLink),
                    '###LABEL###':'Overview'
                }
            ))
        
        ClickPathEntries.reverse() 
        
        
        CSSClasses = ''
        
        #Result Data
        FinalHTML = HtmlParser.substituteSubpartArray(
            FinalHTML, 
            {
                '###CLICKPATH_ENTRY###': ''.join(ClickPathEntries),
                '###RESULTDATA###': self.GenerateResultDataHTML(self, 0, self.DisplayOptions),
                '###ADDITIONALCSSCLASSES###': CSSClasses,
            }
        )
        # Do it again for the ghost
        FinalHTML = HtmlParser.substituteSubpartArray(
            FinalHTML, 
            {
                '###CLICKPATH_ENTRY###': ''.join(ClickPathEntries),
            }
        )
        
        f = open(self.FinalResultsStoragePath+'/'+HTMLFileName, 'w')
        f.write(FinalHTML)
        f.close()
        
        
        
    '''
        Generate Result Data HTML for usage in HTML files
        @final
    '''
    def GenerateResultDataHTML(self, TestResultObject, RecursionLevel, DisplayOptions):
        HtmlParser = self.TestResultEnvironmentObject.HtmlParser
        HTMLTemplate = self.TestResultEnvironmentObject.TestResultHTMLTemplate
        ResultDataHTML = HtmlParser.getSubpart(HTMLTemplate, '###RESULTDATA###')
        HTMLFileName =  'TestResult.html'
        
        CSSClasses = self.NameSingle
        

        
        
        ResultDataHTML = HtmlParser.substituteMarker(ResultDataHTML, 
            '###RESULTDATAADDITIONALCSSCLASSES###', 
            HtmlParser.MaskHTML(CSSClasses)
        )
        
        RecursionRelativePath = ''
        if RecursionLevel > 0:
            PathParts = TestResultObject.FinalResultsStoragePath.split('/')
            #print PathParts
            RecursionRelativePath = PathParts[-1]+'/'
        
        # Title
        if not TestResultObject.Title:
            TestResultObject.Title = TestResultObject.NameSingle
        MyObjectTestDate = '';
        if RecursionLevel == 0 and TestResultObject.Attributes['TestDate']:
            
            MyObjectTestDate = 'Test Date: '+datetime.datetime.fromtimestamp(float(TestResultObject.Attributes['TestDate'])).strftime("%Y-%m-%d %H:%m")
        
        MainTestResultAdditionalClasses = ''
        
        if RecursionLevel == 0:
            MainTestResultAdditionalClasses += 'MainTestResult Group'
            if self.DisplayOptions['Width'] > 1: 
                MainTestResultAdditionalClasses += ' Width'+str(self.DisplayOptions['Width'])
        
        ResultDataHTML = HtmlParser.substituteMarkerArray(
            ResultDataHTML, 
            {
                '###TITLE###':HtmlParser.MaskHTML(TestResultObject.Title),
                '###TESTDATE###':MyObjectTestDate,
                '###MAINTESTRESULTADDITIONALCLASSES###':MainTestResultAdditionalClasses,
            }
        )
        # Plot
        PlotHTML = ''
        if TestResultObject.ResultData['Plot']['Enabled']:
            PlotHTML = HtmlParser.getSubpart(HTMLTemplate, '###PLOT###')
            PlotHTMLTemplate = HtmlParser.getSubpart(HTMLTemplate, '###PLOT###')
            PlotImageHTML = HtmlParser.getSubpart(PlotHTMLTemplate, '###PLOT_IMAGE###')
            '''PlotImageHTML = {
                'SVG':'',
                'PNG':''
            }
            if TestResultObject.ResultData['Plot']['Format'] == 'svg':
                PlotImageHTML['SVG'] = HtmlParser.getSubpart(PlotHTMLTemplate, '###PLOT_IMAGE_SVG###')
            elif TestResultObject.ResultData['Plot']['Format'] == 'png':
                PlotImageHTML['PNG'] = HtmlParser.getSubpart(PlotHTMLTemplate, '###PLOT_IMAGE_PNG###')
            
            for i in PlotImageHTML:
            '''
            
            # file operations for svg
            if TestResultObject.ResultData['Plot']['Format'] == 'svg' and RecursionLevel == 0 and self.SavePlotFile:
                f = open(TestResultObject.ResultData['Plot']['ImageFile'], 'r')
                SVGContent = f.read()
                f.close()
                
                # fix an error in chrome / safari when displaying resized svg
                if SVGContent.find('<svg preserveAspectRatio') == -1:
                    SVGContent = SVGContent.replace('<svg', '<svg preserveAspectRatio="xMinYMin"',1)
                
                # remove an invalid space in attribute width and height 
                SVGContent = SVGContent.replace('width=" ', 'width="')
                SVGContent = SVGContent.replace('height=" ', 'height="')
                SVGContent = SVGContent.replace('x=" ', 'x="')
                SVGContent = SVGContent.replace('y=" ', 'y="')
                SVGContent = SVGContent.replace('r=" ', 'r="')
                SVGContent = SVGContent.replace('=" ', '="')
                SVGContent = SVGContent.replace('&#786', '&#176')
                
                if self.GzipSVG and TestResultObject.ResultData['Plot']['ImageFile'].find('.svgz') == -1:
                    os.remove(TestResultObject.ResultData['Plot']['ImageFile'])
                    TestResultObject.ResultData['Plot']['ImageFile']+='z'
                    f = gzip.GzipFile(TestResultObject.ResultData['Plot']['ImageFile'], 'w')
                    
                else:
                    f = open(TestResultObject.ResultData['Plot']['ImageFile'], 'w')
                    if os.path.exists(TestResultObject.ResultData['Plot']['ImageFile']+'z'):
                        os.remove(TestResultObject.ResultData['Plot']['ImageFile']+'z')
                    
                f.write(SVGContent)
                f.close()
            
            if not TestResultObject.ResultData['Plot']['Caption']:
                TestResultObject.ResultData['Plot']['Caption'] = TestResultObject.Title
                
            PlotImageHTML = HtmlParser.substituteMarkerArray(
                PlotImageHTML,
                {
                    '###FILENAME###':HtmlParser.MaskHTML(RecursionRelativePath+os.path.basename(TestResultObject.ResultData['Plot']['ImageFile'])),
                    '###IMAGELARGECONTAINERID###':HtmlParser.MaskHTML(TestResultObject.Name+'_'+TestResultObject.Key),
                    '###MARGIN_TOP###':str(int(-800./float(DisplayOptions['Width']*self.TestResultEnvironmentObject.Configuration['DefaultValues']['CanvasWidth'])*
                        float(self.TestResultEnvironmentObject.Configuration['DefaultValues']['CanvasHeight'])/2.)),
                    '###TITLE###':TestResultObject.ResultData['Plot']['Caption'],
                    '###WIDTH###':str(DisplayOptions['Width']),
                    '###HEIGHT###':str(1),
                }
            )
            #PlotHTML = HtmlParser.substituteSubpart(PlotHTML, '###PLOT_IMAGE_'+i+'###', PlotImageHTML)
            PlotHTML = HtmlParser.substituteSubpart(PlotHTML, '###PLOT_IMAGE###', PlotImageHTML)
            
            
        ResultDataHTML = HtmlParser.substituteSubpart(ResultDataHTML, '###PLOT###', PlotHTML)
            
        #Key Value Dict Pairs
        KeyValueDictPairsRowHTMLTemplate = HtmlParser.getSubpart(HTMLTemplate, '###KEYVALUEDICTPAIRS_ROW###')
        KeyValueDictPairsRows = ''
        
        for i in TestResultObject.ResultData['KeyList']:
            if not TestResultObject.ResultData['KeyValueDictPairs'].has_key(i):
                warnings.warn('Cannot find Key: %s'%i)
                continue
            if not TestResultObject.ResultData['KeyValueDictPairs'][i].has_key('Unit'):
                TestResultObject.ResultData['KeyValueDictPairs'][i]['Unit'] = ''
            html_value = HtmlParser.MaskHTML(str(TestResultObject.ResultData['KeyValueDictPairs'][i]['Value']))
            if TestResultObject.ResultData['KeyValueDictPairs'][i].has_key('Sigma'):
                TestResultObject.ResultData['KeyValueDictPairs'][i]['SigmaOutput'] = ' +/- %s'%TestResultObject.ResultData['KeyValueDictPairs'][i]['Sigma']
                html_value += ' &plusmn; ' + HtmlParser.MaskHTML(str(TestResultObject.ResultData['KeyValueDictPairs'][i]['Sigma']))
            else:
                TestResultObject.ResultData['KeyValueDictPairs'][i]['SigmaOutput'] = ''

            if not TestResultObject.ResultData['KeyValueDictPairs'][i].has_key('Label'):
                TestResultObject.ResultData['KeyValueDictPairs'][i]['Label'] = i

            KeyValueDictPairsRows += HtmlParser.substituteMarkerArray(
                KeyValueDictPairsRowHTMLTemplate,
                {
                    '###KEY###':HtmlParser.MaskHTML(i),
                    '###LABEL###':HtmlParser.MaskHTML(
                        TestResultObject.ResultData['KeyValueDictPairs'][i]['Label']
                        ),
                    '###VALUE###': html_value,
                    '###UNIT###':HtmlParser.MaskHTML(
                        TestResultObject.ResultData['KeyValueDictPairs'][i]['Unit']
                        ),
                }
            )
        ResultDataHTML = HtmlParser.substituteSubpart(ResultDataHTML, 
            '###KEYVALUEDICTPAIRS_ROW###', 
            KeyValueDictPairsRows)
        
        #Table
        TableHTML = ''
        if RecursionLevel == 0 or True:
            TableHTMLTemplate = HtmlParser.getSubpart(HTMLTemplate, '###TABLE###')
            TableHTML = HtmlParser.GenerateTableHTML(TableHTMLTemplate, TestResultObject.ResultData['Table'], {
                    '###ADDITIONALCSSCLASS###':'',
                    '###ID###':'Table',
            })
        
        ResultDataHTML = HtmlParser.substituteSubpart(ResultDataHTML, 
            '###TABLE###', 
            TableHTML)
        
        # Sub Test Results
        SubTestResultListHTML = ''
        
        if RecursionLevel == 0:
            GroupWithNext = False
            i2 = 0
            for i in TestResultObject.GetSortedSubTestResultDictList():
                if i['TestResultObject'].DisplayOptions['Show']:
                
                    GroupCSSClass = '' 
                    if i2%5 == 0:
                        GroupCSSClass += ' WidthNthChild5n'
                    if i2%4 == 0:
                        GroupCSSClass += ' WidthNthChild4n'
                    if i2%3 == 0:
                        GroupCSSClass += ' WidthNthChild3n'
                    if i2%2 == 0:
                        GroupCSSClass += ' WidthNthChild2n'
                    
                    if i['TestResultObject'].DisplayOptions['Width'] > 1:
                        GroupCSSClass += ' Width'+str(i['TestResultObject'].DisplayOptions['Width'])
                    
                    if not GroupWithNext:
                        SubTestResultListHTML +=  HtmlParser.substituteMarker(
                            HtmlParser.getSubpart(HTMLTemplate, '###SUBTESTRESULTGROUP_START###'), 
                            '###SUBTESTRESULTGROUP_ADDITIONALCSSCLASSES###', 
                            HtmlParser.MaskHTML(GroupCSSClass)
                        )
                        # only increase the width counter for a group start
                        i2 += i['TestResultObject'].DisplayOptions['Width']
                        
                    
                        
                        
                    SubTestResultListHTML += self.GenerateResultDataHTML(i['TestResultObject'], RecursionLevel + 1, i['TestResultObject'].DisplayOptions)
                    
                    
                    if not i['TestResultObject'].DisplayOptions['GroupWithNext']:
                        # if the last element was in a group but the current not, close the group
                        SubTestResultListHTML += HtmlParser.getSubpart(HTMLTemplate, '###SUBTESTRESULTGROUP_END###')
        
                    GroupWithNext = i['DisplayOptions']['GroupWithNext']
                
                
                
            # if the last element was in a group, close the group
            if GroupWithNext:
                        SubTestResultListHTML += HtmlParser.getSubpart(HTMLTemplate, '###SUBTESTRESULTGROUP_END###')
                        
        else:
            
            SubTestResultListItemHTMLTemplate = HtmlParser.getSubpart(HTMLTemplate, '###SUBTESTRESULTLIST_ITEM###')
            SubTestResultListHTML = HtmlParser.getSubpart(HTMLTemplate, '###SUBTESTRESULTLIST###')
            SubTestResultListItems = ''
            
            # Overview link
            SubTestResultOverviewLinkHTML = HtmlParser.getSubpart(SubTestResultListHTML, '###OVERVIEW_LINK###')
            if TestResultObject.ResultData['SubTestResultDictList']:
                SubTestResultOverviewLinkHTML = HtmlParser.substituteMarkerArray(
                    SubTestResultOverviewLinkHTML,
                    {
                        '###URL###':HtmlParser.MaskHTML(
                            os.path.basename(TestResultObject.FinalResultsStoragePath)+'/'+HTMLFileName
                            ),
                    }
                )
            else:
                SubTestResultOverviewLinkHTML = ''
                
            # Subtests
            for i in TestResultObject.GetSortedSubTestResultDictList():
                if i['DisplayOptions']['Show']:
                    SubTestResultListItems += HtmlParser.substituteMarkerArray(
                        SubTestResultListItemHTMLTemplate,
                        {
                            '###URL###':HtmlParser.MaskHTML(
                                os.path.basename(TestResultObject.FinalResultsStoragePath)+'/'+
                                os.path.basename(i['TestResultObject'].FinalResultsStoragePath)+'/'+HTMLFileName
                                ),
                            '###LABEL###':HtmlParser.MaskHTML(
                                i['TestResultObject'].Title
                                ),
                        }
                    )
            SubTestResultListHTML = HtmlParser.substituteSubpartArray(
                SubTestResultListHTML, 
                {
                    '###SUBTESTRESULTLIST_ITEM###':SubTestResultListItems,
                    '###OVERVIEW_LINK###':SubTestResultOverviewLinkHTML,
                }
            )
            
            
            if not SubTestResultListItems:
                SubTestResultListHTML = ''
            
        ResultDataHTML = HtmlParser.substituteSubpartArray(
            ResultDataHTML, 
            {
                '###SUBTESTRESULTLIST###':SubTestResultListHTML,
                '###SUBTESTRESULTGROUP_START###':'',
                '###SUBTESTRESULTGROUP_END###':'',
            }
        )
        return ResultDataHTML
        
        
    '''
        Generate file from ResultData['KeyValueDictPairs'] Key/Value pairs in JSON format
        @final
    '''
    def GenerateDataFileJSON(self):
        try:
            data = self.ResultData['KeyValueDictPairs']
            for key in data:
                #{'NotAlivePixels': {'SigmaOutput': '', 'Unit': '', 'Value': Set([(0, 21, 31)]), 'Label': 'Pixels'}, 'MaskDefects': {'SigmaOutput': '', 'Unit': '', 'Value': Set([]), 'Label': 'Pixels'}, 'NoisyPixels': {'SigmaOutput': '', 'Unit': '', 'Value': Set([]), 'Label': 'Pixels'}, 'DeadPixels': {'SigmaOutput': '', 'Unit': '', 'Value': Set([(0, 21, 31)]), 'Label': 'Pixels'}, 'InefficentPixels': {'SigmaOutput': '', 'Unit': '', 'Value': Set([]), 'Label': 'Pixels'}}
                if data[key].has_key('Value'):
                    value = data[key]['Value']
                    if type(value) == Set:
                        value = list(value)
                        data[key]['Value']=value
                pass
#self.ResultData['KeyValueDictPairs']
            f = open(self.FinalResultsStoragePath+'/KeyValueDictPairs.json', 'w')
            f.write(json.dumps(self.ResultData['KeyValueDictPairs'], sort_keys=True,indent=4, separators=(',', ': ')))
            f.close()
        except:
            print 'Cannot create JSON for %s'%self.ResultData['KeyValueDictPairs']

    '''
        Generate file from ResultData['KeyValueDictPairs'] Key/Value pairs in ASCII format
        @final
    '''
    def GenerateDataFileASCII(self):
        pass
    
    '''
        Write all test results to the database
    '''
    def WriteToDatabase(self, ParentID = 0):
        ColumnMapping = {}
        ID = 0
        ID = self.CustomWriteToDatabase(ParentID)
        
        for i in self.ResultData['SubTestResults']:
            try: 
                self.ResultData['SubTestResults'][i].WriteToDatabase(ID)
            except Exception as inst:
                    print 'Error in subtest (write to database)', self.ResultData['SubTestResults'][i].ModulePath,self.ResultData['SubTestResults'][i].FinalResultsStoragePath
                    print inst
                    print inst.args
                    print sys.exc_info()[0]
                    print "\n\n------\n"
        
        self.PostWriteToDatabase()
        
    def CustomWriteToDatabase(self, ParentID):
        pass
    
    def PostWriteToDatabase(self):
        pass
        
    def __del__(self):
        self.CloseSubTestResultFileHandles()
