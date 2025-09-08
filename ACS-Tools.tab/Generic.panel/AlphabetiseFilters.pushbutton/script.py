from Autodesk.Revit.DB import FilteredElementCollector, Transaction, BuiltInCategory
from pyrevit import revit, forms

__title__ = "Alphabetise\nFilters"
__doc__ = ''' 
Description:\nThis tool retrieves the filters applied to the current view, removes them, sorts them alphabetically, and then re-applies them with the original overrides, visibility settings, and if they were enabled or not.
'''

# Access Revit document and active view
doc = revit.doc
active_view = revit.active_view

def get_filters_and_overrides(view):
    """Get the filters, their overrides, visibility, and enable filter states from the view."""
    filters = view.GetOrderedFilters()
    filter_info = []

    for filter_id in filters:
        # Get filter element
        filter_element = doc.GetElement(filter_id)

        # Get filter graphic overrides
        overrides = view.GetFilterOverrides(filter_id)

        # Get visibility and enable filter states
        is_visible = view.GetFilterVisibility(filter_id)

        # Get if the filter is enabled
        is_enabled = view.GetIsFilterEnabled(filter_id)

        filter_info.append((filter_element, overrides, is_visible, is_enabled))

    return filter_info

def remove_all_filters(view):
    """Remove all filters from the view."""
    filters = view.GetOrderedFilters()

    for filter_id in filters:
        view.RemoveFilter(filter_id)

def reapply_filters(view, sorted_filters):
    """Reapply filters to the view in sorted order, preserving the original overrides, visibility, and enable filter states."""
    for filter_element, overrides, is_visible, is_enabled in sorted_filters:
        # Add the filter back to the view
        view.AddFilter(filter_element.Id)

        # Set the graphic overrides
        view.SetFilterOverrides(filter_element.Id, overrides)

        # Set visibility and enable filter states
        view.SetFilterVisibility(filter_element.Id, is_visible)

        # Set if the filter is enabled 
        view.SetIsFilterEnabled(filter_element.Id, is_enabled)


def alphabetize_filters(view):
    """Main function to alphabetize filters in the active view."""
    # Step 1: Get the current filters, their overrides, and visibility states
    filter_info = get_filters_and_overrides(view)
    
    # Step 2: Sort the filters alphabetically by their name
    sorted_filters = sorted(filter_info, key=lambda x: x[0].Name)

    # Step 3: Remove all filters from the view
    remove_all_filters(view)

    # Step 4: Reapply the filters in sorted order, with their original overrides, visibility, and enable filter states
    reapply_filters(view, sorted_filters)

# Start a transaction to modify the view
with Transaction(doc, "Alphabetise Filters") as t:
    t.Start()
    alphabetize_filters(active_view)
    t.Commit()

forms.alert("Success! Filters have been alphabetised successfully, with visibility and overides preserved.", title="Success")
