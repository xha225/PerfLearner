import requests
import os
import re
import sys, getopt
reload(sys)
sys.setdefaultencoding('utf8')
import UtilTools

# The script is used to get apache directive documentation
ops, otherOps = getopt.getopt(sys.argv[1:],'o:f:h')
#print ops
outDir = None
url = None

for op,val in ops:
	if op == '-o':
		outDir = val
	elif op == '-h':
		print 'Usage: python %s -f http://kb.mozillazine.org/About:config_entries -o ./FfConfDesc' % sys.argv[0] 
		sys.exit(0)
	elif op == '-f':
		url = val	
	else:
		print 'Unknown option: ' + op
		sys.exit(0)

UtilTools.getFfOpDoc(url,outDir)
