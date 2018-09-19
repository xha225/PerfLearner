# V0.5
# Add functions to improve "keyword matching" accuracy 
# Add resource usage trend
# Usage cosine similarity to infer configuration options

import nltk, re, pprint
from nltk.text import Text
from nltk.corpus import gutenberg
from nltk.corpus import PlaintextCorpusReader
from nltk.corpus import stopwords
import operator
import os
import string
import sys, getopt
reload(sys)
sys.setdefaultencoding('utf8')
import UtilTools
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
from nltk import pos_tag
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter 
import codecs

def WriteToStdErr(errStr):
	sys.stderr.write(errStr + '\n')

def ReportUnigramFreq(fdist,conf):
	ACTIONS = UtilTools.GetCsvOpVals(conf,'PTN','ACTIONS')

	actionDict = {}
	for actionName in ACTIONS:
		actionName = actionName.lower()
		actionDict[actionName] = fdist[actionName]
	return actionDict

def ReportBigramFreq(keywords,bigramFdist,actionDict):
	for key,val in keywords:	
		actionName = key+' '+val
		for x in bigramFdist:
			if x == (key,val):
				actionDict[actionName] = bigramFdist[x]
	return

def GetFileDetail(sents,bugId,oPath):
	for sent in sents:
		#print sent
		#m = re.search(r'file.*?(\d|\.)+.*?[mg]{1}b?.*?file.*?',sent,flags=re.IGNORECASE)
		m = re.search(r'(file)+s?.*?(\d|\.)+[mg]{1}b?.*?',sent,flags=re.IGNORECASE)
		if m != None: 
			UtilTools.AppendToFile(oPath,'%s,file size: %s' % (bugId,m.group(0)))
			#print 'File size: %s' % (m.group(0))

		m = re.search(r'.*?(\d|\.)+[mg]{1}b?.*?(file)+s?',sent,flags=re.IGNORECASE)
		if m != None: 
			UtilTools.AppendToFile(oPath,'%s,file size: %s' % (bugId,m.group(0)))
			#print 'File size: %s' % (m.group(0))

# name: name of the file type: e.g., cgi, html
# sent: the sentence
def ApplyFileTypeRule(fTypes,sent):
	for fType in fTypes:
		if fType.lower() == 'cgi':
			sent = re.sub(r'http.*cgi.*\b','',sent)
		elif fType.lower() == 'html':
			sent = re.sub(r'http:.*apache.*\.html.*\b','',sent)

	return sent

def GetInputFile(sents,conf):
	# Get distribution from sentences
	fileTypes = UtilTools.GetCsvOpVals(conf,'PTN','INPUTS')
	fileDist = {}
	for sent in sents:
		sent = ApplyFileTypeRule(fileTypes,sent)
		for key in fileTypes:
			if key in sent:
				if key in fileDist:
					fileDist[key] += 1
				else:
					fileDist[key] = 1
				#fileDic.update({fType: 1})

	sortedFileDict = sorted(fileDist.items(),key=operator.itemgetter(1),reverse=True)	
	return sortedFileDict

def GetOptions(opPath):
	with codecs.open(opPath,'r',encoding='utf8') as confFile:
		ops = confFile.readlines()

	return [op.lower().rstrip('\n')	for op in ops]
		
def GetOptionsFreq(fdist,opListPath):
	# Get option distribution and value range
	# Python 2 does not support open file with encoding=UTF-8
	with open(opListPath,'r') as confFile:
		fullConfigOptions = GetOptions(opListPath)

	optionDict = {}
	fdistList = list(fdist)
	#print fdistList
	i = 0
	for option in fullConfigOptions:
		i += 1
		if option in fdistList:
			optionDict[option] = i #fdist[option]

	sortedOptionDict = sorted(optionDict.items(),key=operator.itemgetter(1),reverse=True)
	return sortedOptionDict

def PrintTestTemplate():
	print 'To be implemented'
	return

def GetSymptoms (fdist,conf):
	sympKeywords = UtilTools.GetCsvOpVals(conf,'PTN','SYMP')
	sympDic = {}
	for symp in sympKeywords:
		sympDic[symp.lower()] = fdist[symp.lower()]

	sortedSympDic = sorted(sympDic.items(),key=operator.itemgetter(1),reverse=True)
	return sortedSympDic

# Add x to the name value pair
# dict is dictionary, if the key is not found, init value to 1
def DictPlusX(dict,key,x):
	if key in dict.keys():
		dict[key] += x
	else: 
		dict[key] = x
	
	return dict

