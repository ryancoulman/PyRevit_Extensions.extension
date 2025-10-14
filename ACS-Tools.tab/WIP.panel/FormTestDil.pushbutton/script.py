# -*- coding: utf-8 -*-

import clr
import os

# Get the path to your DLL — assuming it's in the same folder as this script
dll_path = os.path.join(os.path.dirname(__file__), "WPFpreview.dll")

# Add the reference so .NET knows about your assembly
clr.AddReferenceToFileAndPath(dll_path)

# Now you can safely import your C# class
from WPFpreview import SearchText

# Instantiate and show the WPF form
form = SearchText()
form.ShowDialog()
