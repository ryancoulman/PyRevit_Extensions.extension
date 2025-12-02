from Autodesk.Revit.DB import *
from pyrevit import revit
from System.Windows import MessageBox

__title__ = "Scope Box\nCounter"
__doc__ = "Counts the number of scope boxes in the current document."

doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView


    
def get_scope_box_name_from_view(view, is_active_view=False):
    scope_box_param = view.LookupParameter("Scope Box") or view.get_Parameter(BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
    if not scope_box_param:
        MessageBox.Show("No scope box parameter found in the active view.", "Info") if is_active_view else None
        return None
    
    scope_box_name = scope_box_param.AsValueString() or scope_box_param.AsString()
    if not scope_box_name:
        MessageBox.Show("No scope box is assigned to the active view.", "Info") if is_active_view else None
        return None
    
    return scope_box_name

def get_scope_box_name_from_active_view():
    """Get the scope box name assigned to the active view."""
    return get_scope_box_name_from_view(active_view, True)

def count_scope_boxes_by_name(scope_box_name):
    """Count the number of scope boxes with the given name in the document."""
    collector = FilteredElementCollector(doc).OfClass(View).ToElements()
    name_list = []
    for view in collector:
        try:
            name = get_scope_box_name_from_view(view)
            if name and name == scope_box_name:
                name_list.append(view.Name)
        except:
            continue
    return name_list

def main():
    scope_box_name = get_scope_box_name_from_active_view()
    if not scope_box_name:
        return None

    matching_views = count_scope_boxes_by_name(scope_box_name)
    print("Found {} views with scope box '{}'".format(len(matching_views), scope_box_name))
    for view_name in matching_views:
        print(" - {}".format(view_name))

if __name__ == "__main__":
    main()