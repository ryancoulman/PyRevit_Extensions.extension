# -*- coding: utf-8 -*-

__title__ = "Override In Dependents"

from pyrevit import revit, forms
from helefuncs import get_selected_elements, get_dependent_views

doc = revit.doc
active_view = doc.ActiveView
uidoc = revit.uidoc

# Main script logic
if __name__ == '__main__':

    dependent_views = get_dependent_views(doc, active_view)
    selected_elements = get_selected_elements(doc, uidoc)

    # Store the original graphics override of the selected elements from the active view
    overrides_map = {}
    for element in selected_elements:
        try:
            # Get the element-specific graphics override from the active view
            element_override = active_view.GetElementOverrides(element.Id)
            overrides_map[element.Id] = element_override
        except:
            pass
    
    if not overrides_map:
        forms.alert("None of the selected elements have graphics overrides in the active view.", exitscript=True)

    # Use a transaction to apply the overrides to all dependent views
    with revit.Transaction("Apply Graphic Overrides to Dependent Views"):
        for dependent_view in dependent_views:
            for element_id, override_settings in overrides_map.items():
                try:
                    # Apply the override settings to the element in the dependent view
                    dependent_view.SetElementOverrides(element_id, override_settings)
                except Exception as e:
                    # Handle cases where an element might not exist in a specific dependent view
                    print(e)

    print("Successfully applied graphic overrides to all dependent views")