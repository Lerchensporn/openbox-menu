#!/usr/bin/env python

# coding=utf8

import os
import menuconfig

def parseDeskFiles():
    entries = []
    walkdirs = ["/usr/share/applications", os.path.expanduser('~') + "/.local/share/applications"]
    for directory in walkdirs:
        for root, dirs, files in os.walk(directory):
            for fname in files:
                fname = root + "/" + fname
                if fname.find(".desktop") == -1:
                    continue
                deskfile = open(fname, "r")
                entry = {}
                for line in deskfile:
                    line = line.strip()
                    # Default config
                    if line.find("Name=") == 0:
                        entry["Name"] = line[len("Name="):]
                    if line.find("Exec=") == 0:
                        entry["Exec"] = line[len("Exec="):]
                    if line.find("Icon=") == 0:
                        entry["Icon"] = line[len("Icon="):]
                    if line.find("Categories=") == 0:
                        entry["Categories"] = line[len("Categories="):].split(";")
                    # user config
                    for item in menuconfig.name:
                        if line.find(item+"=") == 0:
                            entry["Name"] = line[len(item+"="):]
                            break
                if "Categories" not in entry or "Name" not in entry or "Exec" not in entry:
                    deskfile.close()
                    continue
                entry["Exec"] = entry["Exec"].replace("%U", "").replace("%F", "").replace("%u", "").replace("%f", "").strip()
                entry["Name"] = entry["Name"].replace("&", "&amp;")
                found = False
                for item in entries:
                    if item["Name"] == entry["Name"]:
                        found = True
                        break
                if not found:
                    entries.append(entry)
                deskfile.close()
    return entries

def getIconPath(icon):
    if icon[0] == "/":
        return icon
    dotindex = icon.find(".")
    if dotindex != -1:
        icon = icon[0:dotindex]
    iconDirs = ["/usr/share/pixmaps", "/usr/share/icons"]
    for item in iconDirs:
        for path, dirs, files in os.walk(item):
            for filename in files:
                dotindex = filename.find(".")
                if dotindex != -1:
                    ext = filename[dotindex:]
                    if ext == ".svg": continue
                    filename = filename[0:dotindex]
                if filename == icon:
                    return path + "/" + icon + ext
    return ""

def getExecLine(entry):
    line = "    <item label=\"" + entry["Name"] + "\""
    if "Icon" in entry:
        icon = getIconPath(entry["Icon"])
        line += " icon=\"" + icon + "\""
    line += "><action name=\"execute\"><execute>" + entry["Exec"] + "</execute></action>"
    line += "</item>\n";
    return line


def writeMenu():
    print("Writing new menu ...");
    entries = parseDeskFiles();
    print("Parsed .desktop files and found " + str(len(entries)) + " entries.");

    # loop through categories

    matchedlist = []
    submenu = {}
    for items in menuconfig.cats:
        if items[0] == "Others": continue
        submenu[items[0]] = ""
        entries = sorted(entries, key=lambda entry: entry["Name"].lower())
        entryindex = 0;
        for entry in entries:
            for cat in entry["Categories"]:
                if items[0] == cat:
                    matchedlist.append(entryindex)
                    submenu[items[0]] += getExecLine(entry)
            entryindex += 1

    # make text from submenu

    menuText = ""
    labelIndex = 0
    for items in menuconfig.cats:
        if items[0] in submenu and submenu[items[0]] == "":
            print("The submenu '" + items[0] + "' has no entries and will be ignored.");
            labelIndex +=1
            continue
        menuText += "<menu id=\"" + items[0] + "\" label=\"" + menuconfig.cats_labels[labelIndex] + "\""
        if len(getIconPath(items[1])) != 0:
            menuText += " icon=\"" + getIconPath(items[1]) + "\""
        menuText += ">"
        if items[0] == "Others":
            for index in range(len(entries)):
                if index not in matchedlist:
                    menuText += getExecLine(entries[index])
        else:
            menuText += submenu[items[0]]
        menuText += "</menu>\n"
        labelIndex +=1
    print("There were " + str(len(matchedlist)) + " entries matching the categories.");
    fp = open(os.path.expanduser("~") + "/.config/openbox/menu.xml", "r+")
    linearray = fp.read().split("\n")
    fp.seek(0)
    buf = ""
    skipText = False
    for line in linearray:
        if line == "<!-- BEGIN AUTOMENU -->":
            buf += "<!-- BEGIN AUTOMENU -->\n" + menuText
            skipText = True
        elif line == "<!-- END AUTOMENU -->":
            buf += "<!-- END AUTOMENU -->\n"
            skipText = False
        elif not skipText:
            buf += line + "\n"
    fp.write(buf)
    fp.truncate()
    fp.close()
    os.system("openbox --reconfigure")
    return

writeMenu()
