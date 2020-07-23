
import requests
import shutil
import json
import lzma
import tarfile
import re
from deb_parse.parser import Parser
from jsondiff import diff
from io import StringIO
from deepdiff import DeepDiff

index="http://system-image.ubports.com/16.04/arm64/mainline/devel/pinephone/index.json"


debug=False

r =requests.get(index)


jsondata = r.json()

lastFull=None
lastDelta=None
lastPackageList=None

changelog=[]

for curImg in jsondata["images"]:
    #print(curImg)

    if curImg["type"] == "full":
        lastFull=curImg
    else: 
        lastDelta=curImg

        if debug:
            print("##################################################")
            print("Delta for release: "+str(curImg["version"]))
            print("")

        changes=[]
            
        for curUpdateFile in curImg["files"]:

            
            path=curUpdateFile["path"]

            updateType="None"
            z=re.match("^/pool/([a-z]+)-",path)

            if z != None:
                updateType=z.groups()[0]

            

            if debug:
                print("Update type: "+updateType)

            deltaURL="http://system-image.ubports.com"+path

            #print("URL: "+str(deltaURL))

            r =requests.get(deltaURL, stream=True)

            if r.status_code == 200:
                with open("file.xz", 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)        

            
                tar = tarfile.open('file.xz', "r:xz")
                for member in tar.getmembers(): 
                    #print(member.name)

                    if member.name == "partitions/boot.img":
                        
                        if debug:
                            print("UBoot/Kernel etc...")

                        newEntry={
                                "name": "UBoot/Kernel etc...", 
                                "description": "",
                                "change": ""
                            }
                        changes.append(newEntry)


                    elif member.name == "system/var/lib/dpkg/status":

                        tar.extract(member) 

                        my_parser = Parser("system/var/lib/dpkg/status")

                        packageList=my_parser.clean_pkg_info
        
                        #print(packageList)

                        if lastPackageList != None:
                            #diffator = json_diff.Comparator(StringIO(lastPackageList), StringIO(packageList))
                            #diff = diffator.compare_dicts()
                            ddiff = DeepDiff(lastPackageList, packageList, verbose_level=1, view='tree', ignore_order=True)                            

                            set_of_values_changed = ddiff['values_changed']
                            #print(ddiff)
                            #print(set_of_values_changed)

                            #(changed,) = set_of_values_changed
                            changeList=list(set_of_values_changed)
                            
                            #print(changeList)
                            for change in changeList:
                                if debug:
                                    print("Change from "+str(change.t1)+" to "+str(change.t2))

                                curLevel=change
                                while True:

                                    if "name" in curLevel.t1:
                                        if debug:
                                            print("Found Name: "+curLevel.t1["name"]+", description: "+curLevel.t1["details"]["synopsis"])

                                        newEntry={
                                                "name":curLevel.t1["name"], 
                                                "description": curLevel.t1["details"]["synopsis"],
                                                "change": str(change.t1)+" -> "+str(change.t2)
                                            }
                                        changes.append(newEntry)
                                        
                                        break
                                    curLevel=curLevel.up
                        
                        lastPackageList=packageList
                   # else:
                   #     print("Unknown member: "+member.name)
                tar.close()

        newEntry={
                    "delta": str(curImg["version"]),
                    "changes": changes
                }
        
        changelog.append(newEntry)


if debug:
    print("Last full: "+str(lastFull["version"]))
    print("Last delta: "+str(lastDelta["version"]))



htmlData = open('pinephonechangelog.html','w')


htmlData.write("""
<html>
<head></head>
<body>""")

for deltaEntry in reversed(changelog):

    htmlData.write("<h1>"+"Delta for release: "+deltaEntry["delta"]+"</h1>")

    for logEntry in deltaEntry["changes"]:

        htmlData.write("<h2>"+logEntry["name"]+"</h2>")
        htmlData.write("<h3>"+"Change from "+logEntry["change"]+"</h3>")
        htmlData.write(logEntry["description"])

    htmlData.write("<hr>")



htmlData.write("""
</body>
</html>
""")


htmlData.close()



