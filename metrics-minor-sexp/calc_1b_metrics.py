from collections import defaultdict
import math
import os, subprocess, time
from pydriller import Repository
from scipy.stats.mstats import gmean

from clean_refactoring_output import create_only_refactorings_file, load_commits
from calc_2_metrics import collect_process_settings, is_a_refactoring_commit, save_metrics

def process_repo(repository_path, refactorings_file_path):
    commit_metrics = []


    # Structure: {file_path: [{developer: count}]}
    dev_commit_count_per_file = {}

    # Structure: {file_path: {developers :{developer1: [commit_date1, commit_date2, ...],
    #                                      developer2: [commit_date1, commit_date2, ...]},
    #             creation_date: datetime,
    #             last_refactor_date: datetime},
    #                       } 
    dev_commit_per_file = {}
    
    all_commits = [c for c in Repository(path_to_repo=repository_path).traverse_commits()]
    total_commits = len(all_commits)
    repository = Repository(path_to_repo=repository_path).traverse_commits() 

    EXP = calculate_exp(repository_path)      
    print(f"EXP: {EXP}")
    
    if not total_commits == 0:
        for i, commit in enumerate(repository):
            progress = (i+1)/total_commits*100
            if i == 0 or (total_commits >= 4 and (i+1) % (total_commits // 4) == 0) or (i+1) == total_commits:
                print(f"Processing commit {i+1}/{total_commits} ({progress:.2f}%)")
            commit_process_output = process_commit(commit,                                                   
                                                   refactorings_file_path,
                                                   repository_path,
                                                   dev_commit_count_per_file,
                                                   dev_commit_per_file)                
            if commit_process_output:             
                commit_metrics.append(commit_process_output) 

    metrics = {
        "repository": repository_path.split(os.sep)[-1],
        "commit_metrics": commit_metrics,
        "EXP":EXP
    }
    return metrics    


def process_commit(commit,                                     
                   refactorings_file_path,
                   repository_path,
                   dev_commit_count_per_file,
                   dev_commit_per_file):
    
    for mod in commit.modified_files:
        # If a file was moved, we need to update the dev_commit_count_per_file dictionary
        if mod.old_path in dev_commit_count_per_file and mod.new_path != mod.old_path:
            dev_commit_count_per_file[mod.new_path] = dev_commit_count_per_file[mod.old_path]
            del dev_commit_count_per_file[mod.old_path]
        # If a file was added, we need to add it to the dev_commit_count_per_file dictionary
        if mod.new_path not in dev_commit_count_per_file:
            dev_commit_count_per_file[mod.new_path] = {}
        if commit.author.name not in dev_commit_count_per_file[mod.new_path]:
            dev_commit_count_per_file[mod.new_path][commit.author.name] = 0
        dev_commit_count_per_file[mod.new_path][commit.author.name] += 1

        # If a file was moved, we need to update the dev_commit_per_file dictionary
        if mod.old_path in dev_commit_per_file and mod.new_path != mod.old_path:
            dev_commit_per_file[mod.new_path] = dev_commit_per_file[mod.old_path]
            del dev_commit_per_file[mod.old_path]
        # If a file was added, we need to add it to the dev_commit_per_file dictionary
        if mod.new_path not in dev_commit_per_file:
            dev_commit_per_file[mod.new_path] = {"developers": {}}
        if commit.author.name not in dev_commit_per_file[mod.new_path]["developers"].keys():
            dev_commit_per_file[mod.new_path]["developers"][commit.author.name] = []
        dev_commit_per_file[mod.new_path]["developers"][commit.author.name].append(commit.committer_date)
        # If the file was created, we need to add the creation date to the dev_commit_per_file dictionary
        if 'creation_date' not in dev_commit_per_file[mod.new_path].keys(): # mod.change_type.name == 'ADD' and 
            dev_commit_per_file[mod.new_path]['creation_date'] = commit.committer_date
        # If the last refactor date is not set, we need to set it to the commit date
        if 'last_refactor_date' not in dev_commit_per_file[mod.new_path].keys():
            dev_commit_per_file[mod.new_path]['last_refactor_date'] = commit.committer_date

    
    if not is_a_refactoring_commit(commit.hash, refactorings_file_path):        
        return    
    
    modified_files = commit.modified_files   


    current_commit_metrics = {
        "commit": commit.hash,
        "MINOR": {},
        "NADEV": {},
        "NDDEV": {},
        "NCOMM": {},
        "OEXP": {},
    }

    try:
        for cpt, file in enumerate(modified_files):
            process_file(file, 
                        commit,                        
                        current_commit_metrics,
                        repository_path,
                        dev_commit_count_per_file,
                        dev_commit_per_file)
    except (OSError, ValueError) as e:
        print(f"Error processing commit {commit.hash}: {e}")
    

    return current_commit_metrics

def process_file(file, 
                 current_commit,                  
                 commit_metrics,
                 repo_path,
                 dev_commit_count_per_file,
                 dev_commit_per_file):
    
    contributors = {}
    
    ## MINOR ##
    if file.new_path: 
        git_blame_cmd = ['git', 'blame', f'{current_commit.hash}'.strip(), os.path.normpath(file.new_path)] 
        blame_result = subprocess.run(git_blame_cmd, capture_output=True, text=True, cwd=repo_path, errors='ignore')

        lines = blame_result.stdout.split('\n')
        for line in lines: 
            if line: 
                try: author = line.split(' ')[1]
                except IndexError as e: continue
                if author not in contributors: 
                    contributors[author] = 0 
                contributors[author] += 1 
        total_lines = sum(contributors.values()) 
        minor_contributors = [author for author, lines in contributors.items() if (lines / total_lines) < 0.05]
        commit_metrics["MINOR"][file.new_path] = len(minor_contributors)

        ## NADEV ##
        active_devs_since_last_refactor = set()
        files_to_match = [mod.new_path for mod in current_commit.modified_files if mod.change_type.name == 'MODIFY']
        for file_to_match in files_to_match:
            if file_to_match in dev_commit_per_file.keys():
                for dev, commit_dates in dev_commit_per_file[file_to_match]["developers"].items():
                    if any(commit_date > dev_commit_per_file[file.new_path]["last_refactor_date"] for commit_date in commit_dates):
                        active_devs_since_last_refactor.add(dev)
        commit_metrics["NADEV"][file.new_path] = len(active_devs_since_last_refactor)

        ## NDDEV ##
        active_devs_since_file_creation = set()
        for file_to_match in files_to_match:
            if file_to_match in dev_commit_per_file.keys():
                for dev, commit_dates in dev_commit_per_file[file_to_match]["developers"].items():
                    if any(commit_date > dev_commit_per_file[file.new_path]["creation_date"] for commit_date in commit_dates):
                        active_devs_since_file_creation.add(dev)
        commit_metrics["NDDEV"][file.new_path] = len(active_devs_since_file_creation)

        ## NCOMM ##
        updated_commit_dates_files = {}
        for file_to_match in files_to_match:
            updated_commit_dates_files[file_to_match] = []
            for commit_dates in dev_commit_per_file[file_to_match]["developers"].values():
                updated_commit_dates_files[file_to_match].extend([date for date in commit_dates if date > dev_commit_per_file[file.new_path]["last_refactor_date"]])

        if updated_commit_dates_files:
            intersection = lambda *lists: list(set(lists[0]).intersection(*lists[1:])) if lists else []
            NCOMM = len(intersection(*updated_commit_dates_files.values()))
        else:
            NCOMM = 0
        commit_metrics["NCOMM"][file.new_path] = NCOMM

        ## OEXP ##
        highest_contributor = max(dev_commit_count_per_file[file.new_path], key=dev_commit_count_per_file[file.new_path].get)
        command = f'git log --pretty=format:"%H %an" | grep "{highest_contributor}" | grep -B 1000000 "{current_commit.hash}" | wc -l'#['git', 'log', '--pretty=format:%H %an', '|', 'grep', highest_contributor, '|', 'grep', '-B', '1000000', current_commit.hash, '|', 'wc', '-l']
        owner_total_contributions = subprocess.run(command, capture_output=True, text=True, cwd=repo_path, shell=True).stdout.strip()
        owner_total_contributions = 0 if owner_total_contributions == '' else int(owner_total_contributions)
        
        command = f'git log --pretty=format:"%H" | grep -B 1000000 "{current_commit.hash}" | wc -l'
        total_contributions = subprocess.run(command, capture_output=True, text=True, cwd=repo_path, shell=True).stdout.strip()
        if total_contributions == '':
            OEXP = 0
        else:
            OEXP = owner_total_contributions*100 / int(total_contributions) 
        commit_metrics["OEXP"][file.new_path] = OEXP

        dev_commit_per_file[file.new_path]["last_refactor_date"] = current_commit.committer_date 
        

def commits_since_last_refactoring(commit, all_commits):
    commit_index = [c.hash for c in all_commits].index(commit.hash)
    found_commits = [all_commits[commit_index]]
    for c in all_commits[commit_index::-1]:
        found_commits.insert(0, c)
        if is_a_refactoring_commit(c.hash,""):
            break        
    return found_commits

def commits_since_file_creation(commit, all_commits, file_path):
    commit_index = [c.hash for c in all_commits].index(commit.hash)
    found_commits = [all_commits[commit_index]]
    for c in all_commits[commit_index::-1]:
        found_commits.insert(0, c)
        if file_path in [mod.filename for mod in c.modified_files if mod.change_type.name == 'ADD']:
            break
    return found_commits

def calculate_exp(repo_path):
    result = subprocess.run(['git', 'log', '--pretty=format:%an'], cwd=repo_path, stdout=subprocess.PIPE)
    authors = result.stdout.decode('utf-8').split('\n')
    # Count modifications per author
    modifications = defaultdict(int)
    for author in authors:
        modifications[author] += 1
    # Calculate the geometric mean
    exp = gmean(list(modifications.values()))
    return exp

def full_repo_analysis_bu(repository_path, refactorings_file_path, project_path):
    print(f"Processing repository: {repository_path}")
    metrics = process_repo(repository_path, refactorings_file_path)
    project_name = repository_path.split(os.sep)[-1]
    save_metrics(metrics, os.path.join(project_path, f"{project_name}-part_1b_metrics.json"))
    print(f"Metrics saved to {os.path.join(project_path, f'{project_name}-part_1b_metrics.json')}")

    if hasattr(is_a_refactoring_commit, 'list_of_commits'):
        delattr(is_a_refactoring_commit, 'list_of_commits')



def main():    
    repository_path, refactorings_file_path, project_path  = collect_process_settings()    
    full_repo_analysis_bu(repository_path, refactorings_file_path, project_path)

if __name__ == '__main__':    
    main()

