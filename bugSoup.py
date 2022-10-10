#!/usr/bin/python3
# -*- coding: utf-8 -*-
# Author: Github: sonicCrypt0r (https://github.com/sonicCrypt0r)


# Global variables
VERSION = "0.036"


# This function establishes the general flow of the program
def main():
    from os import makedirs
    from os import path
    from os import chdir

    banner()        # Prints ASCCI art banner for style
    checkLinux()    # Check this is a linux operating system
    checkPriv()     # Check for root privleges
    checkDepends()  # Check dependencies are installed
    print("")

    # Get project name
    printLine()
    print(pStatus("INPUT") + "Project Name: ", end="")
    projName = input()

    # Create project directory if doesn't exist
    if not (path.exists(projName)):
        makedirs(projName)

    # Change directory to project
    chdir(projName)

    getRootDomains()  # Get root domain names from the user
    domainEnum()      # Perform sub domain enumartion with Amass
    flyOver()         # Perform a sub domain screenshot flyover with Aquatone
    takeOver()        # search for CNAME records for possible takeovers
    nucleiScan()      # use Nuclei to scan all web apps for CVEs
    #quickScan()       # use Naabu to TCP scan all ports on every subdomain

    return


# This function gets root domain names from the user
def getRootDomains():
    from os import makedirs
    from os import path
    from os import getcwd

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Domain_Enum/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    domains = []
    while True:
        print(pStatus("INPUT") + "Enter Domain: ", end="")
        domainInput = input()

        if domainInput == "exit":
            print("")
            break
        elif domainInput == "":
            pass
        elif domainInput not in domains:
            domains.append(domainInput)

    with open("scope.txt", "w") as f:
        f.write("\n".join(domains))

    return


# This function performs sub domain enumartion with Amass
def domainEnum():
    from time import sleep
    from shutil import rmtree
    from os import getcwd
    from os import system
    from os import makedirs
    from os import path
    import json

    # Settings
    RECURSION_DEPTH = 5
    ACTIVE_MODE = True
    MAX_RETRY = 4
    CUSTOM_WORD_LIST = True
    CUSTOM_WORD_LIST_PATH = (
        "/usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt"
    )

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Domain_Enum/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    with open("scope.txt") as f:
        rootDomainsRough = f.readlines()
        rootDomainsRough = list(set(rootDomainsRough))
        rootDomains = []
        for domain in rootDomainsRough:
            rootDomains.append(domain.strip())

    i = 0
    domainList = []
    retry = 0

    while i < len(rootDomains):
        domain = rootDomains[i]
        domainPath = workingPath + domain + "/"

        if not (path.exists(domainPath)):
            makedirs(domainPath)

        # Amass Enmurate
        printLine()
        print(pStatus("GOOD") + "Amass Enmurating Domain: " + domain)

        cmd = (
            "amass enum -src -ip -brute -max-depth "
            + str(RECURSION_DEPTH)
            + " -d "
            + domain
        )
        if ACTIVE_MODE:  # If active mode
            cmd += " -active"
        if CUSTOM_WORD_LIST:  # If custom wordlist
            cmd += " -w " + CUSTOM_WORD_LIST_PATH
        system(cmd)

        print(pStatus("GOOD") + "Amass Creating HTML File...")
        system(
            "amass viz -d3 -o " + domainPath + " -d " + domain
        )  # Create HTML visualizer

        """ Not Working
        print(pStatus("GOOD") + "Amass Creating JSON File...")
        system("amass db -names -silent -json " + domainPath + "domains.json" + " -d " + domain) #Create JSON File
        """

        print(pStatus("GOOD") + "Amass Creating TXT File...")
        system(
            "amass db -names -silent -o " + domainPath + "domains.txt" + " -d " + domain
        )  # Create TXT File

        # Read domains from current enmuration to curDomainList
        try:
            with open(domainPath + "domains.txt", "r") as f:
                curDomainListRough = f.readlines()
                curDomainListRough = list(set(curDomainListRough))
                curDomainList = []
                for domain in curDomainListRough:
                    curDomainList.append(domain.strip())

            with open(domainPath + "domains.txt", "w") as f:
                f.write("\n".join(curDomainList))

        except:
            print("ERROR")
            curDomainList = ""

        # If Amass was successful or max retries has been hit
        if curDomainList or retry > MAX_RETRY:
            if retry > MAX_RETRY:
                retry = 0
            else:
                domainList.extend(curDomainList)
            i += 1

        # If Amass was not successful and retries < max retries
        else:
            print(
                pStatus("BAD") + "Amass Failed To Enmurate:",
                domain,
                "Retries:",
                retry + 1,
            )
            retry += 1
            rmtree(domainPath)
            sleep(60)

    domainListUniq = list(set(domainList))

    textfile = open(workingPath + "Domains_Final.txt", "w")
    for curDomainFinal in domainListUniq:
        textfile.write(curDomainFinal + "\n")

    print("")

    return


