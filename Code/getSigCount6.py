# V6
import getFreq6
import sys, getopt
import os
import re
import glob
import UtilTools

ops, otherOps = getopt.getopt(sys.argv[1:],'d:o:c:h')
#print ops
conf = None
inFileName = None
outFile = None
dirRoot = './'
for op,val in ops:
	if op == '-d':
		dirRoot = val
	elif op == '-h':
		print 'Usage: python ' + sys.argv[0] + ' -d ./CorporaDir/ -c apache.ini -o outPtn 2>debug.log'
		sys.exit(0)
	elif op == '-o':
		outFile = val
	elif op == '-c':
		conf = val
	else:
		print 'Unknown option: ' + op

if outFile == None:
	sys.exit('Please specify directory info with -o')
if conf == None:
	sys.exit('Please specify configuration file with -c')

# Signature dictionary
sigDict = {}
# Pattern component stats
ptnStatDict = {}
# Abstract pattern dict
absSigDict = {}
# Clean up meta data file
metaPath = outFile+'.meta'
UtilTools.InitFile(metaPath)
# Loop through bug reports to get a test signature
files = [f for f in os.listdir(dirRoot) if re.match(r'.*\.txt',f)]
for f in files:
	sigId,absSigId = getFreq6.GetSignature(dirRoot,f,conf,ptnStatDict,metaPath)
	if sigId in sigDict.keys():
		sigDict[str(sigId)] += 1
	else:
		sigDict[str(sigId)] = 1		
	UtilTools.UpdateKeyCount(absSigDict,absSigId)

# Output pattern stats
#UtilTools.PrintPtnDictCount(ptnStatDict)
UtilTools.GenPtnStat(ptnStatDict,outFile+'.stat')

UtilTools.WriteToFile(outFile+'.basket',sigDict)
# Get header
hList = UtilTools.GetTabFileHeader(conf,'PTN')
headers = '\n'.join(hList)
UtilTools.WriteToTabFile(outFile+'Abs.tab',headers,absSigDict)
