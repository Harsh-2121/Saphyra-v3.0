# Saphyra-v3.0
The legendary DDoS tool Saphyra back again with version 3.0. Official full public release included with bug fixes, compatibility with Python 3.11 and code optimization.

# What is Saphyra?
Saphyra is a extremely powerful DDoS tool used for pentesting.This thing can bring down major websites! ONLY USE THIS TOOL FOR ETHICAL PURPOSES!!!

# New stuff and bug fixes

Urllib2 Issue-
As the library urllib2 is not supported in Python 3.11, it has been changed to urllib.parse. This works the same way but is supported.

Parantheses Missing Error-
Weirdly, in the last version of Saphyra, in the HTML URL read part, there have been missing parantheses. We have fixed this.

Comparision Syntax Error:
The line "if (previous+100<request_counter) & (previous<>request_counter):" has been deprecated in Python 3.11 and has been replaced.

# How to run the tool

First, copy the URL to git clone it. Then navigate to the directory. Open the terminal or CMD there. Type pip install -r requirements.txt. Then type python3 saphyra.py [ URL ]. Type your victim's URL without the squre bracket in the place of [ URL ]. Your target website is dead!

Thats all! Enjoy hacking(ethically, of course)!
