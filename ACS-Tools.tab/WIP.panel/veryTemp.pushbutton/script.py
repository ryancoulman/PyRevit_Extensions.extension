from Autodesk.Revit.DB import *
from pyrevit import forms
from System.Collections.Generic import List


uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document    

TEXT_TO_APPEND = "\n" + "NON-MAINTAINED"
BUILT_IN_PARAM = BuiltInParameter.ALL_MODEL_INSTANCE_COMMENTS

def get_selected_elems():
    """Get selected elements from Revit UIDocument."""
    selection = uidoc.Selection.GetElementIds()
    elems = [doc.GetElement(id) for id in selection]
    return elems

def get_comments_param(elems):
    """Get the 'Comments' parameter from a list of elements."""
    comments_params = []
    for elem in elems:
        param = elem.get_Parameter(BUILT_IN_PARAM)
        if param and not param.IsReadOnly:
            comments_params.append(param)
    return comments_params

def appened_text_to_comments(params, text_to_append):
    """Append text to the 'Comments' parameter of each element."""
    for param in params:
        current_value = param.AsValueString() or param.AsString() or ""
        new_value = current_value + text_to_append
        param.Set(new_value)

if __name__ == "__main__":

    selected_elems = get_selected_elems()
    target_params = get_comments_param(selected_elems)

    with Transaction(doc, "Append Text to Comments") as t:
        t.Start()
        appened_text_to_comments(target_params, TEXT_TO_APPEND)
        t.Commit()
