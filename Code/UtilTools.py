import ConfigParser
import os.path
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
import operator
from bs4 import BeautifulSoup
import re

# path: path to the file that contains option names
# outDir: dir to output op descriptions
def SplitOpByName(path,outDir):
	with open(path,'r') as opList:
		 opNames = opList.read().decode('UTF-8').lower().split('\n')
		 for opName in opNames:
			#print opName
			opDesc = re.split('[.-_]', opName)
			#print opDesc
			oFile=outDir+'/'+opName
			with open(oFile,'w') as fout:
				fout.write('%s' % ' '.join(opDesc))

# path: path to the file that contains option names
# outDir: dir to output op descriptions
def SplitOpByCamelName(path,outDir):
	with open(path,'r') as opList:
		 opNames = opList.read().decode('UTF-8').split('\n')
		 for opName in opNames:
			#print opName
			opDesc = re.sub('(?!^)([A-Z][a-z]+)', r' \1', opName).split()
			#print opDesc
			oFile=outDir+'/'+opName
			with open(oFile,'w') as fout:
				fout.write('%s' % ' '.join(opDesc))


def GetTabFileHeader(conf,sec):
	hList = GetOpsFromSec(conf,sec)
	firstLine = '\t'.join(hList)
	total = int(GetNumOfOps(conf,sec))
	secondLine = 'discrete\t'*total
	thirdLine = '\t'*(total-1)+'class'		
	return firstLine, secondLine, thirdLine

def GetNumOfOps(confFile,secName):
	config = ConfigParser.RawConfigParser()
	config.read(confFile)
	#print config.sections()
	return len(config.options(secName))


def GetOpsFromSec(conf,sec):
	config = ConfigParser.RawConfigParser()
	config.read(conf)
	return config.options(sec)

def GetConfOpList(path):
	with open(path,'r') as confFile:
		fullConfigOptions = confFile.read().decode('UTF-8').lower().split('\n')
	return fullConfigOptions

def GetOpVal(confFile,secName,optionName):
	config = ConfigParser.RawConfigParser()
	config.read(confFile)
	return config.get(secName,optionName)	

def GetCsvOpVals(confFile,secName,optionName):	
	config = ConfigParser.RawConfigParser()
	config.read(confFile)
	rawCsvVal = config.get(secName,optionName)	
	# Remove trailing chars, newline, and spaces
	csvVal = rawCsvVal.strip().replace('\n','')
	return csvVal.split(',')

# gtPath: ground truth file path
# evaPath: evaluating method file path
# item: the item name to be evaluated
def IsItemMatch(gtPath, sec1, evaPath, sec2, item):
	gt = ConfigParser.RawConfigParser()
	# Groundtruth file path
	gt.read(gtPath)
	gtVal = gt.get(sec1, item)

	# Evaluation method
	eva = ConfigParser.RawConfigParser()
	eva.read(evaPath)
	evaVal = eva.get(sec2, item)

	if gtVal.lower() == evaVal.lower(): 
		return 1
	else:
		return 0


def PrintPtnDictCount(ptnDict):
	for k in ptnDict:
		print('category:{}'.format(k))
		v = ptnDict[k]
		for k1 in v:
			v1 = v[k1]
			print('{}:{}'.format(k1,v1))


def GenPtnStat(ptnDict,oFile):
	with open(oFile,'w') as fout:
		for k in ptnDict:
			fout.write('category:' + k + '\n')
			v = ptnDict[k]
			# Sort dictionary
			sortedV = sorted(v.items(),key=operator.itemgetter(1),reverse=True)
			for k1,v1 in sortedV:
				fout.write('%s:%d,' % (k1,v1))
			fout.write('\n')
	print 'Pattern stat saved to %s' % oFile	


def AppendToFile(path,msg):
	with open(path,'a') as fout:
		fout.write(msg+'\n')

def WriteToFile(path,sigDict):
	with open(path, 'w') as fout:
		# Print patterns results
		for key in sigDict:
			val = sigDict[key]
			# Filter out less frequent patterns
			if val > 0:
				# print key + ':' + str(val)
				for i in range(val):
					#	print key
					fout.write(key+'\n')
	
	print 'Patterns saved to %s' % (path)

