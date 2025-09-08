from Autodesk.Revit.DB import FilteredElementCollector, ViewSheet, Viewport, ViewSchedule, ViewType
from pyrevit import forms

def is_sheet_view(view):
    # Check if the active view is a sheet
    if not isinstance(view, ViewSheet):
        forms.alert("The active view is not a sheet. Please open a sheet to run this script.", exitscript=True)

# Collect the views on the current sheetviewports 
def get_views_on_sheet(doc, view):
    viewports = FilteredElementCollector(doc, view.Id).OfClass(Viewport).ToElements()
    views_on_sheet = []
    for viewport in viewports:
        view_id = viewport.ViewId
        view = doc.GetElement(view_id)

        # Exclude schedules and legends
        if view is not None and not isinstance(view, ViewSchedule):
            if view.ViewType != ViewType.Legend:  # Check the ViewType
                views_on_sheet.append(view)

    return views_on_sheet


# Determine the view type in a human-readable format
def determine_view_type(view): 
    if view.ViewType == ViewType.FloorPlan:
        return "Floor Plan"
    elif view.ViewType == ViewType.Section:
        return "Section"
    elif view.ViewType == ViewType.ThreeD:
        return "3D View"
    else:
        return "Other"  # Add other types as needed


# Show a selection form and return the selected view objects
def select_views(views_on_sheet):
    if views_on_sheet:
        # Prepare view names for selection
        view_names = [("[{}]: {}").format(determine_view_type(view), str(view.Name)) for view in views_on_sheet]

        # Show the selection form
        selected_view_names = forms.SelectFromList.show(sorted(view_names), title="Select a View", multiselect=True)

        if selected_view_names:
            # Find the selected view objects based on their names
            selected_views = [view for view in views_on_sheet if ("[{}]: {}".format(determine_view_type(view), view.Name)) in selected_view_names]

            # Return the actual selected view objects, not just their names
            return selected_views
    else:
        forms.alert("No views (excluding schedules and legends) are placed on the current sheet.", exitscript=True)
        return []