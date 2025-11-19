# -*- coding: utf-8 -*-

import clr
import os
import random
import shutil

destination_directory = os.path.join(os.path.dirname(__file__), "temp")
if not os.path.exists(destination_directory):# Create the directory if it doesn't exist
    os.makedirs(destination_directory)

dll_folder_path = "C:\\Users\\RyanCoulman\\Documents\\RevTools\\src\\ValveGetter\\ValveGetter.Core\\bin\\Debug R23\\net48"
dll_file = "ValveGetter.Core"
all_files_in_folder = os.listdir(dll_folder_path)

# Copy all files to temp/ in the current directory
for file_name in all_files_in_folder:
    if file_name.endswith(".dll"):
        full_file_path = os.path.join(dll_folder_path, file_name)
        # Copy the file to the destination directory, preserving metadata
        shutil.copy2(full_file_path, destination_directory)

# Generate random suffix of 5 chars to avoid caching issues
random_suffix = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789_-', k=5))

dll_path = os.path.join(destination_directory, "ValveGetter.Core{}.dll".format(random_suffix))
clr.AddReferenceToFileAndPath(dll_path)
from ValveGetter.Core import ValveServiceExtractor


uidoc = __revit__.ActiveUIDocument

if __name__ == "__main__":
    ValveServiceExtractor.ExtractValveServices(uidoc)

