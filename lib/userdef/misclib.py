import fnmatch
import os, sys, html, re
import pandas as pd

from tabulate import tabulate
from re import search
from pathlib import Path    # Resolve the windows / mac / linux path issue
import xml.etree.ElementTree as ET

import lib.userdef.settings as settings

try :
	from jinja2 import Environment, PackageLoader, FileSystemLoader, Template
except ImportError :
	sys.exit("[!] The Jinja2 module is not installed, please install it and try again")

# Current directory of the python file
parentPath = os.path.dirname(os.path.realpath(__file__))


def DiscoverFiles(codebase, sourcepath, mode):

    # mode '1' is for standard files discovery based on the filetypes/platform specified
    if mode == 1:
        ft = re.sub(r"\s+", "", GetRulesPathORFileTypes(codebase, "filetypes"))         # Get file types and use regex to remove any whitespaces in the string
        filetypes = list(ft.split(","))         # Convert the comman separated string to a list
        print("[*] Filetypes Selected: " + str(filetypes))
    elif mode == 2:
        print("Mode 2 Selected - Software Composition Analysis!!\n")
        filetypes = '*.*'

    matches = []
    fext = []

    # MOVE THIS TO GLOBAL INITIALIZATION FUNC
    # Logfile to the used to log discovered filepaths 
    parentPath = settings.root_dir                               # Daksh root directory 
    print("[*] DakshSCRA Directory Path: " + settings.root_dir)      
    
    f_filepaths = open(settings.discovered_Fpaths, "w")         # File ('discovered_Fpaths') for logging all discovered file paths

    print("[*] Identifying total files to be scanned!")
    linescount = 0
    filename = None     # To be removed. Temporarily added to fix - "local variable referenced before assignment" error
    # Reccursive Traversal of Directories and Files
    for root, dirnames, filenames in os.walk(sourcepath):
        for extensions in filetypes:
            for filename in fnmatch.filter(filenames, extensions):
                matches.append(os.path.join(root, filename))
                filename = os.path.join(root, filename)
                f_filepaths.write(filename + "\n")  # Log discovered file paths
                linescount += 1
                

        fext.append(GetFileExtention(filename))
    f_filepaths.close()
    
    print("[*] Total files to be scanned: " + str(linescount) + "\n")
    fext = list(dict.fromkeys(filter(None, fext)))      # filter is used to remove empty item that gets added due to 'filename = None' above
    print("[*] File Extentions Identified: " + str(fext) + "\n")

    #cleanfilepaths(settings.discovered_Fpaths)

    return settings.discovered_Fpaths

# Discovered files extentions and count of each type
def GetFileExtention(fpath):
    extention = Path(str(fpath)).suffix

    return extention


# Remove all files in the temp dir
def DirCleanup(dirname):
    dir = Path(parentPath + "/../../" + dirname)
    if os.path.exists(dir):
        for the_file in os.listdir(dir):
            file_path = os.path.join(dir, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
    else:  # Force create output directory if it doesn't exist
        os.makedirs(dir)
    return



def GenHtmlReport():

    env = Environment( loader = FileSystemLoader(settings.htmltemplates_dir))
    template = env.get_template('template.html')

    print("\n[*] HTML Report Path : "+ str(settings.htmlreport_Fpath))

    print("[*] Areas of Interest (Patterns Identified): " + str(settings.outputAoI))
    
    print("[*] Source Files Path: " + str(settings.discovered_Fpaths))
    
    with open(settings.htmlreport_Fpath, 'w') as fh:
        contents = open(settings.outputAoI, "r")        # Input file 'settings.outputAoI' for generating HTML report
        
        for lines in contents.readlines():
            encodedString = html.escape(lines) # HTML Encoding is used to avoid execution of any malicious script that are part of the code snippet
            if search("Keyword Searched", encodedString):
                fh.write(template.render(keyword=encodedString))
            elif search("Source File", encodedString):
                encodedString = encodedString.strip("S")
                fh.write(template.render(fpath=encodedString))
            else:
                fh.write(template.render(snippet="&nbsp;&nbsp;" + encodedString))

    return



def GetSourceFilePath(project_dir, source_file):
    pattern = re.compile(project_dir + '.+')

    source_filepath = ''
    try:
        source_filepath = pattern.search(source_file)[0]
    except TypeError as e:      # The "'NoneType' object is not subscriptable" error occurs on windows. 
        # print(e)              # This error handling is meant to getaround the error caused on windows os
        source_filepath = source_file

    return source_filepath


# Function to replace absolute file paths with project file paths 
# by stripping out the path before the project directory
def CleanFilePaths(filepaths_source):
    
    target_dir = os.path.dirname(filepaths_source)
    target_dir = os.path.join(target_dir, '')
    source_file = target_dir + "filepaths.log"
    dest_file = target_dir + "filepaths.txt"


    h_sf = open(source_file, "r")
    h_df = open(dest_file, "w")

    for eachfilepath in h_sf:  # Read each line (file path) in the file
        filepath = eachfilepath.rstrip()  # strip out '\r' or '\n' from the file paths
        h_df.write(GetSourceFilePath(settings.sourcedir, filepath) + "\n")

    h_sf.close()
    h_df.close()

    #os.unlink(source_file)

# Function to obtain rules file path of a particular platform or the supported filetypes 
def GetRulesPathORFileTypes(platform, option):

    while option not in ["filetypes", "rules"]:
        print("Error (GetRulesPathORFileTypes): Invalid option supplied. Allowed options are [rules or filetypes]!")
        sys.exit()

    retValue = ''

    # Load filetypes XML config file
    xmltree = ET.parse(settings.rulesConfig)
    rule = xmltree.getroot()

    if option == "filetypes":
        for r in rule:
            if r.find("platform").text == platform:
                retValue = r.find("ftypes").text        # Return file types
                break
    elif option == "rules":
        for r in rule:
            if r.find("platform").text == platform:
                retValue = r.find("path").text          # Return rule file path
                break

    else:
        print("\nError: Invalid value of rulesORfiletypes!")    

    return retValue

# List/Show rules or supported filetypes or both
def ListRulesFiletypes(option):
    retValue = 0
    dict = {}

    # Load filetypes XML config file
    xmltree = ET.parse(settings.rulesConfig)
    rule = xmltree.getroot()


    if option == 'R':
        print("List of all available rules")
        for r in rule:
            print("\t" + r.find("platform").text)        # Return supported platforms
            retValue = 1

    elif option == 'RF':
        print("List both available rules and filetypes")
        for r in rule:
            #print(tabulate([["Platform","File Types"],[r.find("platform").text, r.find("ftypes").text]], headers="firstrow", tablefmt="psql"))
            dict[r.find("platform").text] = r.find("ftypes").text
            retValue = 1
    
        df = pd.DataFrame.from_dict(dict, orient='index')
        print("\n" + tabulate(df, headers=["Platform", "File Types"], tablefmt="grid", maxcolwidths=[None, 40]) + "\n")

    else:
        print("Invalid option")
        retValue = 0


    return retValue
