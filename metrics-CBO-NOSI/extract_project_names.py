# A script that extracts all the names of the projects' folders and outputs them into a txt file.


import os

def get_subfolders(parent_folder):
    # List to store the subfolder names
    folder_names = []
    
    try:
        # List all items in the given directory
        for item in os.listdir(parent_folder):
            # Check if the item is a directory (folder)
            if os.path.isdir(os.path.join(parent_folder, item)):
                folder_names.append(item)  # Add folder name to the list
    except FileNotFoundError:
        print(f"Error: The folder '{parent_folder}' was not found.")
    except PermissionError:
        print(f"Error: You do not have permission to access '{parent_folder}'.")
    
    return folder_names

def save_folders_to_txt(folder_names, output_file):
    # Save the folder names to a text file
    with open(output_file, "w") as file:
        for folder in folder_names:
            file.write(folder + "\n")
    print(f"Folder names have been saved to {output_file}")

def main():
    parent_folder = input("Enter the path to the parent folder: ").strip()
    
    # Get the list of subfolders
    folder_names = get_subfolders(parent_folder)
    
    if folder_names:
        print("List of subfolders found:")
        print(folder_names)  # Print the folder names in the console
        
        # Save the folder names to a text file
        save_folders_to_txt(folder_names, "folders_list.txt")
    else:
        print("No subfolders found or an error occurred.")

if __name__ == "__main__":
    main()
