#!/usr/bin/python

#	Copyright (c) 2008 Matthew Ball
# 
#	Permission is hereby granted, free of charge, to any person
#	obtaining a copy of this software and associated documentation
#	files (the "Software"), to deal in the Software without
#	restriction, including without limitation the rights to use,
#	copy, modify, merge, publish, distribute, sublicense, and/or sell
#	copies of the Software, and to permit persons to whom the
#	Software is furnished to do so, subject to the following
#	conditions:
# 
#	The above copyright notice and this permission notice shall be
#	included in all copies or substantial portions of the Software.
#
#	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#	EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
#	OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
#	NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#	OTHER DEALINGS IN THE SOFTWARE.

import sys 
import os 
import fnmatch
import re
import errno
from optparse import OptionParser
from xml.dom import minidom

def _mkdir(newdir):
    if os.path.isdir(newdir):
        pass
    elif os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired " \
                      "dir, '%s', already exists." % newdir)
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            _mkdir(head)

        if tail:
            os.mkdir(newdir)

def fileIsDocumented(filePath):
	# Only XML files can contain documentation information
	if not os.path.splitext(filePath)[1] == ".xml":
		return False
	
	# Check if the object is documented
	originaldoc = minidom.parse(filePath)
	briefList = originaldoc.getElementsByTagName('briefdescription')
	detailList = originaldoc.getElementsByTagName('detaileddescription')

	for briefItem in briefList:
		paraList = briefItem.getElementsByTagName('para')
		if len(paraList) > 0:
			return True

	for detailItem in detailList:
		paraList = detailItem.getElementsByTagName('para')
		if len(paraList) > 0:
			return True

	return False

def nameForFile(filePath):
	if not os.path.splitext(filePath)[1] == ".xml":
		return None
	
	xmlDoc = minidom.parse(filePath)
	return xmlDoc.getElementsByTagName("name")[0].firstChild.data

def typeForFile(filePath):
	if not os.path.splitext(filePath)[1] == ".xml":
		return None
		
	xmlDoc = minidom.parse(filePath)
	return xmlDoc.getElementsByTagName("object")[0].attributes["kind"].value

def cleanXML(filePath, outputDirectory):
	if not fileIsDocumented(filePath):
		return
		
	fileName = os.path.split(filePath)[1]
		
	global verbose
	if verbose:
		print "Cleaning " + fileName
		
	_mkdir(outputDirectory)
	
	# Perform the XSL Transform
	tempPath = os.path.join(outputDirectory, fileName)
	stylesheetPath = os.path.join(sys.path[0], "object.xslt")
	os.system("xsltproc -o \"%s\" \"%s\" \"%s\"" % (tempPath, stylesheetPath, filePath))
	
	# Load the new XML file to get some values from it
	objectName = nameForFile(tempPath)
	objectType = typeForFile(tempPath)
	
	# Determine the appropriate subdirectory for the file
	if objectType == "class":
		finalPath = os.path.join(outputDirectory, "Classes")
	elif objectType == "category":
		finalPath = os.path.join(outputDirectory, "Categories")
	elif objectType == "protocol":
		finalPath = os.path.join(outputDirectory, "Protocols")
	_mkdir(finalPath)
	
	# Move the file to its final location
	finalPath = os.path.join(finalPath, objectName + ".xml")
	os.system("mv \"%s\" \"%s\"" % (tempPath, finalPath))
	
def createIndexXML(directory):
	outputPath = os.path.join(directory, "index.xml")
	indexXML = minidom.Document()
	
	projectElement = indexXML.createElement("project")
	projectElement.setAttribute("name", "##PROJECT##")
	indexXML.appendChild(projectElement)
	
	# Add one element per file
	for (path, dirs, files) in os.walk(directory):
		for fileName in files:
			# Only look at XML files
			if not os.path.splitext(fileName)[1] == ".xml":
				continue
			
			# Get information about the file
			filePath = os.path.join(path, fileName)
			objectName = nameForFile(filePath)
			objectType = typeForFile(filePath)
			
			# Create an <object> element
			objectElement = indexXML.createElement("object")
			objectElement.setAttribute("kind", objectType)
			projectElement.appendChild(objectElement)
			
			# Create a <name> element
			nameElement = indexXML.createElement("name")
			objectElement.appendChild(nameElement)
			nameText = indexXML.createTextNode(objectName)
			nameElement.appendChild(nameText)
			
	# Write the index file
	f = open(outputPath, "w")
	indexXML.writexml(f, "", "\t", "\n")
	f.close()
	
	return outputPath
	
