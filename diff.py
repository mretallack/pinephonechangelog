
import requests
import shutil
import json
import lzma
import tarfile
from deb_parse.parser import Parser
from jsondiff import diff
from io import StringIO
from deepdiff import DeepDiff

index="http://system-image.ubports.com/16.04/arm64/mainline/devel/pinephone/index.json"



r =requests.get(index)


jsondata = r.json()

lastFull=None
lastDelta=None
lastPackageList=None


htmlData = open('pinephonechangelog.html','w')


htmlData.write("""
<html>
<head></head>
<body>""")

for curImg in reversed(jsondata["images"]):
    #print(curImg)

    if curImg["type"] == "full":
        lastFull=curImg
    else: 
        lastDelta=curImg

        print("##################################################")
        print("Delta for release: "+str(curImg["version"]))
        print("")

        htmlData.write("<h1>"+"Delta for release: "+str(curImg["version"])+"</h1>")


        path=curImg["files"][0]["path"]

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
                    print("UBoot/Kernel etc...")
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

                            print("Change from "+str(change.t1)+" to "+str(change.t2))

                            curLevel=change
                            while True:

                                if "name" in curLevel.t1:
                                    print("Found Name: "+curLevel.t1["name"]+", description: "+curLevel.t1["details"]["synopsis"])
                                    
                                    htmlData.write("<h2>"+curLevel.t1["name"]+"</h2>")
                                    htmlData.write("<h3>"+"Change from "+str(change.t1)+" to "+str(change.t2)+"</h3>")
                                    htmlData.write(curLevel.t1["details"]["synopsis"])

                                    
                                    break
                                curLevel=curLevel.up
                    
                    lastPackageList=packageList
               # else:
               #     print("Unknown member: "+member.name)
            tar.close()

        htmlData.write("<hr>")

print("Last full: "+str(lastFull["version"]))
print("Last delta: "+str(lastDelta["version"]))

htmlData.write("""
</body>
</html>
""")


htmlData.close()

#path=lastDelta["files"][0]["path"]



#outFile=lzma.open('file.xz').read()

#tar = tarfile.open('file.xz', "r:xz")
#tar.extractall()
#tar.close()



