
import requests
import shutil
import json
import lzma
import tarfile
import re
import yaml
import urllib.request
import hashlib
import os


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


def getKernelDiff():
    
    URL="https://gitlab.com/ubports/core/rootfs-builder-debos/-/raw/master/pine64-common.yaml"

    downloaded_obj = requests.get(URL)
    print(downloaded_obj.content)
    open('pine64-common.yaml', 'wb').write(downloaded_obj.content)

    with open('pine64-common.yaml') as file:

        data = yaml.load(file, Loader=yaml.FullLoader)

    print(str(data))

changelog=[]

lastKernelCFG=None
lastDTBCFG=None

def calcHash(img, srcFile):

    os.system('e2tools/e2cp '+img+':'+srcFile+' tmp/hashfile')

    hash_md5 = hashlib.md5()
    with open("tmp/hashfile", "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    newHash = hash_md5.hexdigest()
    return(newHash)


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
            #if debug:
            #    print("Update: "+str(curUpdateFile))
            
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
                with open("tmp/file.xz", 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)        

            
                tar = tarfile.open('tmp/file.xz', "r:xz")
                for member in tar.getmembers(): 
                    #print(member.name)

                    if member.name == "partitions/boot.img":
                        

                        #ext4 = Ext4(member.name)
                        bootChanges=""


                        tar.extract(member, path="tmp") 

                        newHash=calcHash("tmp/partitions/boot.img", "config-5.6.0-pine64")

                        if lastKernelCFG != newHash:
                            bootChanges+=", Kernel Config Changed"
                        lastKernelCFG = newHash

                        newHash=calcHash("tmp/partitions/boot.img", "dtb")

                        if lastDTBCFG != newHash:
                            bootChanges+=", Device Tree Config Changed"
                        lastDTBCFG = newHash

                        if debug:
                            print("UBoot/Kernel etc..."+bootChanges)


                        newEntry={
                                "name": "UBoot/Kernel etc...", 
                                "description": "",
                                "change": bootChanges
                            }

                        changes.append(newEntry)

                        #getKernelDiff()


                    elif member.name == "system/var/lib/dpkg/status":

                        tar.extract(member, path="tmp") 

                        my_parser = Parser("tmp/system/var/lib/dpkg/status")

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
                    #else:
                    #    print("Unknown member: "+member.name)
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



