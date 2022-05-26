NOTE:
If the name of this file is "monaco-$account$-README.txt" it means you need to deobfuscate the folder.  You will need to ask the author for instructions on how to do this if you have not already received them.

There is a monaco directory that contains the "base monaco" executables and batch files that set the URLs and Tokens.

The monaco directory should be added to the Windows Path to allow monaco to be called from any subdirectory.

There are two directories per tenant.  One is for downloads and one is for updates (deploys).

For downloads, just run the batch file in the download directory.
Example: monaco-$TENANT3$-DOWNLOAD\monaco-download-$tenant3$.bat

Just make sure the folders, JSON and YAML files you expect were downloaded.  Checking the logs is really only necessary when it does not work as expected.

For updates, copy the yaml and contents you need to the updates directory and run the batch file.
Example: 
monaco-$TENANT3$-UPDATE\monaco-UPDATE-$tenant3$.bat
$tenant3$-tenant should contain ONLY the contents that need to be deployed.
Remove any other sub-directories, references from the yaml file(s) and any JSON files not being deployed.

Check the log after each update and look for "Deployment finished without errors" near the bottom of log.

