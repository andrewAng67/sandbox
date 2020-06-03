<!-- Version 1.1  -->
# Git CheatSheet 
 ### Copying a repo
 * SSH
	 * Click here to setup [here](https://help.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh) on your computer
	 * Copy and paste the **SSH** key from the [Clone&Download] button on the repo into your terminal 
	 * Follow the instructions on the screen, and you should be set

### Branches
* Think of it as opening different sections of the same repo, one independent after another 
* Each repo is independent, unless when we specify that we want to interact with one another (via *$ git merge*, etc.) 
git checkout -b [new_branch_name] # Create a new branch and switch to it
git branch # List all current branches
git checkout [branch_name]  # Switch to an existing branch
 ```

 ### Note
 - When adding a fresh repo with multiple branches, use this command to see all of the branches
 - Since branches would be hidden at first
 ``` bash
 git checkout -a # Sees all branches, remote and local to you
 ```

### Making a Commit
* Uploading a change from our local machine's version of the branch to the cloud/online  version of the branch
``` bash
git add [files_to_commit] # Stage (Preparing the files we wanna update)
git commit -m "<Message you wanna use>" 
git push # Push -> sending the whole file and msg to Git
```

### Pulling
* Updating the local version of branch with the one present in the cloud
``` bash
git pull # Be in your branch that you wanna update
```
### Merge 
* Takes the files from one branch and adds them / changes the files that match in another branch
* Normally, we merge from *working* to *master* branch

``` bash
git merge <target> 
# Target - Source branch
# Current Branch - Destination Branch
```