def WriteToTabFile(path,header,sigDict):
	with open(path, 'w') as fout:
		# Write header
		fout.write(header+'\n')
		# Print patterns results
		for key in sigDict:
			val = sigDict[key]
			# Filter out less frequent patterns
			if val > 0:
				# print key + ':' + str(val)
				for i in range(val):
					#	print key
					fout.write(key+'\n')
	
	print 'Patterns saved to %s' % (path)


def ReduceOpList(oriOpList, minLength, newOpList):
	if os.path.exists(newOpList):
		print '%s exists, please check!' % newOpList
		sys.exit(0)

	print 'reduce op list'
	print 'option name min length: %s' % minLength

	with open(oriOpList,'r') as f, open(newOpList, 'w') as fout:
		for line in f:
			line = line.rstrip()
			if len(line) > int(minLength):
				fout.write(line + '\n')

def getApacheOpDoc(url, outDir):
	r = requests.get(url)
	soup = BeautifulSoup(r.text, 'html.parser')
	soup.encode("utf-8")
	opSecs = soup.find_all('div', class_='directive-section')
	#print cls[0]
	for opSec in opSecs:
		fileName = opSec.find_next('a').get_text()
		#print fileName
		# Replace < and > in the directive name
		fileName = fileName.replace('<','').replace('>','')
		outFilePath = outDir + '/' + fileName
		if os.path.isfile(outFilePath):
			print 'Found file: ' + outFilePath
			continue
		else:
			print 'Processing" ' + outFilePath

		with open(outFilePath, 'w') as fout:
			#body = opSec.find_next('p').get_text().strip()
			# Calculate limit
			firstP = opSec.find_next('p')
			fout.write(firstP.get_text().strip())

			# Find other paragraphs
			otherPs = firstP.find_next_siblings('p')
			for p in otherPs:
				fout.write(p.get_text().strip())
	return


def getMySqlOpDoc(url, outDir):
	r = requests.get(url)
	soup = BeautifulSoup(r.text, 'html.parser')
	soup.encode("utf-8")
	#print cls[0]
	liTags = soup.find_all('li', class_='listitem')
	 
	for liTag in liTags:
		fileName = liTag.find_next('code', class_='literal').get_text()
		# fileName = liTag.find_next('code', class_='option').get_text() # for server option page
		if '(' in fileName:
			continue

		# Skip if fileName is empty
		if not fileName:
			continue

		fileName = re.sub(r'\[.+\]','',fileName)
		#print fileName
		# Replace < and > in the directive name
		fileName = fileName.replace('<','').replace('>','')
		outFilePath = outDir + '/' + fileName
		if os.path.isfile(outFilePath):
			print 'Found file: ' + outFilePath
			continue
		else:
			print 'Processing" ' + outFilePath

		with open(outFilePath, 'w') as fout:
			#body = opSec.find_next('p').get_text().strip()
			# Title
			divTag = liTag.find_next('p')
			if divTag is not None:
				paraTag = divTag.findNextSibling('p')
				while paraTag:
					fout.write(paraTag.get_text().strip())
					paraTag = paraTag.findNextSibling('p')

	return

def getFfOpDoc(url, outDir):
	r = requests.get(url)
	soup = BeautifulSoup(r.text, 'html.parser')
	soup.encode("utf-8")
	opSecs = soup.find_all('div',class_='editsection')
	#print cls[0]
	for opSec in opSecs:
		table = opSec.find_next('table')
		headerTr = table.find_next('tr')
		trs = headerTr.find_next_siblings()
		for tr in trs:
			td1 = tr.find_next('td')
			fileName = td1.get_text().strip().replace(' ','')
			fileName = re.sub(r'\(.+\)', '', fileName)
			#print fileName
			outFilePath = outDir + '/' + fileName
			if os.path.isfile(outFilePath):
				print 'Found file: ' + outFilePath
				continue
			else:
				print 'Processing" ' + outFilePath

			with open(outFilePath, 'w') as fout:
			# TYPE
				td2 = td1.find_next('td')
				tdDesc = td2.find_next('td')
				fout.write(tdDesc.get_text().strip().replace('\n',''))

	return

def UpdateKeyCount(_dict,_key):
	if _key in _dict.keys():
		_dict[str(_key)] += 1
	else:
		_dict[str(_key)] = 1		

def InitFile(oPath):
 print 'Init %s' % oPath
 with open(oPath,'w') as fout:
	 fout.write('')
