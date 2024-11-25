import json
import matplotlib.pyplot as plt

def plot_metrics(metrics):
    # Plot the metrics
    # Extract the "ENTROPY", "NF", "ND", and "NS" values from the commit metrics
    entropy_values = [commit["ENTROPY"] for commit in metrics["commit_metrics"]]
    nf_values = [commit["NF"] for commit in metrics["commit_metrics"]]
    nd_values = [commit["ND"] for commit in metrics["commit_metrics"]]
    ns_values = [commit["NS"] for commit in metrics["commit_metrics"]]
    fix_values = [commit["FIX"] for commit in metrics["commit_metrics"]]
    # Get a file name from the commit metrics
    file_name = next(iter(metrics["commit_metrics"][0]["LA"])).split("/")[-1]
    la_values = []
    ld_values = []
    lt_values = []
    ndev_values = []
    age_values = []
    nuc_values = []
    cexp_values = []
    rexp_values = []
    sexp_values = []
    for commit in metrics["commit_metrics"]:
        for file in commit["LA"]:
            if file_name in file:
                la_values.append(commit["LA"][file])
                ld_values.append(commit["LD"][file])
                lt_values.append(commit["LT"][file])
                ndev_values.append(commit["NDEV"][file])
                age_values.append(commit["AGE"][file])
                nuc_values.append(commit["NUC"][file])
                cexp_values.append(commit["CEXP"][file])
                rexp_values.append(commit["REXP"][file])
                sexp_values.append(commit["SEXP"][file])
        
    # Create a figure with four subplots
    fig, axs = plt.subplots(3, 2, figsize=(12, 10))
    axs = axs.flatten()
    # Create a figure with seven subplots on the first page
    fig1, axs1 = plt.subplots(4, 2, figsize=(12, 10))
    axs1 = axs1.flatten()
    
    # Plot the entropy values
    axs1[0].plot(entropy_values)
    axs1[0].set_ylabel('Entropy')
    axs1[0].set_title('Entropy Over Commits')
    
    # Plot the number of modified files
    axs1[1].plot(nf_values)
    axs1[1].set_ylabel('Number of Modified Files')
    axs1[1].set_title('Number of Modified Files Over Commits')
    
    # Plot the number of directories involved
    axs1[2].plot(nd_values)
    axs1[2].set_ylabel('Number of Directories')
    axs1[2].set_title('Number of Directories Involved Over Commits')
    
    # Plot the number of modified subsystems
    axs1[3].plot(ns_values)
    axs1[3].set_ylabel('Number of Modified Subsystems')
    axs1[3].set_title('Number of Modified Subsystems Over Commits')

    # Plot the number of added lines
    axs1[4].plot(la_values)
    axs1[4].set_ylabel("Number of Added Lines")
    axs1[4].set_title(f'Number of Added Lines to the {file_name} File Over Commits')
    
    # Plot the number of deleted lines
    axs1[5].plot(ld_values)
    axs1[5].set_ylabel("Number of Deleted Lines")
    axs1[5].set_title(f'Number of Deleted Lines from the {file_name} File Over Commits')
    
    # Plot the number of lines in the file
    axs1[6].plot(lt_values)
    axs1[6].set_ylabel("Number of Lines in the File")
    axs1[6].set_title(f'Number of Lines in the {file_name} File Over Commits')
    
    # Adjust layout and show the first page of plots
    plt.tight_layout()
    plt.show()

    # Create a figure with seven subplots on the second page
    fig2, axs2 = plt.subplots(4, 2, figsize=(12, 10))
    axs2 = axs2.flatten()
    
    # Plot the number of developers
    axs2[0].plot(ndev_values)
    axs2[0].set_ylabel("Number of Developers")
    axs2[0].set_title(f'Number of Developers for the {file_name} File Over Commits')
    
    # Plot the number of bug fixes
    axs2[1].plot(fix_values, '.', markersize=5)
    axs2[1].set_title(f'Bug Fixes for the {file_name} File Over Commits') 
    axs2[1].set_yticklabels(['False', 'True'])   
    axs2[1].set_yticks([0, 1])
    axs2[1].set_ylabel("Bug Fixes")
    
    # Plot the age of the file
    axs2[2].plot(age_values)
    axs2[2].set_ylabel("Age of the File")
    axs2[2].set_title(f'Age of the {file_name} File Over Commits')
    
    # Plot the number of unique changes
    axs2[3].plot(nuc_values)
    axs2[3].set_ylabel("Number of Unique Changes")
    axs2[3].set_title(f'Number of Unique Changes to the {file_name} File Over Commits')
    
    # Plot the code experience
    axs2[4].plot(cexp_values)
    axs2[4].set_ylabel("Code Experience")
    axs2[4].set_title(f'Code Experience for the {file_name} File Over Commits')
    
    # Plot the review experience
    axs2[5].plot(rexp_values)
    axs2[5].set_ylabel("Review Experience")
    axs2[5].set_title(f'Review Experience for the {file_name} File Over Commits')
    
    # Plot the subsystem experience
    axs2[6].plot(sexp_values)
    axs2[6].set_ylabel("Subsystem Experience")
    axs2[6].set_title(f'Subsystem Experience for the {file_name} File Over Commits')
    
    # Adjust layout and show the second page of plots
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    path_metrics_json = "Result_metrics/truth-part_2_metrics.json"
    #"Result_metrics/sonarqube-part_2_metrics.json" 
    #"Result_metrics/android-async-http-part_2_metrics.json"
    with open(path_metrics_json, "r") as f:
        metrics = json.load(f)
    plot_metrics(metrics)