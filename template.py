import sys
import os
import tkFileDialog
from time import sleep
if sys.version_info[0] < 3:
   from Tkinter import *
else:
   from tkinter import *

title1="Getting the Jama Verification Proxy for the Master Functions"

root=""
store = ""
def startGui():
    global root
    root=Tk()
    root.title(title1)
def kill():
    global window
    window.destroy()


def getFromEntryBox1():
    global id,root
    name = entry_1.get()
    string_to_display = name
    label_2 = Label(root)
    label_2["text"] = string_to_display
    id = int(label_2["text"])
    writeText(id)
    #root.destroy()
#end getFromEntryBox

def getFromEntryBox2():
    global root,id1,window,name
    name = entry_2.get()
    string_to_display = name
    label_2 = Label(root)
    label_2["text"] = string_to_display
    id1 = (label_2["text"])
    print "the name of jamaproxy ",id1
    print "Create Test Button is clicked"

    #root.destroy()
#end getFromEntryBox2

def getFromEntryBox3():
    print "Create Relation Button is clicked"

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
    b1 = Button(window,text = "Update",command = getInfoWindow)
    b2 = Button(window,text = "Quit",command = kill)
    l1.grid(row = 0,column = 0)
    l2.grid(row = 1,column = 0)
    l3.grid(row = 2,column = 0)
    l4.grid(row = 3,column = 0)
    entry1.grid(row = 0,column =1)
    entry2.grid(row = 1,column =1)
    entry3.grid(row = 2,column =1)
    entry4.grid(row = 3,column =1)
    b1.grid(row = 5,column = 0)
    b2.grid(row = 5,column = 1)
    window.mainloop()




def getInfoWindow():
    global window,na
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
    print "in the getInfoWindow",name1,name2,name3,name4
    print "getFromEntryBox2() function is callled"
    getFromEntryBox2()



def guimain():
    global entry_1,entry_2,root
    startGui()
    label_1 = Label(root,text = "Enter id")
    label_2 = Label(root,text = "Jama Proxy Id")
    entry_1 = Entry(root)
    entry_2 = Entry(root)
    button_1 = Button(root,text = "submit the Id",command = getFromEntryBox1)
    button_2 = Button(root,text = "Quit",command = quit)
    button_3 = Button(root,text = "Create Test",command = fillTestInfo)
    button_4 = Button(root,text = "Create Relation",command = getFromEntryBox3)
    label_1.grid(row = 0,column = 0)
    entry_1.grid(row = 0,column = 1)
    button_1.grid(row = 1,column = 0)
    button_2.grid(row = 1,column = 1)
    label_2.grid(row = 3,column = 0)
    entry_2.grid(row = 3,column = 1)
    button_3.grid(row = 4,column = 0)
    button_4.grid(row = 4,column = 1)
    root.mainloop()
    #print "Exited from the guimain function"
#end guimain


if __name__ == '__main__':
    #print("in the __name__ function")
    guimain()
