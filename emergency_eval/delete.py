# If someone knows shell commands, he'd be faster than my writing this script, but well...

import os
import shutil


def get_scheduler_and_sim_files(choice, sim_only=False):
    files = []
    for top_folder in os.listdir("."):
        if top_folder.startswith("t_"):
            for stream_folder in os.listdir(top_folder):
                if stream_folder.startswith("s_"):
                    for file in os.listdir(f"{top_folder}/{stream_folder}"):
                        if sim_only and not os.path.isdir(f"{top_folder}/{stream_folder}/{file}"):
                            continue
                        if file.startswith("etsn") and (choice == "1" or choice == "3"):
                            files.append(f"{top_folder}/{stream_folder}/{file}")
                        if (file.startswith("libtsndgm") or file.startswith("cp_out")) and (choice == "2" or choice == "3"):
                            files.append(f"{top_folder}/{stream_folder}/{file}")
    return files


def delete_scheduler_output():
    print("Chose scheduler files to delete:")
    print("1: etsn")
    print("2: libtsndgm")
    print("3: Both")
    choice = input("Your choice: ")
    files = get_scheduler_and_sim_files(choice)

    print("Files to delete:")
    for file in files:
        if os.path.isdir(file):
            print(f"{file} (folder)")
        else:
            print(file)

    confirm = input("Do you want to delete these files? (y/n): ")
    if confirm == "y":
        for file in files:
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
        print("Files deleted.")
    else:
        print("Files not deleted.")


def delete_topology():
    folders = []
    for top_folder in os.listdir("."):
        if top_folder.startswith("t_"):
            folders.append(top_folder)
    print("The following folders will be deleted:")
    for folder in folders:
        print(folder)
    confirm = input("Do you want to delete these folders? (y/n): ")
    if confirm == "y":
        for folder in folders:
            shutil.rmtree(folder)
        print("Folders deleted.")
    else:
        print("Folders not deleted.")


def delete_simulations():
    print("Chose simulation files to delete:")
    print("1: etsn")
    print("2: libtsndgm")
    print("3: Both")
    choice = input("Your choice: ")
    files = get_scheduler_and_sim_files(choice, True)

    print("Files to delete:")
    for file in files:
        if os.path.isdir(file):
            print(f"{file} (folder)")
        else:
            print(file)

    confirm = input("Do you want to delete these files? (y/n): ")
    if confirm == "y":
        for file in files:
            if os.path.isdir(file):
                shutil.rmtree(file)
            else:
                os.remove(file)
        print("Files deleted.")
    else:
        print("Files not deleted.")

if __name__ == "__main__":
    print("Delete:")
    print("Note: Smaller numbers will also delete the files of the larger numbers (i.e. deleting a topology will also delete the streams)")
    print("1: Topology")
    print("2: Streams")
    print("3: Scheduler output")
    print("4: Simulation")
    choice = input("Your choice: ")

    if choice == "1":
        delete_topology()
    elif choice == "2":
        print("Not implemented")
    elif choice == "3":
        delete_scheduler_output()
    elif choice == "4":
        delete_simulations()