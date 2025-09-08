from Autodesk.Revit.DB import (Line, XYZ, ElementTransformUtils, TextNote, AnnotationSymbol)
from pyrevit import revit, forms
import math


def get_selected_elements(uidoc, exitscript=True):
    """Property that retrieves selected views or promt user to select some from the dialog box."""
    doc = uidoc.Document
    selection = uidoc.Selection  

    try:
        selected_elements = [doc.GetElement(e_id) for e_id in selection.GetElementIds()]
        if not selected_elements and exitscript:
            forms.alert("No elements  were selected.\nPlease, try again.", exitscript=exitscript)
    except:
        return

    return selected_elements


def rotate_element(doc, elem, degrees_to_rotate):
    # Get Center Point
    bounding_box = elem.get_BoundingBox(doc.ActiveView)
    point = (bounding_box.Min + bounding_box.Max) / 2

    # Create Vertical Axis Line
    axis_line = Line.CreateBound(point, point + XYZ.BasisZ )

    # Rotate
    ElementTransformUtils.RotateElement(doc, elem.Id, axis_line, math.radians(degrees_to_rotate))

