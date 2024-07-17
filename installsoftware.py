#
# program           : InstallSoftware.py
# purpose           : Install student development environment for PRMIC and Interfacing on Windows
# author            : Nico Verduin 2020-2021
# latest change     : Migrate to Github environment from HvA Gitlab
# date              : 17-7-2024
# author            : Nico Verduin
#
import os.path          # Pathnames in Windows
import subprocess       # Call sub processes
import pathlib          # Path functions
import logging          # log
import sys              # System functions
import struct           # Structs for system info
import shutil           # Shell utilities
import distutils.spawn  # Invoke sub processes
import urllib.request   # Download file
import ssl              # Support for SSL (to disable it)
import tarfile  # Unpack TAR (Tape ARchive) file


# check locations for our programs
program_installations = [   ["7ZIP" , "C:\\Program Files\\7-Zip\\7z.exe"],
                            ["7ZIP" , "C:\\Program Files (x86)\\7-Zip\\7z.exe"],
                            ["GIT"  , "C:\\Program Files\\Git\\cmd\\git.exe"],
                            ["GIT"  , "C:\\Program Files (x86)\\Git\\cmd\\git.exe"],
                            ["CMAKE", "C:\\Program Files\\CMake\\bin\\cmake.exe"],
                            ["CMAKE", "C:\\Program Files (x86)\\CMake\\bin\\cmake.exe"]
                            ]
# Compilers and corresponding repositories to install. The name of the repo folder will be automatically stored here (index[3])
Compilers = [
                ["AVR",
                 "https://ww1.microchip.com/downloads/aemDocuments/documents/DEV/ProductDocuments/SoftwareTools/avr8-gnu-toolchain-3.7.0.1796-win32.any.x86_64.zip",
                 "https://github.com/HvA-Elektrotechniek/prmic_int.git",
                ],
                ["GCC",
                 "http://ftp.vim.org/languages/qt/development_releases/prebuilt/mingw_32/i686-7.3.0-release-posix-dwarf-rt_v5-rev0.7z",
                 "https://github.com/HvA-Elektrotechniek/gcc-voorbeelden-hva.git",
                ]
]

# additional software libraries we need to install separately
ExtraLibraries =  [
    ["PACKS", "https://packs.download.microchip.com/Microchip.ATtiny_DFP.3.0.151.atpack"],
    ["AVRDUDE", "https://github.com/avrdudes/avrdude/releases/download/v7.1/avrdude-v7.1-windows-x64.zip"]
]
# if one of these programs is not installed yet, we will install it automatically always 64 bit versions
ProgramLocations = [
    ["7ZIP" , "https://www.7-zip.org/a/7z2201-x64.exe"],
    ["GIT"  , "https://github.com/git-for-windows/git/releases/download/v2.40.1.windows.1/Git-2.40.1-64-bit.exe"],
    ["CMAKE", "https://github.com/Kitware/CMake/releases/download/v3.26.4/cmake-3.26.4-windows-x86_64.msi"]
]


# this list will be copied to a parameter file for the git installation. This seems to be the best way
# too create a silent automatic installation
GitInstallParameters = ["[Setup]",
"Lang=default",
"Dir=C:\\Program Files\\Git",
"Group=Git",
"NoIcons=0",
"SetupType=default",
"Components=ext,ext\\shellhere,ext\\guihere,gitlfs,assoc,assoc_sh,scalar",
"Tasks=",
"EditorOption=VIM",
"CustomEditorPath=",
"DefaultBranchOption=",
"PathOption=Cmd",
"SSHOption=OpenSSH",
"TortoiseOption=false",
"CURLOption=OpenSSL",
"CRLFOption=CRLFCommitAsIs",
"BashTerminalOption=MinTTY",
"GitPullBehaviorOption=Merge",
"UseCredentialManager=Enabled",
"PerformanceTweaksFSCache=Enabled",
"EnableSymlinks=Disabled",
"EnablePseudoConsoleSupport=Disabled",
"EnableFSMonitor=Disabled]"]

#########################
### F U N C T I O N S ###
#########################
# get index of installable
def get_index_of_program(program_id):
    """
    returns the index of installable programs in ProgramLocations
    :param program_id (index[0]) per entry
    :return index = -1 if fail otherwise positive index
    """
    index = -1
    for x, location in enumerate(ProgramLocations):
        if location[0] == program_id:
            index = x
            break
    return index


