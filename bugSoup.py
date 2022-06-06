#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Github: sonicCrypt0r (https://github.com/sonicCrypt0r)


# Global Imports
from sys import stdout


# Global Variables
VERSION = "0.01"
sprint = stdout.write


# Establishes General Flow Of The Program.
def main():
    import os 

    banner()  # Prints ASCCI Art Banner For Style
    checkLinux()  # Check This Is A Linux Operating System
    checkPriv()  # Check For Root Privleges
    
    #Get Domain Name File
    sprint(pStatus("INPUT") + "Project Name: ")
    projName = input()
    sprint(pStatus("UP"))

    if not(os.path.exists(projName)):
        os.makedirs(projName)
    os.chdir(projName)

    domainEnum()
    flyOver()

    sprint("\n")

    return


def domainEnum():
    import subprocess
    import os
    import json

    if not(os.path.exists("DomainEnum")):
        os.makedirs("DomainEnum")
        os.chdir("DomainEnum")

    domains = []
    while True:
        sprint(pStatus("INPUT") + "Enter Domain: ")
        domainInput = input()
        sprint(pStatus("UP"))

        if domainInput != "exit":
            domains.append(domainInput)
        else:
            break
    
    domainList = []
    for domain in domains:
        if not(os.path.exists(domain)):
            os.makedirs(domain)
        os.chdir(domain)

        print(pStatus("GOOD") + "Amass Enmurating Domain: " + domain)
        subprocess.run(["amass", "enum", "-src", "-ip", "-brute", "-d", domain])
        subprocess.run(["amass", "viz", "-d3", "-d", domain])
        subprocess.run(["amass", "db", "-json", "domains.json", "-d", domain])
        os.system("cat domains.json | jq -r '[.domains[].names[] | {name: .name, num: .sources | length}] | sort_by(.num) | reverse | .[].name' > domains.txt")
        
        with open('domains.txt', 'r') as reader:
            curDomainList = reader.read().split("\n")
        
        for curDomain in curDomainList:
            domainList.append(curDomain)
        
        print(pStatus("GOOD") + "Pulling Domains From BufferOver: " + domain)
        os.system("curl https://dns.bufferover.run/dns?q=." + domain + " > bufferOverDomains.json")
        
        with open('bufferOverDomains.json') as f:
            bufferOverDomains = json.load(f)

        #Get RDNS Later
        if bufferOverDomains["FDNS_A"] is not None:
            for curDomain in bufferOverDomains["FDNS_A"]:
                domainList.append(curDomain.split(",")[1])

        while("" in domainList) :
            domainList.remove("")
        
        #Go Back One Directory
        os.chdir('..')

    domainListUniq = list(set(domainList))
    
    textfile = open("domainsFinal.txt", "w")
    for curDomainFinal in domainListUniq:
        textfile.write(curDomainFinal + "\n")

    os.chdir('..')

    return


def flyOver():
    import os

    if not(os.path.exists("flyover")):
        os.makedirs("flyover")

    os.system("cat DomainEnum/domainsFinal.txt | aquatone -http-timeout 9000 -scan-timeout 200 -screenshot-timeout 60000 -threads 2 -out flyover/")

    return


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
