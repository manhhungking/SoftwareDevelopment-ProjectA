#!/bin/bash
#SBATCH --job-name=All_proj_metric_processing      # Job name
#SBATCH --account=project_2011410   # Billing project, has to be defined!
#SBATCH --time=70:00:00             # Max. duration of the job
#SBATCH --mem=373G                 # Memory pool for all cores
#SBATCH --partition=small         # Job queue (partition)
#SBATCH --cpus-per-task=40          # Number of cores per task
#SBATCH --nodes=1                   # Number of nodes, ensure that all cores are on the same node
#SBATCH --ntasks=1                  # Number of tasks, assign all cores to one task
##SBATCH --mail-type=BEGIN          # Uncomment to enable mail

module load git
module load python-data/3.10-22.09
pip3 install --user pydriller

# Set the number of threads to the number of cores per task
export NUM_THREADS=$SLURM_CPUS_PER_TASK

# Define paths
export PROJAPPL_DIR="/projappl/project_2011410" # Project application directory
export SCRATCH_DIR="/scratch/project_2011410" # Scratch directory on Puhti

# Change directory to your project directory
cd /scratch/project_2011410

# Run python script
echo "Starting the job"
srun python3 multiple_repo_process.py > global_job_output.log


echo "Job completed. All project metrics computed."