def linkify(directory):
	indexFile = minidom.parse(os.path.join(directory, "index.xml"))
	documentedObjects = indexFile.getElementsByTagName("name")
	
	global verbose
	
	# Get each file
	for (path, dirs, files) in os.walk(directory):
		for fileName in files:
			# Skip the index and any non-xml files
			if fileName == "index.xml" or not os.path.splitext(fileName)[1] == ".xml":
				continue
			
			filePath = os.path.join(path, fileName)
			
			if verbose:
				print "Linkifying " + fileName
			
			f = open(filePath, "r")
			fileContents = f.read()
			f.close()
			
			# Remove all refs initially
			# We will recreate them ourselves
			fileContents = re.sub("\\<ref(?: .*)?\\>(.*?)\\</ref\\>", "\\1", fileContents);
			
			# Link to all Foundation and AppKit documentation
			# We don't want links in the name or file or ref
			macFoundationClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(NSMetadataQueryAttributeValueTuple|NSDistributedNotificationCenter|NSURLAuthenticationChallenge|NSPropertyListSerialization|NSScriptCommandDescription|NSMetadataQueryResultGroup|NSMutableAttributedString|NSScriptExecutionContext|NSScriptClassDescription|NSScriptObjectSpecifier|NSScriptCoercionHandler|NSMessagePortNameServer|NSURLCredentialStorage|NSSocketPortNameServer|NSDistantObjectRequest|NSDecimalNumberHandler|NSAppleEventDescriptor|NSScriptSuiteRegistry|NSPositionalSpecifier|NSMutableCharacterSet|NSMachBootstrapServer|NSInvocationOperation|NSDirectoryEnumerator|NSComparisonPredicate|NSURLProtectionSpace|NSTextCheckingResult|NSNotificationCenter|NSUniqueIDSpecifier|NSRelativeSpecifier|NSPropertySpecifier|NSNotificationQueue|NSNetServiceBrowser|NSMutableURLRequest|NSMutableDictionary|NSHTTPCookieStorage|NSCompoundPredicate|NSCachedURLResponse|NSAppleEventManager|NSValueTransformer|NSPointerFunctions|NSGarbageCollector|NSClassDescription|NSAttributedString|NSAssertionHandler|NSScriptWhoseTest|NSRandomSpecifier|NSProtocolChecker|NSNumberFormatter|NSMutableIndexSet|NSMiddleSpecifier|NSMethodSignature|NSKeyedUnarchiver|NSHTTPURLResponse|NSDistributedLock|NSAutoreleasePool|NSAffineTransform|NSWhoseSpecifier|NSSortDescriptor|NSRangeSpecifier|NSPortNameServer|NSOperationQueue|NSIndexSpecifier|NSDateComponents|NSBlockOperation|NSURLCredential|NSURLConnection|NSSpecifierTest|NSScriptCommand|NSRecursiveLock|NSNameSpecifier|NSMutableString|NSMetadataQuery|NSKeyedArchiver|NSExistsCommand|NSDistantObject|NSDeleteCommand|NSDecimalNumber|NSDateFormatter|NSCreateCommand|NSConditionLock|NSUserDefaults|NSPointerArray|NSOutputStream|NSNotification|NSMutableArray|NSMetadataItem|NSDeserializer|NSCountCommand|NSCloseCommand|NSCloneCommand|NSCharacterSet|NSXMLDocument|NSUndoManager|NSURLResponse|NSURLProtocol|NSURLDownload|NSSpellServer|NSQuitCommand|NSProcessInfo|NSPortMessage|NSOrthography|NSMutableData|NSMoveCommand|NSMessagePort|NSLogicalTest|NSInputStream|NSFileManager|NSAppleScript|NSXMLElement|NSXMLDTDNode|NSUnarchiver|NSURLRequest|NSSocketPort|NSSetCommand|NSSerializer|NSNetService|NSMutableSet|NSInvocation|NSHTTPCookie|NSGetCommand|NSFileHandle|NSExpression|NSEnumerator|NSDictionary|NSCountedSet|NSConnection|NSXMLParser|NSURLHandle|NSPredicate|NSPortCoder|NSOperation|NSIndexPath|NSHashTable|NSFormatter|NSException|NSCondition|NSURLCache|NSTimeZone|NSMapTable|NSMachPort|NSIndexSet|NSCalendar|NSArchiver|NSXMLNode|NSScanner|NSRunLoop|NSXMLDTD|NSThread|NSString|NSStream|NSObject|NSNumber|NSLocale|NSBundle|NSValue|NSTimer|NSProxy|NSError|NSCoder|NSArray|NSTask|NSPort|NSPipe|NSNull|NSLock|NSHost|NSDate|NSData|NSURL|NSSet)"
			fileContents = re.sub(macFoundationClassesPattern, '\\1<ref id="http://developer.apple.com/mac/library/documentation/Cocoa/Reference/Foundation/Classes/\\2_Class/index">\\2</ref>', fileContents)
			
			macFoundationProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(NSURLAuthenticationChallengeSender|NSObjCTypeSerializationCallBack|NSScriptingComparisonMethods|NSNetServiceBrowserDelegate|NSKeyedUnarchiverDelegate|NSErrorRecoveryAttempting|NSScriptObjectSpecifiers|NSDecimalNumberBehaviors|NSMetadataQueryDelegate|NSKeyedArchiverDelegate|NSScriptKeyValueCoding|NSSpellServerDelegate|NSNetServiceDelegate|NSConnectionDelegate|NSXMLParserDelegate|NSURLProtocolClient|NSKeyValueObserving|NSComparisonMethods|NSMachPortDelegate|NSURLHandleClient|NSFastEnumeration|NSStreamDelegate|NSMutableCopying|NSKeyValueCoding|NSPortDelegate|NSLocking|NSCopying|NSCoding)"
			fileContents = re.sub(macFoundationProtocolsPattern, '\\1<ref id="http://developer.apple.com/mac/library/documentation/Cocoa/Reference/Foundation/Protocols/\\2_Protocol/index">\\2</ref>', fileContents)
			
			macAppKitClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(NSPredicateEditorRowTemplate|NSUserDefaultsController|NSMutableParagraphStyle|NSDictionaryController|NSSecureTextFieldCell|NSNibControlConnector|NSTextAttachmentCell|NSRunningApplication|NSPersistentDocument|NSNibOutletConnector|NSLevelIndicatorCell|NSDocumentController|NSCollectionViewItem|NSSpeechSynthesizer|NSProgressIndicator|NSPathComponentCell|NSOpenGLPixelFormat|NSOpenGLPixelBuffer|NSWindowController|NSToolbarItemGroup|NSTextInputContext|NSSpeechRecognizer|NSSegmentedControl|NSObjectController|NSAnimationContext|NSTableHeaderView|NSTableHeaderCell|NSSecureTextField|NSSearchFieldCell|NSPredicateEditor|NSPopUpButtonCell|NSGraphicsContext|NSArrayController|NSViewController|NSTreeController|NSTokenFieldCell|NSTextTableBlock|NSTextAttachment|NSPrintOperation|NSPasteboardItem|NSParagraphStyle|NSLevelIndicator|NSGlyphGenerator|NSFontDescriptor|NSDatePickerCell|NSCustomImageRep|NSCollectionView|NSCachedImageRep|NSBitmapImageRep|NSViewAnimation|NSTextFieldCell|NSTextContainer|NSSegmentedCell|NSOpenGLContext|NSLayoutManager|NSATSTypesetter|NSTrackingArea|NSSpellChecker|NSPICTImageRep|NSNibConnector|NSMenuItemCell|NSComboBoxCell|NSToolbarItem|NSTextStorage|NSTableColumn|NSTabViewItem|NSStepperCell|NSSearchField|NSRulerMarker|NSPopUpButton|NSPathControl|NSPDFImageRep|NSOutlineView|NSOpenGLLayer|NSHelpManager|NSFontManager|NSFileWrapper|NSEPSImageRep|NSColorPicker|NSBrowserCell|NSApplication|NSTypesetter|NSTokenField|NSStatusItem|NSSliderCell|NSScrollView|NSRuleEditor|NSPrintPanel|NSPasteboard|NSPageLayout|NSOpenGLView|NSDatePicker|NSController|NSColorSpace|NSColorPanel|NSCIImageRep|NSButtonCell|NSBezierPath|NSActionCell|NSWorkspace|NSTextTable|NSTextField|NSTextBlock|NSTableView|NSStatusBar|NSSplitView|NSSavePanel|NSRulerView|NSResponder|NSPrintInfo|NSOpenPanel|NSImageView|NSImageCell|NSGlyphInfo|NSFontPanel|NSColorWell|NSColorList|NSAnimation|NSTreeNode|NSTextView|NSTextList|NSScroller|NSPathCell|NSMenuView|NSMenuItem|NSImageRep|NSGradient|NSFormCell|NSDocument|NSDockTile|NSComboBox|NSClipView|NSToolbar|NSTextTab|NSTabView|NSStepper|NSPrinter|NSControl|NSBrowser|NSWindow|NSSlider|NSShadow|NSScreen|NSMatrix|NSDrawer|NSCursor|NSButton|NSTouch|NSSound|NSPanel|NSImage|NSEvent|NSColor|NSAlert|NSView|NSText|NSMenu|NSForm|NSFont|NSCell|NSNib|NSBox)"
			fileContents = re.sub(macAppKitClassesPattern, '\\1<ref id="http://developer.apple.com/mac/library/documentation/Cocoa/Reference/ApplicationKit/Classes/\\2_Class/index">\\2</ref>', fileContents)
			
			macAppKitProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(NSDictionaryControllerKeyValuePair|NSAnimatablePropertyContainer|NSValidatedUserInterfaceItem|NSPasteboardItemDataProvider|NSControlTextEditingDelegate|NSSpeechSynthesizerDelegate|NSUserInterfaceValidations|NSSpeechRecognizerDelegate|NSPrintPanelAccessorizing|NSKeyValueBindingCreation|NSTokenFieldCellDelegate|NSDatePickerCellDelegate|NSComboBoxCellDataSource|NSCollectionViewDelegate|NSToolbarItemValidation|NSOutlineViewDataSource|NSOpenSavePanelDelegate|NSLayoutManagerDelegate|NSIgnoreMisspelledWords|NSTableViewDataSource|NSPathControlDelegate|NSOutlineViewDelegate|NSFontPanelValidation|NSDraggingDestination|NSColorPickingDefault|NSApplicationDelegate|NSTokenFieldDelegate|NSTextAttachmentCell|NSRuleEditorDelegate|NSEditorRegistration|NSComboBoxDataSource|NSColorPickingCustom|NSTextFieldDelegate|NSTableViewDelegate|NSSplitViewDelegate|NSPasteboardWriting|NSPasteboardReading|NSAnimationDelegate|NSTextViewDelegate|NSServicesRequests|NSPathCellDelegate|NSComboBoxDelegate|NSWindowScripting|NSToolbarDelegate|NSTextInputClient|NSTabViewDelegate|NSBrowserDelegate|NSWindowDelegate|NSMenuValidation|NSMatrixDelegate|NSDrawerDelegate|NSDraggingSource|NSDockTilePlugIn|NSChangeSpelling|NSSoundDelegate|NSImageDelegate|NSAlertDelegate|NSAccessibility|NSToolTipOwner|NSTextDelegate|NSPlaceholders|NSMenuDelegate|NSGlyphStorage|NSDraggingInfo|NSNibAwaking|NSTextInput|NSEditor)"
			fileContents = re.sub(macAppKitProtocolsPattern, '\\1<ref id="http://developer.apple.com/mac/library/documentation/Cocoa/Reference/ApplicationKit/Protocols/\\2_Protocol/index">\\2</ref>', fileContents)
			
			# iPhone-specific frameworks
			iphoneAddressBookUIClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(ABPeoplePickerNavigationController|ABUnknownPersonViewController|ABNewPersonViewController|ABPersonViewController)"
			fileContents = re.sub(iphoneAddressBookUIClassesPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/AddressBookUI/Reference/\\2_Class/index">\\2</ref>', fileContents)
			
			iphoneAddressBookUIProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(ABPeoplePickerNavigationControllerDelegate|ABUnknownPersonViewControllerDelegate|ABNewPersonViewControllerDelegate|ABPersonViewControllerDelegate)"
			fileContents = re.sub(iphoneAddressBookUIProtocolsPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/AddressBookUI/Reference/\\2_Protocol/index">\\2</ref>', fileContents)
			
			iphoneGameKitClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(GKPeerPickerController|GKVoiceChatService|GKSession)"
			fileContents = re.sub(iphoneGameKitClassesPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/GameKit/Reference/\\2_Class/index">\\2</ref>', fileContents)
			
			iphoneGameKitProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(GKPeerPickerControllerDelegate|GKSessionDelegate|GKVoiceChatClient)"
			fileContents = re.sub(iphoneGameKitProtocolsPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/GameKit/Reference/\\2_Protocol/index">\\2</ref>', fileContents)
			
			iphoneMapKitClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(MKPinAnnotationView|MKReverseGeocoder|MKAnnotationView|MKUserLocation|MKPlacemark|MKMapView)"
			fileContents = re.sub(iphoneMapKitClassesPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/MapKit/Reference/\\2_Class/index">\\2</ref>', fileContents)
			
			iphoneMapKitProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(MKReverseGeocoderDelegate|MKMapViewDelegate|MKAnnotation)"
			fileContents = re.sub(iphoneMapKitProtocolsPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/MapKit/Reference/\\2_Protocol/index">\\2</ref>', fileContents)
			
			iphoneMessageUIClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(MFMailComposeViewController)"
			fileContents = re.sub(iphoneMessageUIClassesPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/MessageUI/Reference/\\2_Class/index">\\2</ref>', fileContents)
			
			iphoneMessageUIProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(MFMailComposeViewControllerDelegate)"
			fileContents = re.sub(iphoneMessageUIProtocolsPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/MessageUI/Reference/\\2_Protocol/index">\\2</ref>', fileContents)
			
			iphoneUIKitClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(UILocalizedIndexedCollation|UISearchDisplayController|UIVideoEditorController|UIImagePickerController|UIActivityIndicatorView|UINavigationController|UIAccessibilityElement|UITableViewController|UITabBarController|UISegmentedControl|UIViewController|UINavigationItem|UIMenuController|UITableViewCell|UINavigationBar|UIBarButtonItem|UIAccelerometer|UIProgressView|UIAcceleration|UIPageControl|UIApplication|UIActionSheet|UITabBarItem|UIScrollView|UIPickerView|UIPasteboard|UIDatePicker|UITextField|UITableView|UISearchBar|UIResponder|UIImageView|UIAlertView|UITextView|UIWebView|UIToolbar|UIControl|UIBarItem|UIWindow|UITabBar|UISwitch|UISlider|UIScreen|UIDevice|UIButton|UITouch|UILabel|UIImage|UIEvent|UIColor|UIView|UIFont)"
			fileContents = re.sub(iphoneUIKitClassesPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/UIKit/Reference/\\2_Class/index">\\2</ref>', fileContents)
			
			iphoneUIKitProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(UIVideoEditorControllerDelegate|UIImagePickerControllerDelegate|UIResponderStandardEditActions|UINavigationControllerDelegate|UITabBarControllerDelegate|UIAccessibilityContainer|UISearchDisplayDelegate|UINavigationBarDelegate|UIAccelerometerDelegate|UIPickerViewDataSource|UITableViewDataSource|UIApplicationDelegate|UIActionSheetDelegate|UIScrollViewDelegate|UIPickerViewDelegate|UITextFieldDelegate|UITableViewDelegate|UISearchBarDelegate|UIAlertViewDelegate|UITextViewDelegate|UIWebViewDelegate|UITextInputTraits|UITabBarDelegate|UIAccessibility)"
			fileContents = re.sub(iphoneUIKitProtocolsPattern, '\\1<ref id="http://developer.apple.com/iphone/library/documentation/UIKit/Reference/\\2_Protocol/index">\\2</ref>', fileContents)
			
			# Establish links to all files in the project
			classesList = []
			categoriesList = []
			protocolsList = []
			
			for documentedObject in documentedObjects:
				# We need to get rid of whitespace
				# (It's a "feature" of minidom)
				objectName = documentedObject.firstChild.data.replace("\n", "").replace("\t", "")
				objectType = documentedObject.parentNode.attributes["kind"].value
				
				if objectType == "class":
					classesList.append(objectName)
				elif objectType == "category":
					categoriesList.append(objectName)
				elif objectType == "protocol":
					protocolsList.append(objectName)
					
			if classesList:
				projectClassesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(" + '|'.join(classesList) + ")"
				fileContents = re.sub(projectClassesPattern, '\\1<ref id="../Classes/\\2">\\2</ref>', fileContents)
			
			if categoriesList:
				projectCategoriesPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(" + '|'.join(categoriesList) + ")"
				fileContents = re.sub(projectCategoriesPattern, '\\1<ref id="../Categories/\\2">\\2</ref>', fileContents)
			
			if protocolsList:
				projectProtocolsPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(" + '|'.join(protocolsList) + ")"
				fileContents = re.sub(projectProtocolsPattern, '\\1<ref id="../Protocols/\\2">\\2</ref>', fileContents)
			
			# Write the xml file
			f = open(filePath, "w")
			f.write(fileContents)			
			f.close()
			
def convertToHTML(filePath, outputDirectory):
	global verbose
	
	# Get info about the object
	objectName = nameForFile(filePath)
	objectType = typeForFile(filePath)
	
	if verbose:
		print "Converting " + objectName + ".html"
	
	if objectType == "class":
		outputDirectory = os.path.join(outputDirectory, "Classes")
	elif objectType == "category":
		outputDirectory = os.path.join(outputDirectory, "Categories")
	elif objectType == "protocol":
		outputDirectory = os.path.join(outputDirectory, "Protocols")
	_mkdir(outputDirectory)
	
	outputPath = os.path.join(outputDirectory, objectName + ".html")
	
	stylesheetPath = sys.path[0] + '/object2html.xslt'
	os.system("xsltproc -o \"%s\" \"%s\" \"%s\"" % (outputPath, stylesheetPath, filePath))

def convertIndexToHTML(filePath, outputDirectory):
	# Create the index html file
	stylesheetPath = sys.path[0] + '/index2html.xslt'
	outputPath = outputDirectory + '/index.html'
	os.system("xsltproc -o \"%s\" \"%s\" \"%s\"" % (outputPath, stylesheetPath, filePath))

def insertProjectName(directory, projectName):
	for (path, dirs, files) in os.walk(directory):
		for fileName in files:
			filePath = os.path.join(path, fileName)
			
			# Replace Project with projectName
			f = open(filePath, "r")
			text = f.read()
			f.close()
			f = open(filePath, "w")
			f.write(text.replace("##PROJECT##", projectName))
			f.close()

def main(argv=None):
	if argv is None:
		argv = sys.argv
		
	global verbose
		
	# Parse command line options
	optionParser = OptionParser(version="%prog 2.1")
	optionParser.add_option("-i", "--input", type="string", dest="inputDirectory", default=os.getcwd(), help="The directory containing Doxygen's XML output. Default is the current directory")
	optionParser.add_option("-o", "--output", type="string", dest="outputDirectory", default=os.getcwd(), help="The directory to output the converted files to. Default is the current directory")
	optionParser.add_option("-n", "--name", type="string", dest="projectName", default="Untitled", help="The name of the project")
	optionParser.add_option("-x", "--xml", action="store_false", dest="makeHTML", default="True", help="Only generate XML. If this flag is not set, both XML and HTML will be generated")
	optionParser.add_option("-v", "--verbose", action="store_true", dest="verbose", default="False", help="Show detailed information")
	(options, args) = optionParser.parse_args(argv[1:])

	verbose = options.verbose

	if verbose:
		print "Checking arguments"
		
	# Check the arguments
	if not os.path.exists(options.inputDirectory):
		print >>sys.stderr, "Error: Input path does not exist: %s" % (options.inputDirectory)
		optionParser.print_help()
		return errno.ENOENT
	elif not os.path.isdir(options.inputDirectory):
		print >>sys.stderr, "Error: Input path is not a directory: %s" % (options.inputDirectory)
		optionParser.print_help()
		return errno.ENOTDIR
	if os.path.exists(options.outputDirectory) and not os.path.isdir(options.outputDirectory):
		print >>sys.stderr, "Error: Output path is not a directory: %s" % (options.outputDirectory)
		return errno.ENOTDIR
	else:
		_mkdir(options.outputDirectory)
		
	# Set the xml output directory
	xmlOutputDirectory = os.path.join(options.outputDirectory, "xml")
		
	# Clean up the XML files
	if verbose:
		print "Cleaning XML files:"
	
	for fileName in os.listdir(options.inputDirectory):
		if fnmatch.fnmatch(fileName, "interface_*.xml") or fnmatch.fnmatch(fileName, "protocol_*.xml"):
			filePath = os.path.join(options.inputDirectory, fileName)
			cleanXML(filePath, xmlOutputDirectory)

	# Create the index file
	if verbose:
		print "Creating index.xml"
	indexPath = createIndexXML(xmlOutputDirectory)
	
	# Establish inter-file links
	if verbose:
		print "Establishing links:"
	linkify(xmlOutputDirectory)
	
	# Convert to HTML
	if options.makeHTML:
		if verbose:
			print "Converting to HTML:"
		htmlOutputDirectory = os.path.join(options.outputDirectory, "html")
		if (os.path.exists(os.path.join(xmlOutputDirectory, "Classes"))):
			for fileName in os.listdir(os.path.join(xmlOutputDirectory, "Classes")):
				filePath = os.path.join(xmlOutputDirectory, "Classes", fileName)
				convertToHTML(filePath, htmlOutputDirectory)
		if (os.path.exists(os.path.join(xmlOutputDirectory, "Categories"))):
			for fileName in os.listdir(os.path.join(xmlOutputDirectory, "Categories")):
				filePath = os.path.join(xmlOutputDirectory, "Categories", fileName)
				convertToHTML(filePath, htmlOutputDirectory)
		if (os.path.exists(os.path.join(xmlOutputDirectory, "Protocols"))):
			for fileName in os.listdir(os.path.join(xmlOutputDirectory, "Protocols")):
				filePath = os.path.join(xmlOutputDirectory, "Protocols", fileName)
				convertToHTML(filePath, htmlOutputDirectory)
		if verbose:
			print "Converting index.html"
		convertIndexToHTML(indexPath, htmlOutputDirectory)
		
		if verbose:
			print "Copying CSS stylesheets"
		# Copy the CSS files over to the new path
		cssPath = sys.path[0] + '/css'
		os.system("cp -R \"%s\" \"%s\"" % (cssPath, htmlOutputDirectory))
			
	# Set the project name where necessary
	if verbose:
		print "Setting project name"
	insertProjectName(xmlOutputDirectory, options.projectName)
	if options.makeHTML:
		insertProjectName(htmlOutputDirectory, options.projectName)
		
	return 0
	
if __name__ == '__main__':
	sys.exit(main())