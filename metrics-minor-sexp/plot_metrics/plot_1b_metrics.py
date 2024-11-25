import json

import matplotlib.pyplot as plt

with open("Result_metrics/truth-part_1b_metrics.json", "r") as f: #"Result_metrics/guacamole-client-part_1b_metrics.json"
    data = json.load(f)

# Extract metrics
commits = [commit['commit'] for commit in data['commit_metrics']]
metrics = ['MINOR', 'NADEV', 'NDDEV', 'NCOMM', 'OEXP']
files = list(data['commit_metrics'][0]['MINOR'].keys())

# Prepare data for plotting
plot_data = {metric: [] for metric in metrics}
for commit in data['commit_metrics']:
    for metric in metrics:
        plot_data[metric].append(sum(commit[metric].values()))

# Plotting
fig, axs = plt.subplots(len(metrics), 1, figsize=(10, 15))
fig.tight_layout(pad=5.0)

for i, metric in enumerate(metrics):
    axs[i].plot(commits, plot_data[metric], marker='.')
    axs[i].set_title(metric)
    axs[i].xaxis.set_major_locator(plt.NullLocator())
    axs[i].set_xlabel('Commits')
    axs[i].set_ylabel(metric)

plt.show()