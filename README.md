## Repo for Microsoft Windows and Linux ##

**State: Testing.** Please do not use for productive projects yet!

This is E.S.R.Labs Repo - just like Google Repo but this one also runs under Microsoft Windows.
For more information, see [Version Control with Repo and Git](http://source.android.com/source/version-control.html).

Repo is a repository management tool that Google built on top of Git. Repo unifies many Git repositories when necessary,
does the uploads to a revision control system, and automates parts of the development workflow.
Repo is not meant to replace Git, only to make it easier to work with Git in the context of multiple repositories.
The repo command is an executable Python script that you can put anywhere in your path.
In working with the source files, you will use Repo for across-network operations.
For example, with a single Repo command you can download files from multiple repositories into your local working directory.


### Setup steps for Microsoft Windows ###

##### Fix priviledges to allow for creation of symbolic links #####
* If you are a member of the Administrators group you have to [turn off User Access Control (UAC)](http://windows.microsoft.com/en-us/windows7/turn-user-account-control-on-or-off) and then restart the computer.
* Otherwise you have to adjust your user rights to [get SeCreateSymbolicLinkPrivilege priviledges](http://stackoverflow.com/questions/6722589/using-windows-mklink-for-linking-2-files).
The editrights tools is provided as part of git-repo for Microsoft Windows.

* **Highly experimental (do not use except for developing this feature!):** If you prefer to not use symbolic links but junctions for folders and hardlinks for files instead, you have to set the following in your ~/.gitconfig:

        [portable]
            windowsNoSymlinks = true

    This will not require to set the the priviledges as described above.

    **Known issue:** Hard links are destroyed by git for example when you delete a branch (breaks .git/config). This will destroy the project workspace!

##### Download and install Git #####
* Download [Git (http://git-scm.com/downloads)](http://git-scm.com/downloads)
* Add Git to your path environment variable: e.g. C:\Program Files (x86)\Git\cmd;
* Add MinGW to your path environment variable: e.g. C:\Program Files (x86)\Git\bin;

##### Download and install Python #####
* Download [Python 2.7+ (https://www.python.org/downloads/)](https://www.python.org/downloads/)
* Add Python to your path environment variable: e.g. C:\Python27;
* Note: Python 3.x is supported on an experimental bases by git-repo

##### Download and install Repo either using the Windows Command Shell or Git Bash #####
###### Windows Command Shell ######

    md %USERPROFILE%\bin
    curl https://raw.githubusercontent.com/esrlabs/git-repo/stable/repo > %USERPROFILE%/bin/repo
    curl https://raw.githubusercontent.com/esrlabs/git-repo/stable/repo.cmd > %USERPROFILE%/bin/repo.cmd

###### Git Bash ######

    mkdir ~/bin
    curl https://raw.githubusercontent.com/esrlabs/git-repo/stable/repo > ~/bin/repo
    curl https://raw.githubusercontent.com/esrlabs/git-repo/stable/repo.cmd > ~/bin/repo.cmd

* Add Repo to your path environment variable: %USERPROFILE%\bin;
* Create a HOME environment variable that points to %USERPROFILE% (necessary for OpenSSH to find its .ssh directory).
* Create a GIT_EDITOR environment variable that has an editor executable as value. For this, first add the home directory of the editor executable to the path environment variable. GIT_EDITOR can than be set to "notepad++.exe", "gvim.exe", for example.

### Setup steps for Linux ###

##### Downloading and installing Git and Python #####

    sudo apt-get install git-core
    sudo apt-get install python

##### Download and install Repo #####

    $ mkdir ~/bin
    $ PATH=~/bin:$PATH
    $ curl https://raw.githubusercontent.com/esrlabs/git-repo/stable/repo > ~/bin/repo
    $ chmod a+x ~/bin/repo

### Usage ###

For more detailed instructions regarding git-repo usage, please visit [git-repo](http://source.android.com/source/version-control.html).


### Changes to original git-repo ###

##### Portable changes #####

* Added Windows executable repo.cmd
* Replacing usage of fcntl with sockets for Windows
* Handling pager and coloring with subprocesses and redirects of sysin, sysout and syserr on Windows
* Using mklink to create symbolic links on Windows (alternative: use junctions and hardlinks by setting `portable.windowsNoSymlinks = true` in ~/.gitconfig)
* fixed some file handling issues / differences

##### New Features #####

* Added push.py sub command to upload and bypass the code review system.
* Added interactive workflow test