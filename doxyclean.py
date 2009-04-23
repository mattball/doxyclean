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
	xmlDoc = minidom.parse(filePath)
	return xmlDoc.getElementsByTagName("name")[0].firstChild.data

def typeForFile(filePath):
	xmlDoc = minidom.parse(filePath)
	return xmlDoc.getElementsByTagName("object")[0].attributes["kind"].value

def cleanXML(filePath, outputDirectory):
	if not fileIsDocumented(filePath):
		return
		
	_mkdir(outputDirectory)
	
	# Perform the XSL Transform
	fileName = os.path.split(filePath)[1]
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
	
	# Get each file
	for (path, dirs, files) in os.walk(directory):
		for fileName in files:
			# Skip the index
			if fileName == "index.xml":
				continue
			
			filePath = os.path.join(path, fileName)
			
			f = open(filePath, "r")
			fileContents = f.read()
			f.close()
			
			# Link to all Foundation and AppKit documentation
			# We don't want links in the name or file
			foundationPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(NSAppleEventDescriptor|NSNetService|NSAppleEventManager|NSNetServiceBrowser|NSAppleScript|NSNotification|NSArchiver|NSNotificationCenter|NSArray|NSNotificationQueue|NSAssertionHandler|NSNull|NSAttributedString|NSNumber|NSAutoreleasePool|NSNumberFormatter|NSBundle|NSObject|NSCachedURLResponse|NSOutputStream|NSCalendarDate|NSPipe|NSCharacterSet|NSPort|NSClassDescription|NSPortCoder|NSCloneCommand|NSPortMessage|NSCloseCommand|NSPortNameServer|NSCoder|NSPositionalSpecifier|NSConditionLock|NSProcessInfo|NSConnection|NSPropertyListSerialization|NSCountCommand|NSPropertySpecifier|NSCountedSet|NSProtocolChecker|NSCreateCommand|NSProxy|NSData|NSQuitCommand|NSDate|NSRandomSpecifier|NSDateFormatter|NSRangeSpecifier|NSDecimalNumber|NSRecursiveLock|NSDecimalNumberHandler|NSRelativeSpecifier|NSDeleteCommand|NSRunLoop|NSDeserializer|NSScanner|NSDictionary|NSScriptClassDescription|NSDirectoryEnumerator|NSScriptCoercionHandler|NSDistantObject|NSScriptCommand|NSDistantObjectRequest|NSScriptCommandDescription|NSDistributedLock|NSScriptExecutionContext|NSDistributedNotificationCenter|NSScriptObjectSpecifier|NSEnumerator|NSScriptSuiteRegistry|NSError|NSScriptWhoseTest|NSException|NSSerializer|NSExistsCommand|NSSet|NSFileHandle|NSSetCommand|NSFileManager|NSSocketPort|NSFormatter|NSSocketPortNameServer|NSGetCommand|NSSortDescriptor|NSHost|NSSpecifierTest|NSHTTPCookie|NSSpellServer|NSHTTPCookieStorage|NSStream|NSHTTPURLResponse|NSString|NSIndexSet|NSTask|NSIndexSpecifier|NSThread|NSInputStream|NSTimer|NSInvocation|NSTimeZone|NSKeyedArchiver|NSUnarchiver|NSKeyedUnarchiver|NSUndoManager|NSLock|NSUniqueIDSpecifier|NSLogicalTest|NSURL|NSMachBootstrapServer|NSURLAuthenticationChallenge|NSMachPort|NSURLCache|NSMessagePort|NSURLConnection|NSMessagePortNameServer|NSURLCredential|NSMethodSignature|NSURLCredentialStorage|NSMiddleSpecifier|NSURLDownload|NSMoveCommand|NSURLHandle|NSMutableArray|NSURLProtectionSpace|NSMutableAttributedString|NSURLProtocol|NSMutableCharacterSet|NSURLRequest|NSMutableData|NSURLResponse|NSMutableDictionary|NSUserDefaults|NSMutableIndexSet|NSValue|NSMutableSet|NSValueTransformer|NSMutableString|NSWhoseSpecifier|NSMutableURLRequest|NSXMLParser|NSNameSpecifier)"
			fileContents = re.sub(foundationPattern, '\\1<ref id="http://developer.apple.com/documentation/Cocoa/Reference/Foundation/Classes/\\2_Class/index">\\2</ref>', fileContents)
			
			appKitPattern = "(?<!\\<name\\>|\\<file\\>)([^\\<|^\\>]*)(NSActionCell|NSOpenGLPixelFormat|NSAffineTransform|NSOpenGLView|NSAlert|NSOpenPanel|NSAppleScript Additions|NSOutlineView|NSApplication|NSPageLayout|NSArrayController|NSPanel|NSATSTypesetter|NSParagraphStyle|NSPasteboard|NSBezierPath|NSPDFImageRep|NSBitmapImageRep|NSPICTImageRep|NSBox|NSPopUpButton|NSBrowser|NSPopUpButtonCell|NSBrowserCell|NSPrinter|NSPrintInfo|NSButton|NSPrintOperation|NSButtonCell|NSPrintPanel|NSCachedImageRep|NSProgressIndicator|NSCell|NSQuickDrawView|NSClipView|NSResponder|NSRulerMarker|NSColor|NSRulerView|NSColorList|NSSavePanel|NSColorPanel|NSScreen|NSColorPicker|NSScroller|NSColorWell|NSScrollView|NSComboBox|NSSearchField|NSComboBoxCell|NSSearchFieldCell|NSControl|NSSecureTextField|NSController|NSSecureTextFieldCell|NSCursor|NSSegmentedCell|NSCustomImageRep|NSSegmentedControl|NSDocument|NSShadow|NSDocumentController|NSSimpleHorizontalTypesetter|NSDrawer|NSSlider|NSEPSImageRep|NSSliderCell|NSEvent|NSSound|NSFileWrapper|NSSpeechRecognizer|NSFont|NSSpeechSynthesizer|NSFontDescriptor|NSSpellChecker|NSFontManager|NSSplitView|NSFontPanel|NSStatusBar|NSForm|NSStatusItem|NSFormCell|NSStepper|NSGlyphGenerator|NSStepperCell|NSGlyphInfo|NSGraphicsContext|NSTableColumn|NSHelpManager|NSTableHeaderCell|NSImage|NSTableHeaderView|NSImageCell|NSTableView|NSImageRep|NSTabView|NSImageView|NSTabViewItem|NSInputManager|NSText|NSInputServer|NSTextAttachment|NSLayoutManager|NSTextAttachmentCell|NSMatrix|NSTextContainer|NSMenu|NSTextField|NSMenuItem|NSTextFieldCell|NSMenuItemCell|NSTextStorage|NSMenuView|NSTextTab|NSMovie|NSTextView|NSMovieView|NSToolbar|NSToolbarItem|NSMutableParagraphStyle|NSTypesetter|NSNib|NSNibConnector|NSUserDefaultsController|NSNibControlConnector|NSView|NSNibOutletConnector|NSWindow|NSObjectController|NSWindowController|NSOpenGLContext|NSWorkspace|NSOpenGLPixelBuffer)"
			fileContents = re.sub(appKitPattern, '\\1<ref id="http://developer.apple.com/documentation/Cocoa/Reference/ApplicationKit/Classes/\\2_Class/index">\\2</ref>', fileContents)
			
			# Get all the paragraphs in the file
			fileXML = minidom.parseString(fileContents)
			fileType = typeForFile(filePath)
			refNodes = fileXML.getElementsByTagName("ref")
			
			# Replace all instances of the current object with a <ref>
			for node in refNodes:
				refName = node.firstChild.data
				
				# Search for the corresponding node in the index
				for documentedObject in documentedObjects:
					# We need to get rid of whitespace
					# (It's a "feature" of minidom)
					objectName = documentedObject.firstChild.data.replace("\n", "").replace("\t", "")
					
					if objectName == refName:
						objectType = documentedObject.parentNode.attributes["kind"].value
						objectPath = ""
						
						# Determine the proper directory
						if fileType != objectType:
							if objectType == "class":
								objectPath += "../Classes"
							elif objectType == "category":
								objectPath += "../Categories"
							elif objectType == "protocol":
								objectPath += "../Protocols"
								
						objectPath = os.path.join(objectPath, refName)
						node.setAttribute("id", objectPath)
						break
				
				# Check if the ref has a "id" attribute
				# If not, remove the <ref>
				if not node.hasAttribute("id"):
					refText = fileXML.createTextNode(refName)
					node.parentNode.replaceChild(refText, node)
					
			# Write the xml file
			f = open(filePath, "w")
			f.write(fileXML.toxml())			
			f.close()
			
