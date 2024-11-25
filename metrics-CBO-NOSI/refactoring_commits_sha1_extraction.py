# A script that takes a list of project names, loops on each folder of the projects' commit history json and extract only the commits that had refactorings in them"

import json
import os

def extract_sha1_with_refactorings(commits):
    """Extracts sha1 values from commits that have refactorings."""
    sha1_values = []
    for commit in commits['commits']:
        # Check if 'refactorings' exists and has content
        if commit.get('refactorings'):  # Using .get() to avoid KeyError
            sha1_values.append(commit['sha1'])  # Store the sha1 if refactorings is present
    return sha1_values

def load_commits(file_path: str):
    """Loads commits from a JSON file, with error handling for malformed JSON and encoding issues."""
    try:
        # Try with UTF-8 encoding first
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON in file: {file_path}")
        print(f"Error details: {e}")
        return None
    except UnicodeDecodeError as e:
        # Try with ISO-8859-1 encoding if UTF-8 fails
        print(f"Error: Failed to decode file '{file_path}' using UTF-8. Trying ISO-8859-1 encoding.")
        try:
            with open(file_path, 'r', encoding='ISO-8859-1') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON in file: {file_path} with ISO-8859-1 encoding.")
            print(f"Error details: {e}")
            return None


def save_sha1_values(sha1_values: list, file_path: str):
    """Saves sha1 values to a JSON file."""
    with open(file_path, 'w') as file:
        json.dump({"sha1_values": sha1_values}, file, indent=4)

def get_project_names(folders_file: str):
    """Reads the folder names from the text file."""
    with open(folders_file, 'r') as file:
        # Read the folder names from the text file, assuming each folder is on a new line
        return [line.strip() for line in file.readlines()]

def process_project(project_name: str, parent_folder: str, output_folder: str):
    """Process each project folder."""
    input_path = os.path.join(parent_folder, project_name, 'refactorings.json')
    
    # Check if refactorings.json exists in the project folder
    if not os.path.exists(input_path):
        print(f"Error: 'refactorings.json' not found in {project_name}")
        return

    # Load commits and extract sha1 values for commits with refactorings
    commits = load_commits(input_path)
    
    if commits is None:
        # If loading the commits failed (due to a JSON error), skip this project
        return
    
    sha1_values = extract_sha1_with_refactorings(commits)
    
    # Prepare the output file path for this project
    output_path = os.path.join(output_folder, project_name, 'refactoring_commits_sha1_values.json')

    # Ensure the project output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save sha1 values to the output file
    save_sha1_values(sha1_values, output_path)
    print(f"Sha1 values for project '{project_name}' saved to {output_path}")

def main():
    # Define input and output directories
    parent_folder = './all_projects_commits_info'  # Parent folder that contains project folders
    output_folder = './sha1_values_refactorings'         # Folder to store the resulting refactorings JSON files

    # Get the list of project names from folders_list.txt
    project_names = get_project_names('folders_list.txt')

    # Process each project folder
    for project_name in project_names:
        process_project(project_name, parent_folder, output_folder)

if __name__ == '__main__':
    main()