# check if a programma is already installed
def check_program(program, program_id):
    """
    checks if a program is installed
    :param program name with suffix
    :return full path of program or empty string
    """
    program_with_path = ""
    ProgramInPath = False
    # check if program in PATH
    executablePath = distutils.spawn.find_executable(program)
    if executablePath is not None:
        program_with_path = safepath(executablePath)
        ProgramInPath = True

    if not ProgramInPath:
        for installation in program_installations:
            if program_id  == installation[0]:
                if os.path.exists(installation[1]):
                    program_with_path = installation[1]
                    break

    return program_with_path


# download and install a program
def get_program_and_install_it(urllink, parameters, program_id):
    """
    function to download a missing program and install it
    :param urllink url o the program to be downloaded
    :param parameters array of parameters need for a silent installation
    :return path to our installed program
    """
    logger.info("Downloading from : " + urllink + " into " + parameters[0])
    # get the file size to be downloaded
    url = urllib.request.Request(urllink, method='HEAD')
    f = urllib.request.urlopen(url)
    fileSize = int(f.headers['Content-Length'])

    # start download
    urllib.request.urlretrieve(urllink, parameters[0])

    # check if file sizes are equal
    localsize = os.stat(ProgramFile).st_size

    # seems like a correct file
    if localsize == fileSize:
        logger.info("Download " + ProgramFile + " was successful")
        # now do a silent installation
        logger.info("Starting silent installation of " + parameters[0])
        # for toe install we use msiexec.exe. However a process run seems to fail so we
        # use os.system with one command statement
        if program_id == "CMAKE":
            commands_string = "msiexec /i" + parameters[0][parameters[0].rfind("/") + 1::] + " ADD_CMAKE_TO_PATH=System /qn"
            logger.info("installation command for Cmake : " + commands_string)
            # do the silent installation
            os.system(commands_string)
        else:
            process = subprocess.run(parameters,
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            data = str(process.stdout)[2:-3].replace('\\r', '').replace('\\n', '\n').splitlines()
            for line in data:
                logger.info('  ' + line)

        logger.info("silent installation of " + parameters[0] + " completed")
        os.remove(parameters[0])
        logger.info("Removed " + parameters[0])
    else:
        logger.info("Download failed")


# find where we installed the compilers
def find_directory(filename, search_path):
    """
    simple function to find the bin directories
    :param filename: name of the file we are searching for
    :param search_path: starting point
    :return bin directory
    """
    result = ""
    # Walking top-down from the root
    for root, dir, files in os.walk(search_path):
        if filename in files:
            root = root.replace("\\", "/")
            return root
    # empty result
    return result

def safepath(string):
    """
    This puts a path with blanks in a string. However currently subprocess fails
    Maybe just cancel installation as the student has to follow the instructions
    :param string: Pathname, potentially containing spaces
    :return: string in quotes if it contained spaces and did not start with a quote.
    """
    string = string.strip()
    return string


# Create our logger
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s : %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename='Install.log',
                    filemode='w')
logger = logging.getLogger()
# copy logging output to stdout
logger.addHandler(logging.StreamHandler(sys.stdout))

# get current working folder and change to forward slashes
CWD = str(pathlib.Path().absolute().resolve()) + "\\"
CWD = CWD.replace("\\", "/")

logger.info("###########################################")
logger.info("### S T A R T   I N S T A L L A T I O N ###")
logger.info("###########################################")
logger.info("")
logger.info("Running on a "+ (str(struct.calcsize("P") * 8) + " bit machine"))

# avoid SSL certificate conflicts
ssl._create_default_https_context = ssl._create_unverified_context

logger.info("")
logger.info("###################################")
logger.info("### P R E - R E Q U I S I T E S ###")
logger.info("###################################")
logger.info("")
logger.info("Verifying 7zip, git and Cmake are installed (PATH and/or elsewhere)")

# find or install GIT and 7Z

# Find git.exe (64 or 32 bit version). If not install the 64-bit version
program = "git.exe"
GitProgram = check_program(program, "GIT")
if GitProgram == "":
    logger.info("Cannot find installation of Git. Trying to download and install it")
    # download and install Git
    index_of_program = get_index_of_program("GIT")

    # url must be in list of program locations
    if index_of_program != -1:
        ProgramFile = ProgramLocations[index_of_program][1][ProgramLocations[index_of_program][1].rfind("/") + 1:]
        # We cannot find it installed so download and try to install it
        # first create a parameter file for the installation
        pathOut = CWD + "parms"
        fileOut = open(pathOut, "wt")
        for row in GitInstallParameters:
            fileOut.write(row + "\n")
        fileOut.close()

        # build our arguments list
        parameter_array = [CWD+ProgramFile, "/LOADINF=parms",
                                            "/VERYSILENT",
                                            "/SILENT"]   # process arguments
        get_program_and_install_it(ProgramLocations[index_of_program][1], parameter_array, "GIT")   # url + program arguments

        # remove parms
        os.remove("parms")
        GitProgram = check_program(program, "GIT")
    else:
        logger.info("GIT is not found in list programlocations")