# modPtn: module pattern, defined in the configuration file (.ini)
# sents: sentences
def GetModule(modPtn,sents):
	modList = []
	for sent in sents:
		# Make sure to have 'r' in front of the string
		loadRegEx = r''+re.escape(modPtn)+r'.*?\b'
		#print ptn
		mods = re.findall(loadRegEx,sent,flags=re.IGNORECASE)
		modList.extend(mods)

	modCounter = Counter(modList) 
	return sorted(modCounter.items(),key=operator.itemgetter(1),reverse=True)

# bugId: bug report name
# oPath: metadata file path
def SaveThroughput(sents,bugId,oPath):
	for sent in sents:
		# Pattern to match: 197 requests/sec - 28.6 kB/second - 148 B/reques
		m = re.findall(r'[\d|\.]+\s[a-z]+\s?/\s?[a-z]+',sent,re.IGNORECASE)
		if m:
			UtilTools.AppendToFile(oPath,'%s,throughput: %s' % (bugId,m))
# 
def GetLoad(sents,conf):
	# Get RegEx from configuration 
	loadRegEx = UtilTools.GetCsvOpVals(conf,'PTN','LOAD')
	#	print loadRegEx
	loadDict = {}
	#text.findall(r'<ab><-><\w>')
	for sent in sents:
		for regEx in loadRegEx:
			# Search RegEx in the sentence
			matchedPattern = re.findall(r'\b'+regEx+r'\b',sent)
			#matchedPattern = re.findall(r'ab \-\w',sent)
			if matchedPattern:
				x = len(matchedPattern)
				DictPlusX(loadDict,regEx,x)	
				#print matchedPattern
	return sorted(loadDict.items(),key=operator.itemgetter(1),reverse=True)

def tokenize(text):
	tokens = nltk.word_tokenize(text)
	# TODO: plugin your stemmer	
	return tokens

def GetTfidfVector(tokenDict,tfidf):
	tfs = tfidf.fit_transform(tokenDict.values())
	#featureNames = tfidf.get_feature_names()	
	# tfs.nonzero()[1] returns the feature index
	#for col in tfs.nonzero()[1]:
	#	print featureNames[col]
	return tfs

def GetOpNameFromInd(selectedInd,opDict):
	#print 'Output selected op'
	#for ind in selectedInd:
		# NOTE: accessing dictionary by index is not guaranteed if the content changes
	#	print 'opt name: {}'.format(opDict.keys()[ind])
	return opDict.keys()[selectedInd[0]]

def GetOpNamesFromInds(selectedInd,opDict):	
	ops = []
	for ind in selectedInd:
		ops.append(opDict.keys()[ind])
	
	return ops

# Retrieve configuration value from text corpus
# bugId: bug report file name
# oPath: metadata output path
def GetOpVals(opDict,sents,bugId,oPath):
	for sent in sents:
		for key,val in	opDict.iteritems():
			if val > 0:
				m = re.search(re.escape(key)+r'\s\w+(?=\n)',sent,flags=re.IGNORECASE)	
				if m:
					UtilTools.AppendToFile(oPath, '%s, Op: %s, Matched: %s' % (bugId, key,m.group()))

def LoadConfigDoc(docPath):
	confDocDict = {}
	for root, dirs, files in os.walk(docPath):
		fInd = 0
		for f in files:	
			fInd += 1
			confPath = os.path.join(root,f)
			confDoc = open(confPath, 'r')
			# Load text with pre-processing
			text = confDoc.read().lower().translate(None, string.punctuation)
			# print text	
			confDocDict[f] = text
		
	return confDocDict

def LoadQueryFile(path):
	doc = open(path,'r')
	text = doc.read().lower().translate(None, string.punctuation)
	return text

# queryPath: file path to the query doc
# conf: path to the configuration file
# topX: top x selected configuration option
# reference: http://blog.christianperone.com/2013/09/machine-learning-cosine-similarity-for-vector-space-models-part-iii/
def GetInferredOp(queryPath,conf,topX):
	# Get option documentation description
	# docPath: dir path to the docs
	docPath = UtilTools.GetCsvOpVals(conf,'OTHERS','ConfDoc')
	confDocDict = LoadConfigDoc(docPath[0])
	# Get vector representation of document
	tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
	tfs = GetTfidfVector(confDocDict,tfidf)
	#queryStr = LoadQueryFile('/home/x/TestGen/DataMining/apache12757')
	queryStr = LoadQueryFile(queryPath)
	queryDoc = tfidf.transform([queryStr])
	# Get the one with the highest similarity score
	flatMat	= cosine_similarity(queryDoc,tfs).flatten()
	#indices = cosine_similarity(queryDoc,tfs).flatten().argsort()[:-3:-1]
	# Return top x
	indices = flatMat.argsort()[:-topX:-1]
	#firstOp = GetOpNameFromInd(indices,confDocDict)
	ops = GetOpNamesFromInds(indices,confDocDict)
	# print indices
	simScores = flatMat[indices[0:topX]]
	# print simScore
	return ops,simScores

