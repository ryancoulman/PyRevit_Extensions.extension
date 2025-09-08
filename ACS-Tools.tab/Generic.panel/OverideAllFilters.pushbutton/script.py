from Autodesk.Revit.DB import FilteredElementCollector, Transaction, BuiltInCategory, ViewType
from pyrevit import revit, forms
import traceback

__title__ = "Overide All\nFilters"
__doc__ = ''' 
Description:\nThis tolol allows you to copy the graphics overides for selected filters in the current view and pastes them to all views containing the filter.
\n
Instructions:\nActivate tool inside a view with your desired filter overides. Select the filters you wish to copy and it will paste the overides in all views and view templates containing this filter.
'''

# Access Revit document and active view
doc = revit.doc
active_view = revit.active_view  # Get the active view the user is in

def select_filters(view):
    """Function to get applied filters from the given view."""
    filter_ids = view.GetOrderedFilters()  # Get all filter IDs applied to the view
    filters = [doc.GetElement(e_id) for e_id in filter_ids]  # Retrieve filter elements from the IDs
    dict_filters = {f.Name: f for f in filters}  # Create a dictionary with filter names

    # Let the user select filters from the active view
    selected_filters = forms.SelectFromList.show(
        sorted(dict_filters.keys()),
        multiselect=True,
        title="Select Filters"
    )

    if not selected_filters:
        forms.alert("No filters were selected.\nPlease try again.", exitscript=True)
    
    # Return the selected filters
    return [dict_filters[name] for name in selected_filters]

def get_filter_overrides(view, filters):
    """Function to get the current overrides for the selected filters in the given view."""
    overrides_info = {}
    
    for filter in filters:
        try:
            # Get the graphic overrides for the current filter in the view
            overrides = view.GetFilterOverrides(filter.Id)
            overrides_info[filter.Id] = overrides  # Store the overrides by filter ID
        except Exception as e:
            print("Error retrieving overrides for filter '{}': {}".format(filter.Name, traceback.format_exc()))
    
    return overrides_info

def apply_overrides_to_all_views(filters, overrides_info):
    """Function to apply the filter overrides to all views and view templates where the filters are present."""
    # Get all views and view templates in the project
    all_views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()

    applied_views = {
        'Floor Plan': [],
        'Section': [],
        '3D View': [],
        'View Template': []
    }

    with Transaction(doc, "Apply Filter Overrides to All Views and Templates") as t:
        t.Start()

        for view in all_views:
            # Get filters in the current view
            view_filters = view.GetOrderedFilters()

            # Determine view type
            view_type = "Unknown"
            if view.IsTemplate:
                view_type = "View Template"
            elif view.ViewType == ViewType.FloorPlan:
                view_type = "Floor Plan"
            elif view.ViewType == ViewType.Section:
                view_type = "Section"
            elif view.ViewType == ViewType.ThreeD:
                view_type = "3D View"
            
            # Apply overrides for each filter that exists in both the current view and the selected filters
            for filter in filters:
                if filter.Id in view_filters:
                    try:
                        # Apply the saved overrides to this view or template
                        view.SetFilterOverrides(filter.Id, overrides_info[filter.Id])
                        applied_views[view_type].append(view.Name)
                    except Exception as e:
                        print("Error applying overrides to view '{}': {}".format(view.Name, traceback.format_exc()))

        t.Commit()

    print_applied_views(applied_views)


def print_applied_views(my_dict):
    # Sort dictionary alphabetically 
    applied_views = {key: my_dict[key] for key in sorted(my_dict)}
    
    # Count how many of each instance 
    floor_plan_count = len(applied_views.get('Floor Plan', []))
    section_count = len(applied_views.get('Section', []))
    threeD_count = len(applied_views.get('3D View', []))
    view_template_count = len(applied_views.get('View Template', []))
    
    print('*' * 100)
    print('The filter has been applied to the following number of views:')
    print("Count of Floor Plans: {}".format(floor_plan_count))
    print("Count of Sections: {}".format(section_count))
    print("Count of 3D Views: {}".format(threeD_count))
    print("Count of View Templates: {}".format(view_template_count))
    print('*' * 100)
    
    # Print all views filter has been applied to 
    # print('All views filter has been applied to: ')
    # for key, values in applied_views.items():
    #     for value in values:
    #         print('[{}]: {}'.format(key, value))


    
# Get the filters from the active view
selected_filters = select_filters(active_view)
print("Selected Filters:")
for filter in selected_filters:
    print(filter.Name)

# Get the overrides for the selected filters in the active view
overrides = get_filter_overrides(active_view, selected_filters)

# # Apply the same overrides to all views and view templates that contain the selected filters
apply_overrides_to_all_views(selected_filters, overrides)

print("Overrides have been successfully applied to all relevant views and view templates.")
