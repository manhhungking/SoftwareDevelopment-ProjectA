import json

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
        json.dump({"commits":refactorings}, file, indent=4)

def main():
    # Change paths according to your file structure
    commits = load_commits('Example_data\\core\\refactorings.json')
    refactorings = keep_refactorings(commits)
    save_refactorings(refactorings, 'Example_data\\core\\only_refactorings.json')

if __name__ == '__main__':
    main()