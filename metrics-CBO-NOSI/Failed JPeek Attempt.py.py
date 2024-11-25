import os
import subprocess
import json
import glob
# Paths configuration
SHA1_VALUES_DIR = "C:\\Users\\testu\\Desktop\\realWork\\sha1_values_refactorings"
PROJECTS_TXT = "C:\\Users\\testu\\Desktop\\realWork\\exampleProjects.txt"
CK_JAR_PATH = "C:\\Users\\testu\\Desktop\\realWork\\ck\\target\\ck-0.7.1-SNAPSHOT-jar-with-dependencies.jar"
JPEEK_JAR_PATH = "C:\\Users\\testu\\Desktop\\realWork\\JPeek\\jpeek-0.32.3-jar-with-dependencies.jar"
OUTPUT_DIR = "output/metrics"
######
JAVAC_PATH = "C:\\Program Files\\Java\\jdk-23\\bin\\javac.exe"


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

# # Function to compile Java files using javac
# def compile_java_files(project_dir):
#     print(f"Compiling Java files in {project_dir}")
    
#     # Find all .java files in the project folder and subfolders
#     java_files = glob.glob(os.path.join(project_dir, '**', '*.java'), recursive=True)

#     if java_files:
#         # Compile the Java files into .class files in the same directory as JPeek will run
#         output_dir = os.path.join(project_dir, 'bin')  # You can customize this folder name
#         os.makedirs(output_dir, exist_ok=True)
#         subprocess.run([JAVAC_PATH, "-d", output_dir] + java_files, cwd=project_dir, check=True)
#         print(f"Java files compiled into {output_dir}")
#     else:
#         print("No Java files found to compile.")
# def compile_java_files(project_dir):
#     print(f"Compiling Java files in {project_dir}")
    
#     # Check if there is a pom.xml in the project directory (Maven project)
#     pom_file = os.path.join(project_dir, "pom.xml")
#     if os.path.exists(pom_file):
#         # Run mvn compile to compile the Java files
#         subprocess.run(["mvn", "compile"], cwd=project_dir, check=True)
#         print(f"Java files compiled using Maven in {project_dir}")
#     else:
#         print(f"No pom.xml found in {project_dir}. Skipping Maven compilation.")

# Function to compile Java files using Maven or Gradle
def compile_java_files(project_dir):
    print(f"Compiling Java files in {project_dir}")
    
    # Check for Maven (pom.xml) or Gradle (build.gradle)
    pom_file = os.path.join(project_dir, "pom.xml")
    gradle_file = os.path.join(project_dir, "build.gradle")

    try:
        if os.path.exists(pom_file):
            # Run mvn compile
            print("Found pom.xml, using Maven to compile.")
            subprocess.run(["mvn", "compile"], cwd=project_dir, check=True)
        elif os.path.exists(gradle_file):
            # Run gradle build
            print("Found build.gradle, using Gradle to compile.")
            subprocess.run(["C:\\Gradle\\gradle-8.11\\bin\\gradle.bat", "build"], cwd=project_dir, check=True, shell=True)
        else:
            print("No build configuration (pom.xml or build.gradle) found. Skipping compilation.")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed for {project_dir}: {e}")
        raise
# Function to run CK on a specific commit
def run_ck(project_dir, commit_hash, output_dir):
    # Change directory to project folder
    os.chdir(project_dir)

    # Checkout the specific commit
    print(f"Checking out commit {commit_hash}")
    subprocess.run(["git", "checkout", commit_hash], check=True)

    # Prepare CK command
    ck_output_dir = os.path.join(output_dir, "ck", commit_hash)
    os.makedirs(ck_output_dir, exist_ok=True)
    ck_command = [
        "java", "-jar", CK_JAR_PATH,
        project_dir, "false", "0", "false", ck_output_dir
    ]

    # Run CK
    print(f"Running CK on commit {commit_hash}")
    subprocess.run(ck_command, check=True)

# Function to run JPeek on a specific commit
def run_jpeek(project_dir, commit_hash, output_dir):
    # Prepare JPeek command
    jpeek_output_dir = os.path.join(output_dir, "jpeek", commit_hash)
    os.makedirs(jpeek_output_dir, exist_ok=True)
    jpeek_command = [
        "java", "-jar", JPEEK_JAR_PATH,
        "--sources", os.path.join(project_dir, 'target/classes'),  # JPeek will use compiled classes from 'bin'
        "--target", jpeek_output_dir,
        "--metrics", "C3",  # You can change this to other metrics
        "--quiet",
        "--overwrite"
    ]

    # Run JPeek
    print(f"Running JPeek on commit {commit_hash}")
    subprocess.run(jpeek_command, check=True)

# Main script
def main():
    project_links = read_project_links(PROJECTS_TXT)

    for repo_url in project_links:
        # Extract project name from URL
        project_name = repo_url.split("/")[-1].replace(".git", "")
        print(f"Processing project {project_name}")

        # Load commit hashes
        sha1_values = load_sha1_values(project_name)
        if not sha1_values:
            print(f"No sha1 values found for {project_name}, skipping...")
            continue

        # Clone or access repository
        project_dir = os.path.join("C:\\Users\\testu\\Desktop\\realWork\\Repos", project_name)
        clone_repo(repo_url, project_dir)

        # Process each commit hash
        for commit_hash in sha1_values:
            try:
                compile_java_files(project_dir)  # Compile Java files
                run_ck(project_dir, commit_hash, OUTPUT_DIR)  # Run CK
                run_jpeek(project_dir, commit_hash, OUTPUT_DIR)  # Run JPeek
            except subprocess.CalledProcessError as e:
                print(f"Error processing commit {commit_hash} for {project_name}: {e}")

        print(f"Finished processing project {project_name}")

if __name__ == "__main__":
    main()