# This function performs a sub domain screenshot flyover with Aquatone
def flyOver():
    from os import path
    from os import makedirs
    from os import system
    from os import getcwd

    # Settings
    THREADS = 2
    SCREENSHOT_TIMEOUT = 60000
    SCAN_TIMEOUT = 200
    HTTP_TIMEOUT = 9000

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Fly_Over/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    # Location of domain list of previous domain enumertion
    domainList = "Domain_Enum/" + "Domains_Final.txt"

    printLine()
    print(pStatus("GOOD") + "Aquatone Performing Flyover...")

    system(
        "cat "
        + domainList
        + " | aquatone -http-timeout "
        + str(HTTP_TIMEOUT)
        + " -scan-timeout "
        + str(SCAN_TIMEOUT)
        + " -screenshot-timeout "
        + str(SCREENSHOT_TIMEOUT)
        + " -threads "
        + str(THREADS)
        + " -out "
        + workingPath
    )

    return


# This function searchs for CNAME records for possible takeovers
def takeOver():
    from os import getcwd
    from os import path
    from os import makedirs
    from concurrent.futures import ThreadPoolExecutor
    import json

    # Settings
    MAX_THREADS = 100  # Max threads for resolving DNS records

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Take_Over/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    # Read sub domains from previous enumeration into a list
    with open("Domain_Enum/Domains_Final.txt", "r") as reader:
        domainList = reader.read().split("\n")

    resolvedDict = []
    for domain in domainList:
        resolvedDict.append(
            {
                "domain": domain,
                "CNAME": None,
            }
        )

    printLine()
    print(pStatus("GOOD") + "Searching For CNAME Records...")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
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
        if pair["CNAME"] != False:
            finalCNAMES.append(pair)
            if not (
                pair["CNAME"].split(".")[-2] == pair["domain"].split(".")[-2]
                and pair["CNAME"].split(".")[-1] == pair["domain"].split(".")[-1]
            ):
                crossDomainCNAMES.append(pair)

    print("\nCNAMES:")
    for name in finalCNAMES:
        print(name)

    print("\nCROSS-DOMAIN CNAMES:")
    for name in crossDomainCNAMES:
        print(name)

    json_object = json.dumps(finalCNAMES, indent=4)
    with open(workingPath + "CNAMES.json", "w") as outfile:
        outfile.write(json_object)

    json_object = json.dumps(crossDomainCNAMES, indent=4)
    with open(workingPath + "takeovers.json", "w") as outfile:
        outfile.write(json_object)

    print("")

    return


# This funtion takes a subdomain and checks for a CNAME record
def getCNAME(domain):
    import dns.resolver
    from time import sleep

    # Settings
    RESOLVER_LIST = [
        "8.8.8.8",
        "9.9.9.9",
        "208.67.222.222",
        "1.1.1.1",
        "185.228.168.9",
        "76.76.19.19",
        "94.140.14.14",
        "4.0.0.53",
    ]  # List of domain resolvers IPs

    my_resolver = dns.resolver.Resolver()
    my_resolver.nameservers = RESOLVER_LIST

    try:
        answers = my_resolver.resolve(domain, "CNAME")
        for data in answers:
            answer = str(data)
    except:
        print("No CNAME For:", domain)
        return False

    if answer[-1] == ".":
        answer = answer[:-1]
    print("Resolved:", domain, "-->:", answer)

    return answer


# This function uses Naabu to TCP scan all ports on every subdomain
def quickScan():
    from os import getcwd
    from os import system
    from os import path
    from os import makedirs

    # Settings
    RATE = 1000
    THREADS = 25
    NMAP_SPEED = 2

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Quick_Scan/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    # Location of domain list of previous domain enumertion
    domainList = "Domain_Enum/" + "Domains_Final.txt"

    # Define command arguments for Naabu
    cmd = "naabu -p - -list $FILE -rate $RATE -scan-all-ips -c $THREADS -nmap-cli 'nmap -O -T$NMAP_SPEED -sV -oX nmap-output' | tee $WORKINGPATH/quickscan.txt"
    cmd = cmd.replace("$RATE", str(RATE))
    cmd = cmd.replace("$FILE", domainList)
    cmd = cmd.replace("$THREADS", str(THREADS))
    cmd = cmd.replace("$NMAP_SPEED", str(NMAP_SPEED))
    cmd = cmd.replace("$WORKINGPATH", workingPath)

    # Let user know starting the scan
    printLine()
    print(pStatus("GOOD") + "Naabu Scanning All discovered Sub-Domains...")
    
    # Execute the scan
    system(cmd)

    return


