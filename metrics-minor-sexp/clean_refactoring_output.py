import json, os
from pathlib import Path

def keep_refactorings(commits):
    print(f"Number of initial commits: {len(commits['commits'])}")
    refactorings = [commit for commit in commits["commits"] if commit['refactorings']]
    print(f"Number of commits with refactorings: {len(refactorings)}")
    return refactorings

def load_commits(file_path:str):
    with open(file_path, 'r') as file:
        return json.load(file)
    
def save_refactorings(refactorings:list, file_path:str):
    with open(file_path, 'w') as file:
        json.dump({"commits":refactorings}, file)

def create_only_refactorings_file(folder_to_process:str):
    # Take folder_to_process and add the refactrings.json file to it
    input_file = os.path.join(folder_to_process, "refactorings.json")
    output_file = os.path.join(folder_to_process, "only_refactorings.json")
    if Path(output_file).exists():
            return output_file
    commits = load_commits(input_file)
    refactorings = keep_refactorings(commits)
    save_refactorings(refactorings, output_file)

    return output_file

def main():
    create_only_refactorings_file("Projects_data\\android")

if __name__ == '__main__':
    main()