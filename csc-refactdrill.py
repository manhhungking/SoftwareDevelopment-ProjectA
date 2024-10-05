# Imports
import json
import shutil
import stat
import subprocess   # For executing external commands
import threading    # For creating and managing threads
import os           # For interacting with the operating system
import time         # For time-related functions

from pydriller import Repository # For extracting commit information

# Path to the RefactoringMiner executable
miner = os.getenv('REFMINER_PATH')
# Root directory where Git repositories will be cloned
git_root = os.getenv('GIT_REPOS_ROOT', '../repos')
# Max number of threads to run concurrently from $SLURM_CPUS_PER_TASK
max_threads = int(os.getenv('NUM_THREADS', '1'))

def collect_refactoring_commits(link):
    # Extract the folder name from the link (repository name)
    folder = link.split('/')[-1].split('.')[0]
    # Create the full path for the cloned repository
    path = git_root+"/"+folder
    # Define RefactoringMiner output file
    output_file = './' + folder + '/refactorings.json'

    try:
        # Load refactoring file
        with open(output_file, 'r') as file:
            try:
                refactorings = json.load(file)
            except json.JSONDecodeError as e:
                print(f'Error loading JSON from file: {output_file}')
                print(f'Error message: {e.msg}')
                print(f'Error at line {e.lineno}, column {e.colno}')
                return
    except FileNotFoundError:
        print('Error reading file:', output_file)
        return

    # Get all commits with refactoring activity
    refactoring_commits = []
    for commit in refactorings['commits']:
        if commit['refactorings']:
            refactoring_commits.append(commit['sha1'])

    # Get all commits from repo
    all_commits = []
    for commit in Repository(path).traverse_commits():
        all_commits.append(commit)

    # Get all commits with refactoring activity
    commits = []
    for index, hash1 in enumerate(refactoring_commits):
        for commit in all_commits:
            if commit.hash == hash1:
                communist = {
                    'commit_hash': commit.hash,
                    'previous_commit_hash': commit.parents[0] if commit.parents else None,
                    'commit_message': commit.msg,
                    'added_lines': 0,
                    'deleted_lines': 0,
                    'diff': {}
                }
                stats = []
                for m in commit.modified_files:
                    path = ""
                    try:
                        path = m.new_path.replace('\\', '/')
                    except:
                        path = m.old_path.replace('\\', '/')

                    communist['diff'][path] = {
                        'diff': m.diff,
                        'added_lines': m.added_lines,
                        'deleted_lines': m.deleted_lines
                    }
                    communist['added_lines'] += m.added_lines
                    communist['deleted_lines'] += m.deleted_lines
                    try:
                        stats.append("{:<8}".format(str(m.added_lines)) + "{:<8}".format(str(m.deleted_lines)) + path)
                    except:
                        pass

                communist['diff_stats'] = '\n'.join(stats)
                commits.append(communist)

    # Write refactoring commits to file
    with open('./' + folder + '/commits.json', 'w') as file:
        json.dump(commits, file, indent=2)


def getlinks(file_path):
    # Initialize an empty list to store links
    links = []
    # Open the specified file in read mode
    with open(file_path, mode='r') as file:
        # Read all lines from the file
        lines=file.readlines()
        # Iterate over each line
        for line in lines:
            # Remove whitespace and add to the links list
            links.append(line.strip())
    return links # Return the list of links

def clone_repo(link):
    # Extract the folder name from the link (repository name)
    folder = link.split('/')[-1].split('.')[0]
    # Create the full path for the cloned repository
    path = git_root+"/"+folder

    # Check if the repository folder already exists
    if not os.path.exists(path):
        # Clone the repository if it does not exist
        subprocess.call(["git", "clone", link, path])

def refactoring_miner(link):
    # Extract the folder name from the link (repository name)
    folder = link.split('/')[-1].split('.')[0]
    # Create the full path for the cloned repository
    path = git_root+"/"+folder
    
    # Check if the folder for storing refactorings exists
    if not os.path.exists(folder):
        # Create the folder if it does not exist
        os.mkdir(folder)

    # Check if the refactorings.json file has already been created
    if not os.path.exists(folder+"/done"):
        if os.path.exists(folder + "/refactorings.json"):
            os.remove(folder+"/refactorings.json")
        # Run the RefactoringMiner tool and output to refactorings.json
        subprocess.call([miner, "-a", path, "-json", folder+"/refactorings.json"])
        # Create an empty file to indicate that the refactorings have been extracted
        open(folder+"/done", 'a').close()

def run_thread(link):
    print("Thread started for", link)
    refactoring_miner(link)
    print("RefactoringMiner completed for", link)
    collect_refactoring_commits(link)
    print("Commits collected for", link)
    # Remove the repository folder after processing
    folder = link.split('/')[-1].split('.')[0]
    path = git_root+"/"+folder
    # Remove the repository folder after processing (linux)
    try:
        def remove_readonly(func, path, _):
            "Clear the readonly bit and reattempt the removal"
            os.chmod(path, stat.S_IWRITE)
            func(path)

        shutil.rmtree(path, onerror=remove_readonly)
    except Exception as e:
        print("Error removing repository", e)
    print("Thread completed for", link)

def main():
    # Path to the file containing project links
    file_path = 'projects.txt'
    threads = [] # List to hold threads
    # Retrieve the list of links from the file
    links = getlinks(file_path)

    # Iterate through each link
    for link in links:
        while threading.active_count() > max_threads:
            time.sleep(0.1)

        # Clone the repository
        clone_repo(link)
        # Create a new thread for processing each link
        t = threading.Thread(target=run_thread, args=(link,))
        threads.append(t) # Add the thread to the list
        t.start() # Start the thread
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
        
# Entry point of the script
if __name__ == "__main__":
    main()