# queryPath: file path to the query doc
# conf: path to the configuration file
# topX: top x selected configuration option
# reference: http://blog.christianperone.com/2013/09/machine-learning-cosine-similarity-for-vector-space-models-part-iii/
def GetInferredOpSplit(queryPath,conf,topX):
	# Get option documentation description
	# docPath: dir path to the docs
	docPath = UtilTools.GetCsvOpVals(conf,'OTHERS','ConfSplitDoc')
	confDocDict = LoadConfigDoc(docPath[0])
	# Get vector representation of document
	tfidf = TfidfVectorizer(tokenizer=tokenize, stop_words='english')
	tfs = GetTfidfVector(confDocDict,tfidf)
	#queryStr = LoadQueryFile('/home/x/TestGen/DataMining/apache12757')
	queryStr = LoadQueryFile(queryPath)
	queryDoc = tfidf.transform([queryStr])
	# Get the one with the highest similarity score
	flatMat	= cosine_similarity(queryDoc,tfs).flatten()
	#indices = cosine_similarity(queryDoc,tfs).flatten().argsort()[:-3:-1]
	# Return top x
	indices = flatMat.argsort()[:-topX:-1]
	#firstOp = GetOpNameFromInd(indices,confDocDict)
	ops = GetOpNamesFromInds(indices,confDocDict)
	# print indices
	simScores = flatMat[indices[0:topX]]
	# print simScore
	return ops,simScores


# Get noun phrase chunk
# res, resource name: CPU, memory
# bugId, bug file
# oPath, output path
def GetResLevel(res,sents,bugId,oPath):
	sents = [nltk.word_tokenize(sent) for sent in sents]
	# Get context: Part of Speech
	sents = [nltk.pos_tag(sent) for sent in sents]
	#print sents
	# Chunk grammar
	grammar = "NP: {<DT>?<JJ.*>+<NN.*>}"
	cp = nltk.RegexpParser(grammar)
	for sent in sents:
		if re.search(re.escape(res),str(sent),flags=re.IGNORECASE):
			result = cp.parse(sent)
			for subtree in result.subtrees():
				if (subtree.label() == 'NP' and re.search(re.escape(res),str(subtree),flags=re.IGNORECASE)):
					#print subtree
					# Match string: (NP excessive/JJ CPU/NNP)
					# RegEx: (?=/), look ahead, find '/' but do not include it 
					m = re.findall(r'\s.*?(?=/)',str(subtree),flags=re.IGNORECASE)
					UtilTools.AppendToFile(oPath,'%s,res-level: %s' % (bugId,' '.join(m)))
	
# Get the resource trend: e.g., CPU goes to 100%
def GetResUsage(rName,sents,bugId,oPath):
	if rName.lower() == 'cpu':
		# Get numbers
		for sent in sents:
			# print sent
			#m = re.search('(\d+).*cpu|cpu.*(\d+)',sent)
			m = re.search('(\d+%?).*cpu',sent)
			if m != None:
				UtilTools.AppendToFile(oPath,'%s,CPU usage: %s' % (bugId,m.group(0)))
				#print m.group(0)	
			# *?: non greedy matching
			m = re.search('cpu.*?(\d+%?)',sent)
			if m != None:
				UtilTools.AppendToFile(oPath,'%s,CPU usage: %s' % (bugId,m.group(0)))
				#print m.group(0)	
	#TODO: Add RegEx for other types 

# ptnDict: pattern statistics dictionary, a dict of dicts
# catName: category name, e.g., Action, Input
# catVal: e.g., Action: start/stop; Input: cgi/HTML
# {'Action': {'start':1, 'stop':2}, 'Input': {'cgi':10,'html':5}}
def UpdatePtnDictCount(ptnDict,catName,catVal):
	# Check if the catName is already in the dictionary
	if catName in ptnDict.keys():
		if catVal in ptnDict[catName].keys():
			ptnDict[catName][catVal] += 1
		else:
			# category exists
			ptnDict[catName].update({catVal:1})
	else:
		# Add category
		#ptnDict.update(catName={catVal:1})
		ptnDict[catName] = {catVal:1}