# This function uses Nuclei to CVE scan previously discovered web apps
def nucleiScan():
    from os import getcwd
    from os import system
    from os import path
    from os import makedirs

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Nuclei_Scan/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    # Location of domain list of previous domain enumertion
    URLList = "/Fly_Over/aquatone_urls.txt/"

    # Define command arguments for Naabu
    cmd = "nuclei -tags cve -u $URLLIST | tee $WORKINGPATHnuclei.txt"
    cmd = cmd.replace("$URLLIST", URLList)
    cmd = cmd.replace("$WORKINGPATH", workingPath)

    # Execute the scan
    printLine()
    print(pStatus("GOOD") + "Nuclei Scanning All discovered web applications...")
    system(cmd)

    return


# This function prints banner art for sweet style
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
    print("")
    printLine()

    return


# This function makes sure it is running on a Linux operating system
def checkLinux():
    from platform import system

    # If the OS is not Linux exit the program
    os = system()
    if os != "Linux":
        print(pStatus("BAD") + "Operating System Is Not Linux Value: " + os)
        exit(1)  # Exit With Error Code

    print(pStatus("GOOD") + "Operating System Is Linux Value: " + os)

    return


# This function checks if the script has root privleges
def checkPriv():
    from os import geteuid

    euid = geteuid()

    # If the effective user ID is not 0 (not root)
    if euid != 0:
        print(
            pStatus("BAD")
            + "This Script Does Not Have Root Privledges EUID: "
            + str(euid)
        )
        exit(1)  # Exit With Error Code

    print(pStatus("GOOD") + "This Script Has Root Privledges EUID: " + str(euid))

    return


# This function is for fancy output throughout the program
def pStatus(status):
    # Colors used for fancy output
    COLORS = {
        "WARN": "\033[93m",  # Yellow
        "GOOD": "\033[92m",  # Green
        "BAD": "\033[91m",  # Red
        "INPUT": "\033[96m",  # Blue
        "ENDC": "\033[0m",  # White
        "UP": "\033[F",  # This Goes Up A Line
    }

    # Select color/prefix based on status
    if status == "GOOD":
        prefix = COLORS["ENDC"] + "[" + COLORS["GOOD"] + "+" + COLORS["ENDC"] + "] "
    elif status == "BAD":
        prefix = COLORS["ENDC"] + "[" + COLORS["BAD"] + "+" + COLORS["ENDC"] + "] "
    elif status == "WARN":
        prefix = COLORS["ENDC"] + "[" + COLORS["WARN"] + "+" + COLORS["ENDC"] + "] "
    elif status == "INPUT":
        prefix = COLORS["ENDC"] + "[" + COLORS["INPUT"] + "+" + COLORS["ENDC"] + "] "
    elif status == "UP":
        prefix = COLORS["UP"]

    return prefix


# This function prints a line that goes across the terminal screen
def printLine():
    from os import get_terminal_size

    columns, rows = get_terminal_size(0)
    print("=" * columns)  # Print line

    return


# This function checks dependencies and terminates if not found
def checkDepends():
    from sys import version_info
    from shutil import which
    from os import path

    apps = ['amass', 'aquatone', 'naabu', 'nmap', 'nuclei', 'tee']

    if version_info[0] <= 3 and version_info[1] <= 6:
        print(
            pStatus("BAD")
            + "This Script Was Designed For Python Version 3.6 or Greater"
        )
        exit(1)  # Exit With Error Code

    for app in apps:
        if which(app) is None:
            print(pStatus("BAD") + "Your System Is Missing:", app)
            exit(1)  # Exit With Error Code

    if not(path.exists("/usr/share/seclists/")):
        print(pStatus("BAD") + "Your System Is Missing: SecLists")
        exit(1)  # Exit With Error Code

    try:
        import dns.resolver

    except:
        print(pStatus("BAD") + "Your System Is Missing Python3 Pip 'dns.resolver'")
        exit(1)  # Exit With Error Code

    print(pStatus("GOOD") + "Checking Dependencies Status: Good")

    return


# call the main function if not an import
if __name__ == "__main__":
    main()