def convertToHTML(filePath, outputDirectory):
	# Get info about the object
	objectName = nameForFile(filePath)
	objectType = typeForFile(filePath)
	
	if objectType == "class":
		outputDirectory = os.path.join(outputDirectory, "Classes")
	elif objectType == "category":
		outputDirectory = os.path.join(outputDirectory, "Categories")
	elif objectType == "protocol":
		outputDirectory = os.path.join(outputDirectory, "Protocols")
	_mkdir(outputDirectory)
	
	outputPath = os.path.join(outputDirectory, objectName + ".html")
	
	stylesheetPath = sys.path[0] + '/object2xhtml.xslt'
	os.system("xsltproc -o \"%s\" \"%s\" \"%s\"" % (outputPath, stylesheetPath, filePath))

def convertIndexToHTML(filePath, outputDirectory):
	# Create the index html file
	stylesheetPath = sys.path[0] + '/index2xhtml.xslt'
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
		
	# Parse command line options
	optionParser = OptionParser(version="%prog 1.0")
	optionParser.add_option("-i", "--input", type="string", dest="inputDirectory", default=os.getcwd(), help="The directory containing Doxygen's XML output. Default is the current directory")
	optionParser.add_option("-o", "--output", type="string", dest="outputDirectory", default=os.getcwd(), help="The directory to output the converted files to. Default is the current directory")
	optionParser.add_option("-n", "--name", type="string", dest="projectName", default="Untitled", help="The name of the project")
	optionParser.add_option("-x", "--xml", action="store_false", dest="makeHTML", default="True", help="Only generate XML. If this flag is not set, both XML and HTML will be generated")
	(options, args) = optionParser.parse_args(argv[1:])

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
	for fileName in os.listdir(options.inputDirectory):
		if fnmatch.fnmatch(fileName, "interface_*.xml") or fnmatch.fnmatch(fileName, "protocol_*.xml"):
			filePath = os.path.join(options.inputDirectory, fileName)
			cleanXML(filePath, xmlOutputDirectory)

	# Create the index file
	indexPath = createIndexXML(xmlOutputDirectory)
	
	# Establish inter-file links
	linkify(xmlOutputDirectory)
	
	# Convert to HTML
	if options.makeHTML:
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
		convertIndexToHTML(indexPath, htmlOutputDirectory)
		
		# Copy the CSS files over to the new path
		cssPath = sys.path[0] + '/css'
		os.system("cp -R \"%s\" \"%s\"" % (cssPath, htmlOutputDirectory))
			
	# Set the project name where necessary
	insertProjectName(xmlOutputDirectory, options.projectName)
	if options.makeHTML:
		insertProjectName(htmlOutputDirectory, options.projectName)
	
if __name__ == '__main__':
	sys.exit(main())