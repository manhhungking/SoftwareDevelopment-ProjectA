#!/bin/bash
#SBATCH --job-name=Refactoring      # Job name
#SBATCH --account=project_2011276   # Billing project, has to be defined!
#SBATCH --time=70:00:00             # Max. duration of the job
#SBATCH --mem=1400G                 # Memory pool for all cores
#SBATCH --partition=hugemem         # Job queue (partition)
#SBATCH --cpus-per-task=40          # Number of cores per task
#SBATCH --nodes=1                   # Number of nodes, ensure that all cores are on the same node
#SBATCH --ntasks=1                  # Number of tasks, assign all cores to one task
##SBATCH --mail-type=BEGIN          # Uncomment to enable mail

module load biojava/17
module load git
module load python-data/3.10-22.09
pip3 install --user pydriller

# Set the number of threads to the number of cores per task
export NUM_THREADS=$SLURM_CPUS_PER_TASK

# Define paths
export PROJAPPL_DIR="/projappl/project_2011276" # Project application directory
export SCRATCH_DIR="/scratch/project_2011276" # Scratch directory on Puhti
export GIT_REPOS_ROOT="$SCRATCH_DIR/git_repos" # Local scratch directory on local NVMe disk
export RUN_DIR="$SCRATCH_DIR/run" # Local scratch directory on local NVMe disk

# Ensure that the directories exist
mkdir -p "$GIT_REPOS_ROOT"
mkdir -p "$RUN_DIR"

# Change to the local NVMe disk scratch directory
cd "$RUN_DIR" || exit

# Copy script and projects.txt file to the local scratch directory
cp "$PROJAPPL_DIR/csc-refactdrill.py" .
cp "$PROJAPPL_DIR/projects.txt" .

# Set refactoring miner path
export REFMINER_PATH="$PROJAPPL_DIR/miner/RefactoringMiner-3.0.9/bin/RefactoringMiner" # Path to RefactoringMiner

# Set execution permissions for the RefactoringMiner
chmod +x "$REFMINER_PATH"

# Run python script
srun python csc-refactdrill.py > refactdrill.log

# Copy the results back to the scratch directory
#cp -r "$RUN_DIR" "$SCRATCH_DIR/results"

echo "Job completed. All repositories processed."