# Find 7z.exe (32  or 64 bit version)
program = "7z.exe"
ZipProgram = check_program(program, "7ZIP")

if ZipProgram == "":
    logger.info("Cannot find installation of 7z. Trying to download and install it")
    # download and install 7-zip
    ProgramFile = ProgramLocations[0][1][ProgramLocations[0][1].rfind("/") + 1:]
    # We cannot find it installed so download and try to install it
    index_of_program = get_index_of_program("7ZIP")
    parameter_array = [CWD+ProgramFile, "/S", "/D=C:/Program Files/7-Zip"]  # process arguments
    get_program_and_install_it(ProgramLocations[index_of_program][1], parameter_array, "7ZIP")     # url + program arguments
    # check zip program again
    ZipProgram = check_program(program, "7ZIP")

# Find cmake.exe (64 bit version). If not install the 64-bit version
program = "cmake.exe"
CmakeProgram = check_program(program, "CMAKE")
if CmakeProgram == "":
    logger.info("Cannot find installation of Cmake. Trying to download and install it")
    # download and install Cmake
    index_of_program = get_index_of_program("CMAKE")

    # url must be in list of program locations
    if index_of_program != -1:
        ProgramFile = ProgramLocations[index_of_program][1][ProgramLocations[index_of_program][1].rfind("/") + 1:]
        # We cannot find it installed so download and try to install it
        # build our arguments list
        parameter_array = [CWD+ProgramFile, "/S"]  # process arguments
        get_program_and_install_it(ProgramLocations[index_of_program][1], parameter_array, "CMAKE")   # url + program arguments
        CmakeProgram = check_program(program, "CMAKE")
    else:
        logger.info("Cmake is not found in list programlocations")


# if still not found
if ZipProgram != "":
    logger.info("found  7z program : " + ZipProgram)
else:
    logger.info("Tried to download and install 7Z. However it failed. Aborting installation")

if GitProgram != "":
    logger.info("found GIT program : " + GitProgram)
else:
    logger.info("Tried to download and install Git. However it failed. Aborting installation")

if CmakeProgram != "":
    logger.info("found Cmake program : " + CmakeProgram)
else:
    logger.info("Tried to download and install Cmake. However it failed. Aborting installation")


if "" in [ZipProgram, GitProgram, CmakeProgram]:
    # We cannot continue
    logger.info("Required program not found. Installation aborted.")
    exit(1)

logger.info("")
logger.info("########################################################")
logger.info("### E X T R A   F I L E S   A N D  L I B R A R I E S ###")
logger.info("########################################################")
logger.info("")

# get extra libaries like PACKS

avrdude_path = ""
for Library in ExtraLibraries:
    # download the lib
    # get our local file name
    libraryName = Library[0]
    LibraryUrl  = Library[1]
    LibraryFile = LibraryUrl[LibraryUrl.rfind("/") + 1:]
    # check if the zip file is already there
    if os.path.exists(LibraryFile):
        logger.info("skipping download : " + LibraryFile + " as it already exists")
        decompressable = True
    else:
        # not here yet, so download it
        logger.info("Downloading from : " + LibraryUrl + " into " + LibraryFile)

        # get the filesize to be downloaded
        req = urllib.request.Request(LibraryUrl, method='HEAD')
        f = urllib.request.urlopen(req)
        fileSize = int(f.headers['Content-Length'])
        # start download
        urllib.request.urlretrieve(LibraryUrl, LibraryFile)
        # check if filesizes are equal
        localsize = os.stat(LibraryFile).st_size
        if localsize == fileSize:
            logger.info("Download " + LibraryFile + " was successful")
            decompressable = True
        else:
            logger.info("Download " + LibraryFile + " failed. "
                                                     "Downloaded " + localsize + ", should be " + fileSize)
            decompressable = False
            # TODO: retry the download a number of times (?)

    file_extension = LibraryFile[LibraryFile.rfind(".") + 1::]
    if file_extension == "atpack":
        # rename the pack file into a zip file and unpack it
        filebase = LibraryFile[0:LibraryFile.rfind("."):]
        os.rename(LibraryFile, filebase + ".zip")
        logger.info("Renamed " + filebase + ".atpack into " + filebase + ".zip")
        shutil.unpack_archive(filebase+".zip", filebase)
        logger.info("Unpacked " + filebase + ".zip")
        os.remove(filebase + ".zip")
        logger.info("removed" + filebase + ".zip")

    # any zip files will be unpacked here. If avrdude we need to copy
    # some files to the bin folder later on
    if file_extension == "zip":
        filebase = LibraryFile[0:LibraryFile.rfind("."):]
        shutil.unpack_archive(filebase + ".zip", filebase)
        logger.info("Unpacked " + filebase + ".zip")
        if "avrdude" in filebase:
            # save the avrdude folder name
            avrdude_path = filebase
        os.remove(filebase + ".zip")
        logger.info("removed " + filebase + ".zip")

