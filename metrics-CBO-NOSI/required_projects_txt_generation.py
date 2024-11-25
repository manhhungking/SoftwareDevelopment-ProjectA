# A simple script that reads a csv (refactoring-stats-correct(in).csv) and outputs a text file with URLs of the projects"

import csv

# Input CSV file and output text file paths
csv_file = 'refactoring-stats-correct(in).csv'  # Change this to your actual CSV file path
txt_file = 'required_projects.txt'  # Output text file

# Open the CSV file and the text file for writing
with open(csv_file, mode='r', newline='', encoding='utf-8') as infile, open(txt_file, mode='w', encoding='utf-8') as outfile:
    # Create a CSV reader object
    csv_reader = csv.reader(infile)
    
    # Skip the header row (optional, remove if no header)
    next(csv_reader)
    
    # Iterate over each row in the CSV
    for row in csv_reader:
        # Extract the project_url (assuming it's the second column)
        project_url = row[1]  # Adjust the index if the URL is not in the second column
        # Write the URL to the text file, one per line
        outfile.write(project_url + '\n')

print("URLs have been extracted and saved to project_urls.txt.")
