import json, os, re, math
from pydriller import Repository
from clean_refactoring_output import load_commits, create_only_refactorings_file
from collections import defaultdict

def analyze_repository(repository_path, refactorings_file_path):
    """
    Analyze a repository and extract the metrics for each commit
    Input: repository_path: str
           refactorings_file_path: str
    Output: dict
    """ 
    commit_metrics = []    
    last_modification_for_file = {}
    file_pkg_data = defaultdict(lambda: defaultdict(dict))
    
    # Dictionary to store the commit dates
    commit_dates_modifs = get_commit_dates(Repository(path_to_repo=repository_path).traverse_commits())
    total_commits = len(commit_dates_modifs)

    repository = Repository(path_to_repo=repository_path).traverse_commits()  

    if not total_commits == 0:
        for i, commit in enumerate(repository):
            progress = (i+1)/total_commits*100
            if i == 0 or (total_commits >= 4 and (i+1) % (total_commits // 4) == 0) or (i+1) == total_commits:
                print(f"Processing commit {i+1}/{total_commits} ({progress:.2f}%)")
            commit_process_output = process_commit(commit,                      
                                                last_modification_for_file, 
                                                file_pkg_data,
                                                refactorings_file_path,
                                                commit_dates_modifs)        
                
            if commit_process_output:             
                commit_metrics.append(commit_process_output)         

    metrics = {
        "repository": repository_path.split(os.sep)[-1],
        "commit_metrics": commit_metrics
    }
    return metrics

def process_commit(commit,                 
                   last_modification_for_file,
                   file_pkg_data,                   
                   refactorings_file_path,
                   commit_dates_modifs):

    directories = set()
    modified_packages = set()
    
    if not is_a_refactoring_commit(commit.hash, refactorings_file_path):
        # Only add the date of the file modification if it's not a refactoring commit
        for modified_file in commit.modified_files:
            if modified_file.new_path:
                last_modification_for_file[modified_file.new_path] = commit.committer_date
                # Add the file to the file_pkg_data if it's not a deletion
                new_package = extract_package_name(modified_file.new_path)
                if new_package:
                    file_pkg_data[new_package][modified_file.new_path] = {commit.hash: {"committer": commit.author.name, "date": commit.committer_date}}                
            else:
                # remove the file from the last modification dictionary if it was deleted
                last_modification_for_file.pop(modified_file.old_path, None)
        return    
    
    modified_files = commit.modified_files

    ## NF ## Number of modified files
    NF = len(modified_files)

    ## ENTROPY ## The distribution of the modified code across each given file in the considered commit
    ENTROPY = calculate_entropy(modified_files) 

    ## FIX ## Whether or not the change is a defect fix
    FIX = bool(re.search(r'(?i)\b(?:fix(?:ed|es)?|bug(?:fix)?|patch|resolve[sd]?)\b(?:.*\b[A-Z]+-\d+\b)?', commit.msg))

    current_commit_metrics = {
        "commit": commit.hash,
        "NF": NF,
        "ENTROPY": ENTROPY,
        "ND": -1,
        "NS": -1,
        "LA": {},
        "LD": {},
        "LT": {},
        "NDEV": {},
        "FIX": FIX,
        "AGE": {},
        "NUC": {},
        "CEXP": {},
        "REXP": {},
        "SEXP": {},
    }    

    try:
        for file in modified_files:       
            process_file(file, 
                        commit,
                        directories, 
                        modified_packages, 
                        current_commit_metrics,                                                                                                                             
                        last_modification_for_file, 
                        commit_dates_modifs, 
                        file_pkg_data)
    except ValueError as e:
        print(f"Error processing commit {commit.hash}: {e}")

    ## ND ## The number of directories involved in a commit (convert to sets to remove the duplicates)      
    ND = len(directories)    
    current_commit_metrics["ND"] = ND

    ## NS ## Number of modified subsystems (convert to sets to remove the duplicates)
    NS = len(modified_packages)
    current_commit_metrics["NS"] = NS

    return current_commit_metrics

def process_file(file, 
                 current_commit,
                 directories, 
                 modified_packages, 
                 commit_metrics,                                  
                 last_modification_for_file,
                 commit_dates_modifs,
                 file_pkg_data):
    
    file_name = os.path.basename(file.new_path) if file.new_path else os.path.basename(file.old_path)+ "(deleted)"
     
    # Add the directory of the old and new paths to the set
    if file.old_path:
        directories.add(file.old_path.rsplit('/', 1)[0])
    if file.new_path:
        directories.add(file.new_path.rsplit('/', 1)[0])

    # Get the old and new package names
    old_package = extract_package_name(file.old_path)
    new_package = extract_package_name(file.new_path)

    if new_package:
        modified_packages.add(new_package)        
        # Add the package to the file_pkg_data
        file_pkg_data[new_package][file.new_path][current_commit.hash] = {"committer": current_commit.author.name, "date": current_commit.committer_date}  

    # Add both to the set (only non-null packages)
    if old_package: 
        modified_packages.add(old_package)

        if new_package and old_package != new_package:
           # There has been a package change
           # Move the commits regarding the file to the new package
              if old_package in file_pkg_data.keys():
                    if file.old_path in file_pkg_data[old_package].keys():
                        file_pkg_data[new_package][file.new_path] = file_pkg_data[old_package].pop(file.old_path)
    
    if file.new_path:
        ## LA ## The lines added to the given file in the considered commit 
        commit_metrics["LA"][file.new_path] = file.added_lines    

        ## LD ## The number of lines removed from the given file in the considered commit
        commit_metrics["LD"][file.new_path] = file.deleted_lines

        ## LT ## The number of lines of code in the given file in the considered commit before the change 
        commit_metrics["LT"][file.new_path] = len(file.source_code_before.split('\n')) if file.source_code_before else 0

        ## AGE ##The average period between the last and the current change
        # The last modification date is the last time the file was modified before the current commit. If it's the first time, it's the commit date
        last_modification_date = last_modification_for_file.get(file.new_path, commit_dates_modifs[current_commit.hash])
        commit_metrics["AGE"][file.new_path] = (commit_dates_modifs[current_commit.hash] - last_modification_date).days
       
        ## NUC ## The number of times the file has been modified up to the considered commit
        NUC = 1
        if new_package:
            NUC = len(file_pkg_data.get(new_package, {}).get(file.new_path, {})) # Since there is at least one commit (the current one)
        commit_metrics["NUC"][file.new_path] = NUC

    
        developer_set = set()
        # Count the number of different developers that changed the file
        for commit in file_pkg_data.get(new_package, {}).get(file.new_path, {}).values():            
            developer_set.add(commit["committer"])

        ## NDEV ## The number of developers that changed the modified
        commit_metrics["NDEV"][file.new_path] = len(developer_set) or 1 # Since there is at least one developer (that isn't added to the file_pkg_data yet)
        
    CEXP = 1
    REXP = 1
    for package_files in file_pkg_data.values():        
        if file.new_path in package_files.keys():
            for commit in package_files[file.new_path].values():
                if current_commit.author.name == commit["committer"]:
                    CEXP += 1
                    if (current_commit.committer_date - commit["date"]).days <= 30:
                        REXP += 1
            break

    commits_done_by_one_dev = set()
    SEXP = 1
    if new_package and new_package in file_pkg_data.keys():
        for file_details in file_pkg_data[new_package].values():
            for commit_hsh, commit_details in file_details.items():
                if current_commit.author.name == commit_details["committer"]:
                    commits_done_by_one_dev.add(commit_hsh)
        SEXP = len(commits_done_by_one_dev)

    ## CEXP ## The number of commits performed on the given file by the committer up to the considered commit
    commit_metrics["CEXP"][file.new_path] = CEXP
    ## REXP ## The number of commits performed on the given file by the committer in the last month
    commit_metrics["REXP"][file.new_path] = REXP
    ## SEXP ## The number of commits a given developer performs in the considered package containing the given
    commit_metrics["SEXP"][file.new_path] = SEXP   

def is_a_refactoring_commit(commit_hash, refactorings_file_path):
    """
    Check if a commit is a refactoring commit
    Input: commit_hash: str
              refactorings_file_path: str
    Output: bool
    """
    if not hasattr(is_a_refactoring_commit, "list_of_commits"):
        refactoring_commits = load_refactoring_commits(refactorings_file_path)
        is_a_refactoring_commit.list_of_commits = [commit['sha1'] for commit in refactoring_commits]
    
    found = commit_hash in is_a_refactoring_commit.list_of_commits
    return found

def load_refactoring_commits(refactorings_file_path):
    """
    Load all refactoring commits from a repository
    Input: refactorings_file_path: str
    Output: list
    """
    if not os.path.exists(refactorings_file_path):
        create_only_refactorings_file(os.path.dirname(refactorings_file_path))
    refactoring_commits = load_commits(refactorings_file_path)["commits"]
    print(f"Loaded refactoring commits: {len(refactoring_commits)}")
    return refactoring_commits

def calculate_entropy(modified_files):
    # Calculate the total number of lines modified in the commit
    total_lines_modified = sum(mod.added_lines + mod.deleted_lines for mod in modified_files)    
    if total_lines_modified == 0:
        return 0  # No modifications, entropy is 0
    # Calculate the proportion of changes per file
    proportions = [(mod.added_lines + mod.deleted_lines) / total_lines_modified for mod in modified_files]    
    # Apply Shannon's entropy formula
    entropy = -sum(p * math.log2(p) for p in proportions if p > 0)
    return entropy

def extract_package_name(file_path):
    """
    Given a file path, extract the package name by removing the file name 
    and converting the directory structure into a package-like format.
    """
    if file_path is None or not file_path.endswith(".java"):
        return None
    
    # Split the path into directories
    path_parts = file_path.split(os.sep)
    
    # Find the 'java' directory and extract the package part
    if 'java' in path_parts:
        java_idx = path_parts.index('java')
        # Everything after 'java' and before the file name is considered the package name
        package_parts = path_parts[java_idx + 1:-1]  # Skip the file name itself
        return ".".join(package_parts)  # Convert to package format with dots
    return None

def get_commit_dates(repository):
    commit_dates = {}    
    for commit in repository:        
        commit_dates[commit.hash] = commit.committer_date
    return commit_dates

def save_metrics(metrics, file_path):
    with open(file_path, 'w') as file:
        json.dump(metrics, file, indent=4)

def collect_process_settings():
    with open("nicolas_process_settings.json", 'r') as file:
        content = json.load(file)
        return (content["paths"]["repo_path"], 
                content["paths"]["refactoring_commits_file"], 
                content["paths"]["project_path"])
    
def full_repo_analysis(repository_path, refactorings_file_path, project_path):
    metrics = analyze_repository(repository_path, refactorings_file_path)
    project_name = repository_path.split(os.sep)[-1]
    save_metrics(metrics, os.path.join(project_path, f"{project_name}-part_2_metrics.json"))

    if hasattr(is_a_refactoring_commit, 'list_of_commits'):
        delattr(is_a_refactoring_commit, 'list_of_commits')

def main():    
    repository_path, refactorings_file_path, project_path  = collect_process_settings()    
    full_repo_analysis(repository_path, refactorings_file_path, project_path)

if __name__ == '__main__':    
    main()