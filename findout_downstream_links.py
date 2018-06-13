from utils import jama_api
import sys
import os
import tkFileDialog
from time import sleep
if sys.version_info[0] < 3:
   from Tkinter import *
else:
   from tkinter import *
from jama import API
from widgets import unamepass
import re

# global variables
jama_production_url = 'http://jama03.rockwellcollins.com/contour/ws/v3/soap/ContourSoapService?wsdl'
title1="Getting the Jama Verification Proxy for the Master Functions"


# Please contact Deepak Gupta if any support required. """
path = r"C:\C295Jama"
root=""
store = ""
def startGui():
    global root
    root=Tk()
    root.title(title1)


def killGui():
    global window
    window.destroy()

reqapid = {}
username = ""
password = ""
# jama rest
jamarest = ''
def jamaInt():
    global jamarest
    # print("in the jamaInt function")
    jamarest = jama_api.JamaRestApi(server='jama03')
    jamarest.prompt_for_auth()

jamasoap=""
def jamasoapInt():
    
    global jamasoap
    # print("in the jamasoapInt function")
    jamasoap=API(unamepass.username,unamepass.password,jama_production_url)
# End jamasoapint()

def getFromEntryBox1():
    global id,root
    name = entry_1.get()
    string_to_display = name
    label_2 = Label(root)
    label_2["text"] = string_to_display
    id = int(label_2["text"])
    writeText(id)
    # root.destroy()
# End getFromEntryBox()


def fillTestInfo():
    global root,entry1,entry2,entry3,entry4,window
    window = Toplevel(root)
    window.title("Update Test Case Details")
    l1 = Label(window,text = "CM File Name")
    l2 = Label(window,text = "CM Path")
    l3 = Label(window,text = "CM Revision")
    l4 = Label(window,text = "Ref Loc Path")
    entry1 = Entry(window)
    entry2 = Entry(window)
    entry3 = Entry(window)
    entry4 = Entry(window)
    b1 = Button(window,text="Update", command=getInfoWindow)
    b2 = Button(window,text="Quit", command=killGui)
    l1.grid(row=0, column=0)
    l2.grid(row=1, column=0)
    l3.grid(row=2, column=0)
    l4.grid(row=3, column=0)
    entry1.grid(row=0, column=1)
    entry2.grid(row=1, column=1)
    entry3.grid(row=2, column=1)
    entry4.grid(row=3, column=1)
    b1.grid(row=5, column=0)
    b2.grid(row=5, column=1)
    window.mainloop()

# End of fillTestInfo()

def getInfoWindow():
    global root,window,na
    name1 = entry1.get()
    name2 = entry2.get()
    name3 = entry3.get()
    name4 = entry4.get()
    label1 = Label(window)
    label1["text"] = name1
    label2 = Label(window)
    label2["text"] = name2
    label3 = Label(window)
    label3["text"] = name3
    label4 = Label(window)
    na = label4["text"] = name4
    # print "value of name1,name2,name3,name4",name1,name2,name3,name4
    # print "getFromEntryBox2() function is callled"
    getFromEntryBox2(name1,name2,name3,name4)

def getFromEntryBox2(n1,n2,n3,n4):
    #fillTestInfo()
    cm_filename = n1
    cm_path = n2
    cm_revision = n3
    cm_ref_loc_path = n4
    global root,id1,window
    name = entry_2.get()
    string_to_display = name
    label_2 = Label(root)
    label_2["text"] = string_to_display
    id1 = int(label_2["text"])
    print "the id of jamaproxy", id1
    print "Create Test Button is clicked"
    print "cm_filename,cm_path,cm_revision,cm_ref_loc_path", cm_filename, cm_path, cm_revision, cm_ref_loc_path
    jamaTestCaseCreate(cm_filename, cm_path, cm_revision, cm_ref_loc_path)

# End getFromEntryBox()


def getFromEntryBox3():
    print "Create Relation Button is clicked"
    jamaReletionshipCreate()
# End of getFromEntryBox3()


def guimain():
    global entry_1,entry_2,root
    startGui()
    # print "In the guimain function"
    label_1 = Label(root,text = "Enter Master Feature Id")
    label_2 = Label(root,text = "Jama Proxy Id")
    entry_1 = Entry(root)
    entry_2 = Entry(root)
    button_1 = Button(root,text="Get DStream Id", command=getFromEntryBox1)
    button_2 = Button(root,text="Quit", command=quit)
    button_3 = Button(root,text="Create Test", command=fillTestInfo)
    button_4 = Button(root,text="Create Relation", command=getFromEntryBox3)
    label_1.grid(row=0, column=0)
    entry_1.grid(row=0, column=1)
    button_1.grid(row=1, column=0)
    button_2.grid(row=1, column=1)
    label_2.grid(row=3, column=0)
    entry_2.grid(row=3, column=1)
    button_3.grid(row=4, column=0)
    button_4.grid(row=4, column=1)
    root.mainloop()
    # print "Exited from the guimain function"
