import json
import os
import subprocess
from pydriller import Repository
import collections
import codecs

GIT_ROOT = 'E:/Data/git_repos'
BASE_PATH = 'C:/Data/Koulu/University of Oulu/CSC-Puhti'

def is_same_path(path1, path2):
    if path1 is None or path2 is None:
        return False
    if not path1.startswith('/') and not path1.startswith('\\'):
        path1 = '/' + path1
    if not path2.startswith('/') and not path2.startswith('\\'):
        path2 = '/' + path2
    return os.path.normpath(path1) == os.path.normpath(path2)

def safe_read_file(file_path):
    """Attempts to read a file using different encodings."""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with codecs.open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    
    # If all encodings fail, try with 'ignore' error handler
    try:
        with codecs.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

def get_blame_info(repo_path, commit_hash, file_path):
    try:
        # Set PYTHONIOENCODING environment variable
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        cmd = ['git', '-C', repo_path, 'blame', commit_hash, '--', file_path]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            env=env
        )
        return result.stdout
    except subprocess.SubprocessError as e:
        print(f"Error in git blame command: {e}")
        return ""
    except UnicodeDecodeError as e:
        print(f"Unicode decode error in git blame: {e}")
        # Try with different encoding
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding='latin-1',
                errors='ignore',
                env=env
            )
            return result.stdout
        except Exception as e:
            print(f"Failed to get blame info: {e}")
            return ""

def calculate_own(blame_info):
    if not blame_info:
        return 0
        
    lines = blame_info.split('\n')
    author_lines = collections.Counter()

    for line in lines:
        if line:
            try:
                author = line.split('(')[1].split(' ')[0]
                author_lines[author] += 1
            except (IndexError, ValueError) as e:
                print(f"Error parsing blame line: {e}")
                continue

    total_lines = sum(author_lines.values())
    if total_lines == 0:
        return 0

    highest_contributor_lines = max(author_lines.values()) if author_lines else 0
    own_percentage = (highest_contributor_lines / total_lines) * 100
    return own_percentage

def get_metrics(considered_commit, refactoring_commits, file_path, repo, repo_path):
    metrics = {
        'COMM': 0,
        'ADEV': set(),
        'DDEV': set(),
        'ADD': 0,
        'DEL': 0,
        'OWN': 0
    }
    total_added_lines = 0
    total_deleted_lines = 0

    metric_found = False
    for commit in repo:
        for mod in commit.modified_files:
            if is_same_path(mod.new_path, file_path) or is_same_path(mod.old_path, file_path):
                metric_found = True
                metrics['COMM'] += 1
                metrics['ADEV'].add(commit.author.email)
                metrics['DDEV'].add(commit.author.email)
                metrics['ADD'] += mod.added_lines
                metrics['DEL'] += mod.deleted_lines
                total_added_lines += mod.added_lines
                total_deleted_lines += mod.deleted_lines

    if metric_found:
        blame_info = get_blame_info(repo_path, considered_commit['commit_hash'], file_path)
        metrics['OWN'] = calculate_own(blame_info)

    if not metric_found:
        return None
        
    metrics['ADEV'] = len(metrics['ADEV'])
    metrics['DDEV'] = len(metrics['DDEV'])
    metrics['ADD'] /= total_added_lines if total_added_lines else 1
    metrics['DEL'] /= total_deleted_lines if total_deleted_lines else 1

    return metrics

def process_repository(repo_path, repo_name):
    try:
        commits_content = safe_read_file(os.path.join(repo_path, 'commits.json'))
        refactorings_content = safe_read_file(os.path.join(repo_path, 'refactorings.json'))
        
        if commits_content is None or refactorings_content is None:
            print(f"Could not read JSON files in {repo_path}")
            return
            
        commits = json.loads(commits_content)
        refactorings = json.loads(refactorings_content)['commits']
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading JSON files in {repo_path}: {e}")
        return

    if not isinstance(refactorings, list):
        print(f"Unexpected format in refactorings.json in {repo_path}")
        return

    refactoring_commits = refactorings
    results = []

    for refactoring_commit in refactoring_commits:
        for commit in commits:
            if refactoring_commit['sha1'] == commit['commit_hash']:
                files = list(commit['diff'].keys())

                if commits.index(commit) == 0:
                    repo = Repository(os.path.join(GIT_ROOT, repo_name),
                                   to_commit=commit['commit_hash']).traverse_commits()
                else:
                    prev_commit = refactoring_commits[refactoring_commits.index(refactoring_commit) - 1]
                    repo = Repository(os.path.join(GIT_ROOT, repo_name), 
                                   from_commit=prev_commit['sha1'],
                                   to_commit=commit['commit_hash']).traverse_commits()
                for file in files:
                    try:
                        metrics = get_metrics(commit, refactoring_commits, file, repo, os.path.join(GIT_ROOT, repo_name))
                    except Exception as e:
                        print(f"Error getting metrics for {file} in {repo_name}: {e}")
                        continue
                    if metrics is not None:
                        results.append({
                            'commit': commit['commit_hash'],
                            'metrics': metrics
                        })
        if refactoring_commits.index(refactoring_commit) % 10 == 0:
            print(f"Processed {refactoring_commits.index(refactoring_commit) + 1}/{len(refactoring_commits)} refactorings in {repo_name}")

    print(f"Processed all refactorings in {repo_name}")

    try:
        metrics_file_path = os.path.join(repo_path, f"{repo_name}_metrics.json")
        with open(metrics_file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4)
    except Exception as e:
        print(f"Error writing metrics file for {repo_name}: {e}")

def main():
    base_path = BASE_PATH
    for repo_name in os.listdir(base_path):
        if repo_name.startswith('.'):
            continue
        repo_path = os.path.join(base_path, repo_name)
        if os.path.isdir(repo_path):
            process_repository(repo_path, repo_name)

if __name__ == "__main__":
    main()