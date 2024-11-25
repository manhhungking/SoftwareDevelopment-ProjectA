# For each project folder in the Projects folder
    # We have the path to the given project folder
    # A project has the git repository cloned, and the refactorings.json file created
    # Create the only_refactorings.json file with the create_only_refactorings_file function (if the file already exists, the function call doesn't do anything)
    # Run the metrics_nicolas_reformed.py with the paths to the only_refactorings.json file and the project folder

import os, subprocess
from pathlib import Path
from calc_1b_metrics import full_repo_analysis_bu
from clean_refactoring_output import create_only_refactorings_file
from calc_2_metrics import full_repo_analysis


def clone_project(project_url:str, project_name:str, project_folder:str):
    cloned_repo_path = os.path.join(project_folder, project_name).rstrip()
    if not Path(cloned_repo_path).exists(): # Check if the project is already cloned
        print(f"Cloning project: {project_name} (into {cloned_repo_path})")
        subprocess.run(["git", "clone", project_url, cloned_repo_path], check=True)
    return cloned_repo_path

def remove_project(project_folder:str):
    if Path(project_folder).exists():
        try:
            subprocess.run(["rm", "-rf", project_folder], check=True)
        except:
            print(f"Error removing project folder: {project_folder}")


def get_project_urls(file_path:str):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file.readlines()]

def main():
    # For each project folder in the Projects folder
    project_folder = '.\\Projects_data' # '/scratch/project_2011410/Projects_data'
    project_urls = get_project_urls("projects.txt")

    total_projects = len(project_urls)

    for cpt, project_url in enumerate(project_urls):
        project_name = project_url.split('/')[-1].replace('.git', '').rstrip()
        print(f"Processing project: {project_name} ({(cpt+1)*100/total_projects:.2f}%)")
        current_project_folder = os.path.join(project_folder, project_name)        
        if not Path(current_project_folder).exists():
            os.mkdir(current_project_folder)
        try:
            cloned_repo_path = clone_project(project_url.rstrip(), project_name, current_project_folder)
        except:
            print(f"Error cloning project: {project_name}")
            continue
        try:
            ref_com_file_path = create_only_refactorings_file(current_project_folder)
        except:
            print(f"Error creating only_refactorings file for project: {project_name}")
            remove_project(cloned_repo_path)
            continue

        #full_repo_analysis(cloned_repo_path, ref_com_file_path, project_folder)
        full_repo_analysis_bu(cloned_repo_path, ref_com_file_path, project_folder)
        remove_project(cloned_repo_path)
    
    print("All projects processed")

if __name__ == '__main__':
    print("Starting multi-repo process")
    main()
        