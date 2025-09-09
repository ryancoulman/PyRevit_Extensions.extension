from Autodesk.Revit.DB import Transaction, ElementId
from pyrevit import revit, forms
from System.Collections.Generic import List
from helefuncs import get_selected_elements, get_dependent_views

__title__ = "Hide In Dependents"
__doc__ = "Overview:\nIf working in a primary view this allows you to hide an element in the current master view and all dependent views"

doc = revit.doc
active_view = revit.active_view
uidoc = __revit__.ActiveUIDocument



if __name__ == "__main__":

    dependent_views = get_dependent_views(doc, active_view)
    all_views = dependent_views.append(active_view)
    selected_elements = get_selected_elements(doc, uidoc)
    with Transaction(doc, "Hide Elements In Dependents") as t:
            t.Start()
            for view in dependent_views:
                elements_to_hide = List[ElementId]()
                for element in selected_elements:
                     # Update to check if element is visible in view first (not just manually hidden)
                     if element.CanBeHidden(active_view) and not element.IsHidden(view):
                          elements_to_hide.Add(element.Id)
                if elements_to_hide.Count > 0:  # Only hide if there are sections to hide
                    view.HideElements(elements_to_hide)
            print("Successfully hidden element(s) in all dependent views")
            t.Commit()
                     

