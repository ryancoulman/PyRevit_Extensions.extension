from pyrevit import forms, revit
from Autodesk.Revit.DB import FilteredElementCollector, View



class ViewHandler():
    """Helper for selecting independent views in a project."""

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