logger.info("")
logger.info("###############################################################################")
logger.info("### D O W N L O A D I N G   C O M P I L E R S   &   R E P O S I T O R I E S ###")
logger.info("###############################################################################")
logger.info("")

for compiler in Compilers:
    # download the compiler
    # get our local file name
    compilerFile = compiler[1][compiler[1].rfind("/") + 1:]
    # add column in compiler with our BIN path name for the custom make later on
    makefileName = compilerFile[:compilerFile.rfind(".")]
    compiler.append(makefileName)
    # check if the zip file is already there
    if os.path.exists(compilerFile):
        logger.info("skipping download : " + compilerFile + " as it already exists")
        decompressable = True
    else:
        # not here yet, so download it
        logger.info("Downloading from : " + compiler[1] + " into " + compilerFile)
        # get the filesize to be downloaded
        req = urllib.request.Request(compiler[1], method='HEAD')
        f = urllib.request.urlopen(req)
        fileSize = int(f.headers['Content-Length'])
        # start download
        urllib.request.urlretrieve(compiler[1], compilerFile)
        # check if filesizes are equal
        localsize = os.stat(compilerFile).st_size
        if localsize == fileSize:
            logger.info("Download " + compilerFile + " was successful")
            decompressable = True
        else:
            logger.info("Download " + compilerFile + " failed. "
                                                     "Downloaded " + localsize + ", should be " + fileSize)
            decompressable = False
            # TODO: retry the download a number of times (?)

    # let's decompress the file if we can
    if decompressable:
        # extract in root of compilername
        foldername = compilerFile[0:compilerFile.rfind(".")]
        logger.info("Decompressing " + compilerFile + "...")
        # TODO: see if finding install directory is better choice

        process = subprocess.run(
            [ZipProgram, "x", compilerFile, "-y"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        data = str(process.stdout)[2:-3].replace('\\r', '').replace('\\n', '\n').splitlines()
        for line in data:
            logger.info('  ' + line)

        os.remove(compilerFile)
        logger.info("Remove compiler zip file: " + compilerFile)

    # get the corresponding git repository
    repoName = compiler[2][compiler[2].rfind("/") + 1:compiler[2].rfind(".")]

    print(GitProgram)
    print (compiler[2])
    print("reponame :" + repoName)

    if os.path.exists(repoName):
        logger.info("Skipping git clone. Repository " + repoName + " exists and/or is not empty.")
    else:
        logger.info("Start cloning repository " + repoName)
        process = subprocess.run([GitProgram, "clone", compiler[2]],
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        data = str(process.stdout)
        logger.info(data[2:-3])


    # change the correct cmake files as we have 2 GIT repos
    logger.info("Modify file_locations.cmake")
    pathIn = repoName + "/file_locations.cmake"
    pathOut = repoName + "/file_locations.out"
    # open input and output files
    fileIn = open(pathIn, "rt")
    fileOut = open(pathOut, "wt")
    # find correct compilerpath
    if compiler[0] == "GCC":
        compiler_path = find_directory("gcc.exe", CWD)
    else:
        compiler_path = find_directory("avr-gcc.exe", CWD)
    logger.info("compiler_path = " + compiler_path)
    # for each line in the input file
    for line in fileIn:
        # read replace the string and write to output file
        line = line.replace('MYWINDOWSPATH',  compiler_path)
        line = line.replace('MYAVRDUDEPATH',  CWD+avrdude_path)
        fileOut.write(line)
    # close input and output files
    fileIn.close()
    fileOut.close()

    # copy our new file_locations.cmake to the original
    logger.info("Copy new file to file_locations.cmake")
    shutil.copyfile(pathOut, pathIn)
    logger.info("Remove file file_locations.out")
    os.remove(pathOut)
    logger.info("Removed file file_locations.out")

logger.info("Downloaded and unpacked all Compilers")
logger.info("")
logger.info("#################################################")
logger.info("### F I N I S H E D   I N S T A L L A T I O N ###")
logger.info("#################################################")
logger.info("")
logger.info("Installation complete.\n")
