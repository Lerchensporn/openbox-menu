#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2011 woho
# Copyright (c) 2013 Lara Maia <lara@craft.net.br>
#
# Obmenu is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import menuconfig
import logging

def replaceSymbols(text):
    dic = { "%U":"", "%u":"",
            "%F":"", "%f":"",
            "&":"amp;",
          }

    for i, o in dic.items():
        text = text.replace(i, o)
    return text

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
                entry["Exec"] = replaceSymbols(entry["Exec"]).strip()
                entry["Name"] = replaceSymbols(entry["Name"])
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
    logging.info("Parsing .desktop files")
    entries = parseDeskFiles()
    logging.debug("Found %d entries.", len(entries))

    # loop through categories
    logging.info("Scanning categories")
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
    logging.info("Scanning submenus")
    menuText = ""
    labelIndex = 0
    for items in menuconfig.cats:
        if items[0] in submenu and submenu[items[0]] == "":
            logging.warning("The submenu '%s' has no entries and will be ignored.", items[0]);
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
    logging.debug("There were %d entries matching the categories.", len(matchedlist));
    logging.info("Writing new menu")

    try:
        fp = open(os.path.expanduser("~") + "/.config/openbox/menu.xml", "r+")
    except:
        logging.error("Cannot open menu file")
        return

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
    logging.info("Reconfiguring openbox")
    os.system("openbox --reconfigure")
    return

if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
    obmenu = writeMenu()
