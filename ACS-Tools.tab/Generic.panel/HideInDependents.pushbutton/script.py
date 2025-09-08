from Autodesk.Revit.DB import Transaction, ElementId
from pyrevit import revit, forms
from System.Collections.Generic import List

__title__ = "Hide In\nDependents"
__doc__ = "Overview:\nIf working in a primary view this allows you to hide an element in the current master view and all dependent views"

doc = revit.doc
active_view = revit.active_view
uidoc = __revit__.ActiveUIDocument

def get_dependent_views(doc, active_view):
    """Get all dependent views of a primary view."""
    
    # Check if the view has dependent views
    dependent_view_ids = active_view.GetDependentViewIds()

    if dependent_view_ids:
        dependent_views = []
        for view_id in dependent_view_ids:
            # Retrieve the dependent view from the document using its ID
            dependent_view = doc.GetElement(view_id)
            dependent_views.append(dependent_view)
        
        print("Found {} dependent views for the primary view:".format(len(dependent_views)))
        for view in dependent_views:
                print("Dependent View Name: {}".format(view.Name))
        return dependent_views
    else:
        forms.alert("No dependent views found for this primary view.", exitscript=True)
        return []

def get_selected_elements(doc, uidoc):
        """Property that retrieves selected views or promt user to select some from the dialog box."""

        selection = uidoc.Selection  

        try:
            selected_elements = [doc.GetElement(e_id) for e_id in selection.GetElementIds()]
            if not selected_elements:
                forms.alert("No elements were selected.\nPlease, try again.", exitscript=True)
        except:
            return

        return selected_elements

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
                     

