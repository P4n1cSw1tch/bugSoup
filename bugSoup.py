#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Github: sonicCrypt0r (https://github.com/sonicCrypt0r)


# Global Imports
from sys import stdout


# Global Variables
VERSION = "0.02"
sprint = stdout.write


# Establishes General Flow Of The Program.
def main():
    import os 

    banner()  # Prints ASCCI Art Banner For Style
    checkLinux()  # Check This Is A Linux Operating System
    #checkPriv()  # Check For Root Privleges
    
    #Get Project Name
    sprint(pStatus("INPUT") + "Project Name: ")
    projName = input()
    sprint(pStatus("UP"))

    #Create Project Directory If Doesn't Exist
    if not(os.path.exists(projName)):
        os.makedirs(projName)

    domainEnum(projName)
    flyOver(projName)
    takeOver(projName)

    sprint("\n")

    return


def domainEnum(projName):
    import time
    import subprocess
    import os
    import json

    workingPath = projName + "/DomainEnum"+ "/"

    if not(os.path.exists(workingPath)):
        os.makedirs(workingPath)

    domains = []
    while True:
        sprint(pStatus("INPUT") + "Enter Domain: ")
        domainInput = input()
        sprint(pStatus("UP") + pStatus("UP"))

        if domainInput == "exit":
            break
        elif domainInput == "":
            pass
        else:
            domains.append(domainInput)
    
    domainList = []
    for domain in domains:
        time.sleep(60)
        domainPath = workingPath + domain + "/"

        if not(os.path.exists(domainPath)):
            os.makedirs(domainPath)

        print(pStatus("GOOD") + "Amass Enmurating Domain: " + domain)
        subprocess.run(["amass", "enum", "-src", "-ip", "-active", "-max-depth", "3", "-brute", "-d", domain])
        subprocess.run(["amass", "viz", "-d3", "-o", domainPath, "-d", domain])
        subprocess.run(["amass", "db", "-json", domainPath + "domains.json", "-d", domain])
        os.system("cat " + domainPath + "domains.json | jq -r '[.domains[].names[] | {name: .name, num: .sources | length}] | sort_by(.num) | reverse | .[].name' > " +  domainPath + "domains.txt")
        
        with open(domainPath + "domains.txt", 'r') as reader:
            curDomainList = reader.read().split("\n")
        
        for curDomain in curDomainList:
            domainList.append(curDomain)
        
        
        ''' Bufferover Run Currently Not Working
        print(pStatus("GOOD") + "Pulling Domains From BufferOver: " + domain)
        os.system("curl https://dns.bufferover.run/dns?q=." + domain + " > " + domainPath + "bufferOverDomains.json")
        
        with open(domainPath + "bufferOverDomains.json") as f:
            bufferOverDomains = json.load(f)

        #Get RDNS Later
        if bufferOverDomains["FDNS_A"] is not None:
            for curDomain in bufferOverDomains["FDNS_A"]:
                domainList.append(curDomain.split(",")[1])
        '''

        while("" in domainList) :
            domainList.remove("")

    domainListUniq = list(set(domainList))
    
    textfile = open(workingPath + "domainsFinal.txt", "w")
    for curDomainFinal in domainListUniq:
        textfile.write(curDomainFinal + "\n")

    return


def flyOver(projName):
    import os

    workingPath = projName + "/flyover"
    if not(os.path.exists(workingPath)):
        os.makedirs(workingPath)

    domainList = projName + "/DomainEnum/domainsFinal.txt"

    os.system("cat " + domainList + " | aquatone -http-timeout 9000 -scan-timeout 200 -screenshot-timeout 60000 -threads 2 -out " + workingPath)

    return


def takeOver(projName):
    import os
    from concurrent.futures import ThreadPoolExecutor
    import json

    workingPath = projName + "/takeover/"

    if not(os.path.exists(workingPath)):
        os.makedirs(workingPath)
 
    with open(projName + '/DomainEnum/domainsFinal.txt', 'r') as reader:
        domainList = reader.read().split("\n")

    resolvedDict = []
    for domain in domainList:
        resolvedDict.append({
                            'domain' : domain,
                            'CNAME'  : None,
                            })

    with ThreadPoolExecutor(max_workers = 100) as executor:
        results = executor.map(getCNAME, domainList)

    
    CNAMES = []
    for result in results:
        CNAMES.append(result)
    
    i = 0
    while i < len(CNAMES):
        resolvedDict[i]["CNAME"] = CNAMES[i]
        i += 1

    finalCNAMES = []
    crossDomainCNAMES = []

    for pair in resolvedDict:
        if (pair["CNAME"] != False):
            finalCNAMES.append(pair)
            if not(pair["CNAME"].split('.')[-2] == pair["domain"].split('.')[-2] and pair["CNAME"].split('.')[-1] == pair["domain"].split('.')[-1]):
                crossDomainCNAMES.append(pair)


    print("\nCNAMES:")
    for name in finalCNAMES:
        print(name)


    print("\nCROSS-DOMAIN CNAMES:")
    for name in crossDomainCNAMES:
        print(name)

    json_object = json.dumps(finalCNAMES, indent = 4)
    with open(workingPath + "CNAMES.json", "w") as outfile:
        outfile.write(json_object)

    json_object = json.dumps(crossDomainCNAMES, indent = 4)
    with open(workingPath + "takeovers.json", "w") as outfile:
        outfile.write(json_object)

    return


