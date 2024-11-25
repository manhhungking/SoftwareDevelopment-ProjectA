# A script that outputs CK metrics using Multiprocessing of all URLs listed in a txt file. Just hard-code the path of the txt file in the global variable "PROJECTS_TXT"


import os
import subprocess
import json
import shutil
import stat
from multiprocessing import Pool

# Paths configuration
SHA1_VALUES_DIR = "C:\\Users\\testu\\Desktop\\realWork\\sha1_values_refactorings"
PROJECTS_TXT = "C:\\Users\\testu\\Desktop\\realWork\\exampleProjects.txt"
CK_JAR_PATH = "C:\\Users\\testu\\Desktop\\realWork\\ck\\target\\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"
OUTPUT_DIR = "C:\\Users\\testu\\Desktop\\realWork\\Metrics"

# Helper function to handle read-only files during deletion
def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

# Function to read GitHub project URLs from the text file
def read_project_links(file_path):
    with open(file_path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

# Function to load sha1 values from the JSON file
def load_sha1_values(project_name):
    json_path = os.path.join(SHA1_VALUES_DIR, project_name, "refactoring_commits_sha1_values.json")
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
            return data.get("sha1_values", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error reading JSON for project {project_name}: {e}")
        return []

# Function to clone repository if it doesn't exist locally
def clone_repo(repo_url, project_dir):
    if not os.path.exists(project_dir):
        print(f"Cloning repository {repo_url} into {project_dir}")
        subprocess.run(["git", "clone", repo_url, project_dir], check=True)

# Function to run CK metrics for a specific commit
def run_ck(project_dir, commit_hash, output_dir):
    os.chdir(project_dir)
    subprocess.run(["git", "checkout", commit_hash], check=True)
    project_name = os.path.basename(project_dir)
    ck_output_dir = os.path.join(output_dir, project_name, commit_hash)
    os.makedirs(ck_output_dir, exist_ok=True)
    ck_command = [
        "java", "-jar", CK_JAR_PATH,
        project_dir, "false", "0", "false", ck_output_dir
    ]
    subprocess.run(ck_command, check=True)

# Function to process a single project
def process_project(repo_url):
    project_name = repo_url.split("/")[-1].replace(".git", "")
    print(f"Processing project {project_name}")
    sha1_values = load_sha1_values(project_name)
    if not sha1_values:
        print(f"No sha1 values found for {project_name}, skipping...")
        return
    
    project_dir = os.path.join("C:\\Users\\testu\\Desktop\\realWork\\Repos", project_name)
    clone_repo(repo_url, project_dir)
    
    for commit_hash in sha1_values:
        try:
            run_ck(project_dir, commit_hash, OUTPUT_DIR)
        except subprocess.CalledProcessError as e:
            print(f"Error processing commit {commit_hash} for {project_name}: {e}")
    
    print(f"Cleaning up repository for {project_name}")
    try:
        shutil.rmtree(project_dir, onerror=remove_readonly)
        print(f"Deleted repository folder {project_name}")
    except Exception as e:
        print(f"Failed to delete repository {project_name}: {e}")

# Main script with multiprocessing
def main():
    project_links = read_project_links(PROJECTS_TXT)
    max_workers = min(os.cpu_count(), len(project_links))  # Limit number of processes to CPU count or number of projects
    
    with Pool(processes=max_workers) as pool:
        pool.map(process_project, project_links)

if __name__ == "__main__":
    main()
