#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from xml.dom.minidom import parse, parseString, Document
import re
import os,sys
import kommunenummer
import mypasswords
import mysql.connector
from osmapi import OsmApi


if len(sys.argv) != 2:
	print ("Usage command <osm-file>")
	sys.exit()

cachedir = "/var/cache/addrnodeimport"

munipnumber = sys.argv[1]
munipnumberpadded = "%04d" % (int(munipnumber))

#report1 = open(cachedir+"/reports/report_"+str(munipnumberpadded)+".txt","r")
#content = report1.read()
##match1 = re.compile(u"Existing:\s+(\d+)\s+New")
#matches = re.match(r"Existing:\s+(\d+)\s+New:\s+(\d+)\s+Missing:\s+(\d+)\s+Otherthings:\s+(\d+)\s+Duplicates:\s+(\d+)\s+Veivegfixes:\s+(\d+)\s+Buildings:\s+(\d+)\s+Abandoned:\s+(\d+)\s+Notmatched:\s+(\d+)\s+NotmatchedPOIs:\s+(\d+)",content,re.MULTILINE);
#report1.close()
#print (matches.group(0))
#missing=matches.group(3)
#new=matches.group(2)
#notmatched=matches.group(9)
#
#report1 = open(cachedir+"/reports/report2_"+str(munipnumberpadded)+".txt","r")
#content = report1.read()
##match1 = re.compile(u"Existing:\s+(\d+)\s+New")
#report1.close()
#matches = re.match(r"Fixes:\s+(\d+)\s+Errors:\s+(\d+)\s+Onlynumber:\s+(\d+)\s+",content,re.MULTILINE);
#print (matches.group(0))
#onlynumber=matches.group(3)
#fixes=matches.group(1)
#print (new)
#print (notmatched)
#print (missing)
#print (onlynumber)
#print (fixes)
#if int(notmatched) == 0 and int(fixes) == 0 and int(onlynumber) == 0 and int(new) != 0 and int(missing) != 0:
#	print ("Can be imported")
#else:
#	print ("Cannot be imported")
#	sys.exit()


db = mysql.connector.connect(host="localhost",user=mypasswords.sqldbuser,password=mypasswords.sql,database=mypasswords.sqldbname)
cursor = db.cursor()
cursor.execute("set names utf8")
cursor.execute("select person from osmimportresp where kommunenummer=\""+str(munipnumber)+"\" and person != 'rubund' and deleted != 1;")
rows = cursor.fetchall()
if(len(rows) > 0):
	print ("Someone else is responsible for this one. Not importing...")
	sys.exit()
else:
	print ("Nobody is responsible for this one")

cursor.execute("select tid from update_requests where kommunenummer=\"%s\" and ferdig=0 and upload=0 order by tid desc limit 1" % (munipnumber,))
rows = cursor.fetchall()
if(len(rows) > 0):
	print("Waiting for getting updated")
	sys.exit()

cursor.execute("select tid from update_requests where kommunenummer=\"%s\" and ferdig=1 and upload=1 and addtime(tid, \"0:20:00\") > now()" % (munipnumber,))
rows = cursor.fetchall()
if(len(rows) > 0):
	print("Has recently uploaded, will skip for now")
	sys.exit()
db.close()

#api = OsmApi(api="api06.dev.openstreetmap.org", username="", password="", changesetauto=True, changesetautotags={"source":"Kartverket"})
#api = OsmApi(api="api06.dev.openstreetmap.org", username="rubund_import", passwordfile="./password.txt")
api = OsmApi(username=mypasswords.osmuser, password=mypasswords.osm)
#api.NodeGet(123)
mycomment=u"addr node import "+kommunenummer.nrtonavn[int(munipnumber)]+" kommune"
#mycomment=u"addr node import municipality number "+munipnumberpadded+", Norway"
#api.ChangesetCreate({"comment":u"addr node import "+str(sys.argv[2].decode('utf-8')), "source":"Kartverket", "source:date":"2014-08-24"})
api.ChangesetCreate({"comment": mycomment, "source":"Kartverket", "source:date":"2017-04-25"})

