from pyrevit import forms, revit
from Autodesk.Revit.DB import FilteredElementCollector, View

# implement all funcs into viewhandler. think there is a way to avoid having to init and just use staic methods 

class ViewHandler():
    """Helper for selecting views in a project."""

    def __init__(self, doc):
        self.doc = doc

    def get_independent_views(self):
        """Return all non-template, non-dependent views."""
        all_views = FilteredElementCollector(self.doc).OfClass(View).ToElements()
        independent = [v for v in all_views if not v.IsTemplate]
        return independent

    def select_independent_views(self, multiselect=True):
        """Show UI to select independent views."""
        independent_views = self.get_independent_views()
        if not independent_views:
            forms.alert("No independent views found.", exitscript=True)

        # Build dict {label: view}
        view_dict = {"{} [{}]".format(v.Name, v.ViewType): v for v in independent_views}

        selected_names = forms.SelectFromList.show(
            sorted(view_dict.keys(), key=str.lower),  # sort alphabetically
            multiselect=multiselect,
            title="Select Independent Views",
            button_name="Select"
        )

        if not selected_names:
            return []

        return [view_dict[name] for name in selected_names]
    


def get_selected_views(uidoc, doc):
    """
    Return a list of Revit View elements selected in the Project Browser.
    If no views are selected, return an empty list.
    """
    sel_ids = uidoc.Selection.GetElementIds()
    if not sel_ids:
        return []

    views = []
    for eid in sel_ids:
        elem = doc.GetElement(eid)
        if isinstance(elem, View) and not elem.IsTemplate:
            views.append(elem)

    return views

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
