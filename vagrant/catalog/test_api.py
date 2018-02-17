import httplib2
import json
import sys
import codecs
sys.stdout = codecs.getwriter('utf8')(sys.stdout)
sys.stderr = codecs.getwriter('utf8')(sys.stderr)

address = 'http://0.0.0.0.xip.io:5000'

# Testing READ all ideas
try:
	print "Starting endpoint tester...\n"

	print "Testing all_ideas...\n"
	url = address + '/api/all_ideas'
	h = httplib2.Http()
	resp, result = h.request(url,'GET')
	if resp['status'] != '200':
		raise Exception('Received an unsuccessful status code of %s' % resp['status'])
	print json.loads(result)

	print "\n"

except Exception as err:
	print "Test #1 Failed, couldn't read all ideas"
	print err.args
	sys.exit()

else: 
	print "Passed Test #1"

# Testing READ idea based on idea_id
try:
	print "Testing single id...\n"

	idd = "2"

	url = address + '/api/' + idd + '/idea'
	h = httplib2.Http()
	resp, result = h.request(url,'GET')
	if resp['status'] != '200':
		raise Exception('Received an unsuccessful status code of %s' % resp['status'])
	print json.loads(result)

	print "\n"

except Exception as err:
	print "Test #2 Failed, couldn't read idea with id = " + idd
	print err.args
	sys.exit()

else: 
	print "Passed Test #2"