# End of guimain()

def getId(id):
    global data
    # print "Id is ",type(id)
    data = jamasoap('getDownstreamRelationships', id)
    #print("data",data)
    return data
# end getId

def unicode(da):
    n = ""
    for k in da:
        if ord(k) < 128:
            n += k
    #print n
    return n

def getDownSteramData(id):
   var = getId(id)
   store = {}
   jamaGidPid = {}
   for i in range(len(var)):
      d = var[i].toItem
      try :
          k =str(d.globalId)
          j = d.id
          store[str(k)] = repr( d.name)
      except UnicodeEncodeError:
          store[str(k)] = unicode(d.name)
      except Exception as e:
          print e
          #print na


      #store[str(d.globalId)] = repr(na)
      #try:

      jamaGidPid[str(d.globalId)] = str(d.id)
      #jamaGidPid[str(k)] = str(j)
      #intStore[d.globalId] = d.name
   # end for
   return store,jamaGidPid
   # print "Total {0} downstream is found for give MasterFeature  ID {1} \n".format((len(var)),id)
   # print "Listed of the downstream Id's \n",store.keys()
   # print "Name of the Id's and Function Name of the downstream Id's\n",store
# End of getDownSteramData()


def getAllContent(id):
    var = getId(id)
    dc ={}
    for i in range(len(var)):
        d = var[i].toItem
        dc[str(d.globalId)] = [str(d.name),str(d.description)]
    print "length of the items is",len(dc)
    return dc

def getLocalData():
    global id
    store,jamaGidPid = getDownSteramData(id)
    return store,jamaGidPid


def writeText(gid):
   #global id
   id = gid
   createDirectory()
   store,jamaGidPid = getDownSteramData(id) #dictionary way of using
   #sv = getAllContent(id)
   #print "in the writeText function",store
   #store = getDownSteramData(id)
   if os.path.isfile(path+"\jamaid.txt"):
       os.remove(r'C:\C295Jama\jamaid.txt')

   counter = 0 #count the Length of the Items
   #farray = []
   with open(path+"\jamaid.txt","w") as fd:
       #fd.writelines(store)#List way of using
       #fd.writelines([i+"\n" for i in store.keys()])#way of writing the dictionary in the file

       for k,v in store.items(): #New way of writing the dictionary keys and valye
           if "-SysReq-" in k:
               fd.write(str(k)+"  :     " + str(v)+ "\n")
               #farray.append(str(k)+"  :     " + str(v)+ "\n")
               #farray.sort()
               #print farray
               counter+=1

   # print "type of store data type is ", type(store)
   # print "Total {0} downstream is found for give MasterFeature  ID {1} \n".format((counter),id)
   # print "Listed of the downstream Id's \n",store.keys()
   print "Name of the Id's and Function Name of the downstream Id's \n",store
   #print "intStore \n",intStore'''
   print "File Sucessfully created at location {0}...".format(path+"\jamaid.txt")
   print "Opening the file {0} in Default text Editor".format(path+"\jamaid.txt")
   openEditor(path+"\jamaid.txt")
   # print "Dispaly the content in the Downstream ID",sv
   print "Total {0} downstream is found for given MasterFeature  ID {1} \n".format((counter), id)

#End of writeText()

def openEditor(ofile):
    os.system(ofile)
#End openEditor()

def createDirectory():
   if not (os.path.isdir(path)):
      os.mkdir(path)
      print "Directory Created Sucessfully"
   print "Already Directory Existed in Location",path
#End of createDirectory()


def createJamaProxy():

    jamaTestCaseCreate()
    jamaReletionshipCreate()

def jamaTestCaseCreate(fname,cpath,crevision,rlpath):
    global id1
    data,jamaGidPid = getLocalData()
    print "data variable type ",type(data),len(data)
    print "value of the data is ",data
    print "valye of jamaGlobal and Project ID",jamaGidPid
    print "id of the given value",id1
    va = jamasoap("getItem",id1)
    #getDownSteramData(id1)
    print "value are ",va.projectId,va.documentTypeId,va.parentId
    length = len(data)
    jamaPid = []
    counter = 0 #count the Length of the Items
    #elist = checkProxyExist(id1)
    #print "jamaproxy id is = ", id1
    #print "elist values are ", elist
    for k,v in data.items():
        if ("-SysReq-") in k:
            s = jamarest.create_item(va.projectId, 187, id1, {'name': v,
                                                           'verification_method' :[1582],
                                                           'cm_path':cpath,
                                                           'cm_file_name':fname,
                                                           'cm_revision':crevision,
                                                           'reference_location_in_file':rlpath
                                                           }
                                     )
            s['meta']['location']
            ffd = re.findall(r'\d+',s['meta']['location'])
            jamaPid.append([i for i in ffd if len(i)>4])
            counter+=1

    print "value of s ",s
    print "sorted value of jamaPid are ",jamaPid[0]
    #jamarest.create_item(v.projectId,56,id1,{'name': 'auto tool try'})
    print "Total {0} Jama Proxy is created sucessfully".format(counter)

