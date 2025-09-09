# -*- coding: utf-8 -*-
__title__ = "Rotate Counter-Clockwise"
__doc__ = """
Description:
Rotate selected elements by 90 degrees anti-clockwise
"""

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> IMPORTS
from pyrevit import revit
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from lib import get_selected_elements, rotate_element

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> VARIABLES
doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument
app = __revit__.Application

#>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> MAIN
if __name__ == '__main__':
    selected_elements = get_selected_elements(uidoc)
    with revit.Transaction(__title__):
        for element in selected_elements:
            try:
                rotate_element(doc, element, 90)
            except Exception as e:
                print("Could not rotate element - {}: {}".format(element.Id, e))
