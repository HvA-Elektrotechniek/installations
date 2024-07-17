# Installations

This is a python script that enables a complete installation for the VSCode environment for AVR projects and Native projects both under Windows.

# Requirements
You need the following software packages installed
- VSCode

Any missing software packages will be installed automatically

# Fast installation under Windows
1. create a subdirectory (preferably close tot the root) (i.e. c:/school) **DO NOT USE ANY SPACES in the directory name**
2. Just download the installsoftware.exe and put it into the empty directory just created. 
3. go to the folder with installsoftware.exe (just uses Windows explorer)
4. Double-click on i**nstallSoftwware.exe** and click **yes** when asked and wait a few minutes until done
5. 6 directories are created and a install.log file showing progress

# Rebuild of installsoftware.exe
If you have no idea what the below means... skip it

1. you need to have installed **python**
2. if not done yet, install pyinstaller : **pip install pyinstaller**
3. in the folder containing the python file to be converted using a CMD box type: **pyinstaller -F --uac-admin pyton file name.py**
4. Your executable will be in a created **dist** sub-folder

# Atmel drivers missing
In the event that the system does not recognize the XMega board. The drivers are probably missing. In that case download from this repository **driver-atmel-installer-x64-7.0.1645.msi** and double click on it. The problem should be solved.
