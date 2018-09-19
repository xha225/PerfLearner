import requests
import os
import re
import sys, getopt
from bs4 import BeautifulSoup

def create_corpora(urls_file, subdir, corporaDir):
	bug_report_urls_list = open(urls_file, "r")
	
	for url_str in bug_report_urls_list:
		url_with_comm = url_str.rstrip('\n')
		url_split_comm = url_with_comm.split('#')
		url = url_split_comm[0].rstrip(' ')
		id_num = re.findall(r'\d+', url)[0]
		outFilePath = corporaDir+'ID_'+id_num+'.txt'
		if os.path.isfile(outFilePath):
			print 'Found file: ' + outFilePath
			continue
		else:
			print 'Processing" ' + outFilePath

		# print(url)
		# print(id_num)
		# https://bugzilla.mozilla.org/show_bug.cgi?id= 
		r = requests.get(url)
		soup = BeautifulSoup(r.text, "html.parser")
		#soup.encode("utf-8")
		#cls = soup.find_all("class")
					
		with open(outFilePath, 'w') as fout:
			title_data = soup.find_all("h1", {"id":"field-value-short_desc"})
			for item in title_data:
				title = str(item.text.encode("utf-8"))
				title = re.sub(r'\\xe2\\x80\\x93', '', title)
				title = re.sub(r'b\'', '', title)
				#sent = re.sub(r\n\n*, ' ', sent)
				title = title.replace('\\n', ' ')
				title = re.sub(r'b\"', '', title)
				title = title.rstrip('\'')
				title = title.rstrip('\"')
				title = title.rstrip('\\n')
				fout.write(title + '\n')

			g_data = soup.find_all("pre", {"class": "comment-text"})
			for item in g_data:
				sent = item.text
				sent = str(item.text.encode("utf-8"))
				sent = re.sub(r'b\'', '', sent)
				sent = sent.replace('\\n', ' ')
				sent = sent.replace('\\r', ' ')
				sent = re.sub(r'b\"', '', sent)
				sent = re.sub(r'\r', '', sent)
				sent = sent.rstrip('\'')
				sent = sent.rstrip('\"')
				sent = sent.rstrip('\\n')
				fout.write(sent)
	return

# Main
ops, otherOps = getopt.getopt(sys.argv[1:],'o:f:h')
#print ops
outDir = None
urlFile = None

for op,val in ops:
	if op == '-o':
		outDir = val
		print 'outDir' + val
	elif op == '-h':
		print 'Usage: python ' + sys.argv[0] +' -o ./OutputDir/ -f bugUriList'
		sys.exit(0)
	elif op == '-f':
		urlFile = val	
	else:
		print 'Unknown option: ' + op
		sys.exit(0)

create_corpora(urlFile,'./',outDir)
