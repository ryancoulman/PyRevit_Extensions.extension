from Autodesk.Revit.DB import Transaction, ElementId
from pyrevit import revit, forms
from System.Collections.Generic import List
from helefuncs import get_selected_elements, get_dependent_views
from System.Windows import MessageBox


doc = revit.doc
active_view = revit.active_view
uidoc = __revit__.ActiveUIDocument

if __name__ == "__main__":

    dependent_views = get_dependent_views(doc, active_view)
    all_views = dependent_views.append(active_view)
    selected_elements = get_selected_elements(doc, uidoc)
    with Transaction(doc, "Unhide Elements In Dependents") as t:
            t.Start()
            for view in dependent_views:
                elements_to_unhide = List[ElementId]()
                for element in selected_elements:
                     # Update to check if element is visible in view first (not just manually hidden)
                     if element.CanBeHidden(active_view) and element.IsHidden(view):
                          elements_to_unhide.Add(element.Id)
                if elements_to_unhide.Count > 0:  # Only hide if there are sections to hide
                    view.UnhideElements(elements_to_unhide)
            MessageBox.Show("Successfully un-hidden element(s) in all dependent views", 'Success!')
            t.Commit()
                     