def getCNAME(domain):
    import dns.resolver
    import time

    time.sleep(1)

    my_resolver = dns.resolver.Resolver()
    my_resolver.nameservers = ['8.8.8.8', '9.9.9.9', '208.67.222.222', '1.1.1.1', '185.228.168.9', '76.76.19.19', '94.140.14.14', '4.0.0.53']

    try:
        answers = my_resolver.resolve(domain, 'CNAME')
        for data in answers:
            answer = str(data)
    except dns.resolver.NoAnswer:
        print("No CNAME For:", domain)
        return False
    except dns.resolver.NXDOMAIN:
        print("No CNAME For:", domain)
        return False

    if answer[-1] == ".":
        answer = answer[:-1]
    print("Resolved:", domain, "-->:", answer)

    return answer

    


# This Function Prints ASCCI Art Banner For Style
def banner():
    banner = r"""                                                                           
 ______            _______    _______  _______           _______ 
(  ___ \ |\     /|(  ____ \  (  ____ \(  ___  )|\     /|(  ____ )        \   /
| (   ) )| )   ( || (    \/  | (    \/| (   ) || )   ( || (    )|        .\-/.
| (__/ / | |   | || |        | (_____ | |   | || |   | || (____)|    /\ ()   ()
|  __ (  | |   | || | ____   (_____  )| |   | || |   | ||  _____)   /  \/~---~\.-~^-.
| (  \ \ | |   | || | \_  )        ) || |   | || |   | || (      .-~^-./   |   \---.
| )___) )| (___) || (___) |  /\____) || (___) || (___) || )           {    |    }   \
|/ \___/ (_______)(_______)  \_______)(_______)(_______)|/        .  -~\   |   /~-.
                   VERSION: {VERSION}                                   /    \  A  /    \
                   BY: sonicCrypt0r                                      \   /        
                                                                         \/ \/"""
    print(banner.replace("{VERSION}", VERSION))

    return


def checkLinux():
    from platform import system

    os = system()

    if os != "Linux":
        sprint(pStatus("BAD") + "Operating System Is Not Linux Value: " + os + "\n")
        exit(1)  # Exit With Error Code

    sprint(pStatus("GOOD") + "Operating System Is Linux Value: " + os)

    return


def checkPriv():
    from os import geteuid

    euid = geteuid()

    if euid != 0:
        sprint(
            pStatus("BAD")
            + "This Script Does Not Have Root Privledges EUID: "
            + str(euid)
            + "\n"
        )
        exit(1)  # Exit With Error Code

    sprint(pStatus("GOOD") + "This Script Has Root Privledges EUID: " + str(euid))

    return


# This Function Is For Fancy Output Throughout The Program
def pStatus(status):
    # Colors Used For Fancy Output
    COLORS = {
        "WARN": "\033[93m",  # Yellow
        "GOOD": "\033[92m",  # Green
        "BAD": "\033[91m",  # Red
        "INPUT": "\033[96m",  # Blue
        "ENDC": "\033[0m",  # White
        "UP": "\033[F",  # This Goes Up A Line
    }

    # Select Color/Prefix Based On "status"
    if status == "GOOD":
        prefix = (
            "\n" + COLORS["ENDC"] + "[" + COLORS["GOOD"] + "+" + COLORS["ENDC"] + "] "
        )
    elif status == "BAD":
        prefix = (
            "\n" + COLORS["ENDC"] + "[" + COLORS["BAD"] + "+" + COLORS["ENDC"] + "] "
        )
    elif status == "WARN":
        prefix = (
            "\n" + COLORS["ENDC"] + "[" + COLORS["WARN"] + "+" + COLORS["ENDC"] + "] "
        )
    elif status == "INPUT":
        prefix = (
            "\n" + COLORS["ENDC"] + "[" + COLORS["INPUT"] + "+" + COLORS["ENDC"] + "] "
        )
    elif status == "UP":
        prefix = COLORS["UP"]

    return prefix


# This Calls The Main Function.
if __name__ == "__main__":
    main()