if not os.path.isfile(cachedir+"/reports/new/"+str(munipnumberpadded)+"/changes_"+str(munipnumberpadded)+".osm"):
	print("Cannot find file")
	sys.exit(-1)

dom1 = parse(cachedir+"/reports/new/"+str(munipnumberpadded)+"/changes_"+str(munipnumberpadded)+".osm")
mainelement1 = dom1.getElementsByTagName("osm")[0]
nodes = mainelement1.childNodes
counter = 1
for node in nodes:
	if(node.nodeType == 1):
		if node.tagName != "node":
			continue
		#if node.tagName != "node" and node.tagName != "way":
		#	continue
		housenumber = ""
		street      = ""
		postcode    = ""
		city        = ""
		osm_id = node.attributes["id"].value
		osm_version = node.attributes["version"].value
		if node.tagName == "node":
			latitude = node.attributes["lat"].value
			longitude = node.attributes["lon"].value
		tags = node.getElementsByTagName("tag")
		if "action" in node.attributes:
			action = node.attributes["action"].value
		else:
			action = ""
		jtags = {}
		for tag in tags:
			if tag.attributes["k"].value == "addr:housenumber":
				housenumber = tag.attributes["v"].value
				jtags["addr:housenumber"] = housenumber
			#elif tag.attributes["k"].value == "addr:street":
			#	street = tag.attributes["v"].value
			#	jtags.append("addr:street" : street)
			#elif tag.attributes["k"].value == "addr:postcode":
			#	postcode    = tag.attributes["v"].value
			#	jtags.append("addr:postcode" : postcode)
			#elif tag.attributes["k"].value == "addr:city":
			#	city        = tag.attributes["v"].value
			#	jtags.append("addr:city" : city)
			else:
				jtags[tag.attributes["k"].value] = tag.attributes["v"].value
		ndlist = []
		if node.tagName == "way":
			nds = node.getElementsByTagName("nd")
			for nd in nds:
				ndlist.append(nd.attributes["ref"].value)

		if housenumber != "":
			editnode = {}
			if action == "modify":
				if node.tagName == "node":
					editnode = {"id": osm_id , "version" : osm_version , "lat" : latitude, "lon": longitude , "tag": jtags}
				else:
					editnode = {"id": osm_id , "version" : osm_version , "tag": jtags, "nd" : ndlist}
			elif action == "delete":
				if node.tagName == "node":
					editnode = {"id": osm_id , "version" : osm_version , "lat" : latitude, "lon": longitude , "tag": jtags}
			else:
				if node.tagName == "node":
					editnode = {"id": -counter , "version" : osm_version , "lat" : latitude, "lon": longitude , "tag": jtags}
					counter = counter + 1;
			#print (str(latitude)+""+str(longitude)+""+street+" "+housenumber)
			if action == "modify":
				print("Modifying")
				if node.tagName == "node":
					api.NodeUpdate(editnode)
				else:
					api.WayUpdate(editnode)
			elif action == "delete":
				print("Deleting")
				if node.tagName == "node":
					api.NodeDelete(editnode)
			else:
				if node.tagName == "node":
					print("Creating")
					api.NodeCreate(editnode)
			print (editnode)
		
api.ChangesetClose()

db = mysql.connector.connect(host="localhost",user=mypasswords.sqldbuser,password=mypasswords.sql,database=mypasswords.sqldbname)
cursor = db.cursor()
cursor.execute("set names utf8")
cursor.execute("insert into update_requests (kommunenummer,ip,tid) values ('"+str(munipnumber)+"','script',addtime(now(),\"0:05:00\"));")
db.commit()
db.close()
#os.system("echo \"insert into update_requests (kommunenummer,ip,tid) values (543,'script',now())\" | mysql -u ruben --password="+mypasswords.sql+" beebeetle")
##api.flush()
#api.NodeCreate