# Remove comments quotations
def RemoveCmtQuote(sent):
	return re.sub('(>\s)+.*','',sent,flags=re.IGNORECASE)

# Pre-process sentences
def SentsPreProc(sents):
	# Remove comment quotations
	return [RemoveCmtQuote(sent) for sent in sents]

def GetSentFromReport(iFilePath):
	#rawText = open(iFilePath).read()
	with codecs.open(iFilePath,'r',encoding='utf8') as f:
		rawText = f.read()
		sents = nltk.sent_tokenize(rawText)
	return sents

# Get test signature
def GetSignature(dirRoot,inFileName,conf,ptnDict,metaPath):
	inFilePath = dirRoot + inFileName
	#print 'Input file path: ' + inFilePath
	WriteToStdErr('\ninFileName: ' + inFileName)

	#wordlists = PlaintextCorpusReader(dirRoot,inFileName)
	stopWords = stopwords.words('english')
	#print wordlists.fileids()
	# TODO: How not to split on hyphen
	sents = GetSentFromReport(inFilePath)
	## Pre-Processing
	sents = SentsPreProc(sents)
	reportRawTokens = []	
	for sent in sents:
		reportRawTokens.extend(nltk.word_tokenize(sent))
	#print reportRawTokens

	#reportRawTokens = Text(w.lower() for w in wordlists.words(inFileName))
	# TODO: create a function for lemmatization
	# Get context: Part of Speech
	report_pos = pos_tag(reportRawTokens)	
	#print report_pos
	report = []
	# Lemmarization
	lemma = WordNetLemmatizer()
	for token,tag in report_pos:
		# Skip stop words
		if token in stopWords:
			continue
		#print('{}:{}'.format(token,tag)) 
		 #	n for noun files, v for verb files, a for adjective files, r for adverb files
		if tag.startswith('VB'): # Verb
			sTag = wordnet.VERB
		elif tag.startswith('NN'): # Noun
			sTag = wordnet.NOUN
		elif tag.startswith('JJ'):
			sTag = wordnet.ADJ
		elif tag.startswith('RB'):
			sTag = wordnet.ADV
		else: # TODO: what is the better tagger to use and add other types of pos tag
			sTag = ''
		
		if sTag == '':
			word = lemma.lemmatize(token)
		else: 
			word = lemma.lemmatize(token,pos=sTag)
		report.append(word.lower())
		#print word

	#print report
	## Action
	fdist = nltk.FreqDist(report)
	#print(fdist['-'])
	bgs = nltk.bigrams(report)
	#print list(bgs)
	#print 'Collocation: ', report.collocations()
	bigramDist = nltk.FreqDist(bgs)
	#print 'bigramDist:', bigramDist.most_common(10)

	actionDict = ReportUnigramFreq(fdist,conf)
	# Sort in descending order
	sortedActionDict = sorted(actionDict.items(),key=operator.itemgetter(1),reverse=True)
	selectedAction = 'NonAct'
	if bool(sortedActionDict):
		if sortedActionDict[0][1] != 0:
			selectedAction = sortedActionDict[0][0]
			WriteToStdErr('Actions: ' + str(selectedAction))
			WriteToStdErr(str(sortedActionDict))
			absAction = 'ACTION'
		else:
			WriteToStdErr('Actions: N/A')
			absAction = 'NO_ACTION'
	
	UpdatePtnDictCount(ptnDict,'Actions',selectedAction)
	
	## Load
	selectedLoad = 'NonLoad'
	loadList = GetLoad(sents,conf)
	# Get throughput
	SaveThroughput(sents,inFileName,metaPath)
	if loadList:
		if loadList[0][1] != 0:
			selectedLoad = loadList[0][0]
			WriteToStdErr('Load:' + selectedLoad)
			WriteToStdErr(str(loadList))
			absLoad = 'LOAD'
	else:
		WriteToStdErr('Load: N/A')
		absLoad = 'NO_LOAD'
	
	UpdatePtnDictCount(ptnDict,'Load',selectedLoad)

	## Input file
	GetFileDetail(sents,inFileName,metaPath)
	selectedFileType = 'NonFile'
	sortedFileDict = GetInputFile(sents,conf)
	if bool(sortedFileDict):
		if sortedFileDict[0][1] != 0:
			selectedFileType = sortedFileDict[0][0]
			WriteToStdErr('File:' + selectedFileType)
			WriteToStdErr(str(sortedFileDict))
			absFileType = 'FILE'
	else:
		WriteToStdErr('File: N/A') 
		absFileType = 'NO_FILE'
	
	UpdatePtnDictCount(ptnDict,'Input',selectedFileType)

	## Configuration Option
	optionDict = {}
	confName = UtilTools.GetCsvOpVals(conf,'PTN','CONFIGS')
	#print '@'+str(confName[0])+'@'
	# Similarity first, then search keywords
	selectedOp = 'NonOp'
	absOp = 'NO_OP'

	topNConf = 50
	selectedOps,simScores = GetInferredOp(inFilePath,conf,topNConf)
	WriteToStdErr('Infered option:' + str(selectedOps)) 
	WriteToStdErr('Sim scores:' + str(simScores))
	# TODO: save configuration option into a standalone file

	outOpList = './inferredOpList'
	# print outOpList
	with open(outOpList, 'a+') as fout:
		for op in selectedOps:
			fout.write(op+'\n')
		fout.write('NonOp\n')

	#WriteToStdErr('Options: N/A') 
	# Set a threshold for the inferred option and decide 
	# if absOp should be NO_OP or OP

	# TODO: use splitted conf name as doc
	splitSelectedOps,splitSimScores = GetInferredOpSplit(inFilePath,conf,topNConf)
	WriteToStdErr('Split infered option:' + str(splitSelectedOps)) 
	WriteToStdErr('Split sim scores:' + str(splitSimScores))

	if simScores[0] > 0.1:
		selectedOp = selectedOps[0]
		absOp = 'OP'

	UpdatePtnDictCount(ptnDict,'Options',selectedOp)

	sortedOptionDict = GetOptionsFreq(fdist,confName[0])
	if bool(sortedOptionDict): 
		if sortedOptionDict[0][1] != 0:
			selectedOp = sortedOptionDict[0][0]
			selectedOp = "OP_" + selectedOp
			WriteToStdErr('Options: ' + str(sortedOptionDict))
			WriteToStdErr(str(sortedOptionDict))
			absOp = 'OP'
			# Get option value range
			GetOpVals(dict(sortedOptionDict),sents,inFileName,metaPath)
	else:
		WriteToStdErr('No conf options matched!')
		#'/home/x/TestGen/DataMining/ApacheOpDoc'
		
	
	## Module 
	selectedMod = 'NonMod'
	modPtn = UtilTools.GetOpVal('apache.ini','OTHERS','MOD')
	sortedModDict = GetModule(modPtn,sents)

	absMod = 'NO_MOD'
	if bool(sortedModDict):
		if sortedModDict[0][1] != 0:
			selectedMod = sortedModDict[0][0]
			WriteToStdErr('Module: ' + selectedMod)
			WriteToStdErr(str(sortedModDict))
			absMod = 'Mod'
		else:
			WriteToStdErr('Module: N/A') 

	UpdatePtnDictCount(ptnDict,'Module',selectedMod)

	## Symptoms 
	selectedSymp = 'NonSymp'
	sortedSympDict = GetSymptoms(fdist,conf)
	# print 'sortedSympDict: %s' % sortedSympDict

	if bool(sortedSympDict):
		if sortedSympDict[0][1] != 0:
			selectedSymp = sortedSympDict[0][0]
			WriteToStdErr('Symptom: ' + selectedSymp)
			WriteToStdErr(str(sortedSympDict))
			absSymp = 'SYMP'
			# Get resource usage level, metadata
			GetResUsage(selectedSymp,sents,inFileName,metaPath)
			GetResLevel(selectedSymp,sents,inFileName,metaPath)
		else:
			WriteToStdErr('Symptom: N/A') 
			absSymp = 'NO_SYMP'

	UpdatePtnDictCount(ptnDict,'Symptom',selectedSymp)

	# PatternID: Action + Option + Input + Symp
	#patternId = ','.join([selectedAction,selectedFileType,selectedOp,selectedMod,selectedLoad,selectedSymp,inFileName])
	patternId = ','.join([selectedAction,selectedFileType,selectedOp,selectedLoad,selectedSymp,inFileName])
	#absPtn = '\t'.join([absAction,absFileType,absOp,absMod,absLoad,inFileName,absSymp])
	absPtn = '\t'.join([absAction,absFileType,absOp,absLoad,inFileName,absSymp])
	return patternId, absPtn
