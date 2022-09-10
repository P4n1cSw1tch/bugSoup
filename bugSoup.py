#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Github: sonicCrypt0r (https://github.com/sonicCrypt0r)


# Global variables
VERSION = "0.03"


# This function establishes the general flow of the program
def main():
    from os import makedirs
    from os import path
    from os import chdir

    banner()  # Prints ASCCI Art Banner For Style
    checkLinux()  # Check This Is A Linux Operating System
    # checkPriv()  # Check For Root Privleges
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
    domainEnum()  # Perform sub domain enumartion with Amass
    flyOver()  # Perform a sub domain screenshot flyover with Aquatone
    takeOver()  # search for CNAME records for possible takeovers
    quickScan()  # use RustScan to TCP scan all ports on every subdomain

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
        # system(cmd)

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
        if curDomainList or MAX_RETRY > 4:
            if retry > 4:
                retry = 0
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

    domainList.extend(curDomainList)
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


# This function uses RustScan to TCP scan all ports on every subdomain
def quickScan():
    from os import getcwd
    from os import system
    from os import path
    from os import makedirs

    # Settings
    LIMIT_BATCH_SIZE = False
    BATCH_SIZE = 250

    # Create working path if doesn't exist
    workingPath = getcwd() + "/Quick_Scan/"
    if not (path.exists(workingPath)):
        makedirs(workingPath)

    # Location of domain list of previous domain enumertion
    domainList = "Domain_Enum/" + "Domains_Final.txt"

    # Define command arguments for RustScan
    if LIMIT_BATCH_SIZE:
        cmd = """rustscan -a '$FILE' -b $BATCH_SIZE --scan-order "Random" -r 1-65535 -- -A -sC | tee $WORKINGPATH/rustscan_out.txt"""
        cmd = cmd.replace("$BATCH_SIZE", BATCH_SIZE)
    else:
        cmd = """rustscan -a '$FILE' --scan-order "Random" -r 1-65535 -- -A -sC | tee $WORKINGPATH/rustscan_out.txt"""

    cmd = cmd.replace("$FILE", domainList)
    cmd = cmd.replace("$WORKINGPATH", workingPath)

    # Execute the scan
    printLine()
    print(pStatus("GOOD") + "RustScanning All discovered Sub-Domains...")
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


# call the main function if not an import
if __name__ == "__main__":
    main()