#End of jamaTestCaseCreate()


def checkProxyExist(uid):
    print "in the checkProxyExist function "
    a,b = getDownSteramData(uid)
    print "length of a ",len(a)
    u_id = uid
    l_list = []
    data = jamarest.get_all_children(u_id)
    print "data from the existing jama proxy",data
    for i in range(len(data)):
        data[i]['id']
        up = jamasoap('getUpstreamRelationships', data[i]['id'])
        if len(up) >= 1:
            print "already have link", up[0].toItem.id
        else:
            print "dont have link", data[i]['id']
            l_list.append(data[i]['id'])

    idlist = []
    return l_list


def jamaReletionshipCreate():

    global id1,id
    createddict = {}
    existingdict = {}
    print "jamaReletionshipCreate function and the given id1 and id is ",id1,id
    existingitems = jamasoap('getDownstreamRelationships', id)
    createditems =jamarest.get_all_children(id1)
    for i in range(len(existingitems)):
        if ("COL03-SysReq") in existingitems[i].toItem.globalId:
            existingdict[existingitems[i].toItem.name] = [existingitems[i].toItem.id,existingitems[i].toItem.globalId]
    print "existingdict is created"
    #End for
    for i in range(len(createditems)):
        createddict[createditems[i]['fields']['name']] = [createditems[i]['id'],createditems[i]['fields']['globalId']]
    print "createddict is created"
    #End for
    for k,v in existingdict.items():
        if k in createddict:
            jamarest.create_relationship(v[0],createddict[k][0],22)
    print "Relationship is Created for Total {0} JamaProxy".format(len(createditems))

#End of jamaReletionshipCreate()

if __name__ == '__main__':
    import time
    #print("in the __name__ function")
    jamaInt()
    jamasoapInt()
    guimain()
#End of __name__


    #Below commented code is test code
    '''ci= {}
    ei = {}
    ci[createditems[2]['fields']['name']] = [createditems[2]['id'],createditems[2]['fields']['globalId']]
    #jamarest.create_relationship(frm,to,lin)
    ei[existingitems[0].toItem.name] = [existingitems[0].toItem.id,existingitems[0].toItem.globalId]

    print "value of created items at location 2",ci
    print "value of existing items at location 0",ei
    for k,v in ei.items():
        if ci[k]:
            print "value of from id {0} to id {1} and Item type {2}".format(ci[k][0],v[0],22)
            jamarest.create_relationship(ci[k][0],v[0],22)'''

'''def jamaCreTcItem(ltc):
    newtc=jamarest.create_item(evalues[7],evalues[2],evalues[3],{'name':ntpath.split(tcdata[ltc][0])[1],'description':tcdata[ltc][0]})#,'revision':tcdata[ltc][1]})
    return int(os.path.basename(newtc['meta']['location']))'''

'''def jamaCreTpItem(ltp):
    newtp=jamarest.create_item(evalues[7],evalues[4],evalues[5],{'name':ntpath.split(ltp[0])[1] ,'description':ltp[0]})#,'revision':tpdata[ltp][1]})
    return int(os.path.basename(newtp['meta']['location'])) '''


'''def getDownSteramData(id):
   var = getId(id)
   store = []
   #intStore = {}
   for i in range(len(var)):
      d = var[i].toItem
      #store[str(d.globalId)] = repr(d.name)
      #intStore[d.globalId] = d.name
      store.append(str(d.globalId)+"  :  "+ repr(d.name)+"\n")
   #end for
   return store
   #print "Total {0} downstream is found for give MasterFeature  ID {1} \n".format((len(var)),id)
   #print "Listed of the downstream Id's \n",store.keys()
   #print "Name of the Id's and Function Name of the downstream Id's\n",store
#end getDownSteramData'''


'''def updateTestCaseSteps():
    global root,id1,window
    name = entry_2.get()
    string_to_display = name
    label_2 = Label(root)
    label_2["text"] = string_to_display
    id1 = int(label_2["text"])
    print "the id of jamaproxy ",id1
    print "Create Test Button is clicked"
    jamaTestCaseCreate()'''

