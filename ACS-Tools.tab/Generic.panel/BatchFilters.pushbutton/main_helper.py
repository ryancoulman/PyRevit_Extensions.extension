from Autodesk.Revit.DB import Transaction
from helper_classes import CheckBoxState
import traceback

class MainHelper:
    def __init__(self, doc, active_view, UI_ListBox_Src_Views, UI_ListBox_Filters, is_sheet):
        # Save variables
        self.doc = doc
        self.active_view = active_view
        self.UI_ListBox_Src_Views = UI_ListBox_Src_Views
        self.UI_ListBox_Filters = UI_ListBox_Filters
        self.is_sheet = is_sheet 
        # Main Logic
        self.selected_views, self.selected_filters = self.collect_states()
        self.print_selected()
        self.commit_transaction()

    def collect_states(self):
        """Collect final states of filters and views when Apply button is clicked."""
        selected_filters = {} # Format: {name: [item element, Selected, Visibility]}
        selected_views = []

        for item in self.UI_ListBox_Src_Views.Items:
            # Check if the checkbox is checked
            if item.IsChecked:
                selected_views.append(item.element)  # Store the associated element

        for item in self.UI_ListBox_Filters.Items:
            # Get the name of the filter
            filter_name = item.Name
            # Get the state of the first checkbox
            checkbox1_state = item.ThreeWayState 
            # Get the state of the second checkbox
            checkbox2_state = item.IsVisible  
            
            # If any checkbox1 (selected) is selected, add to selected filters
            if checkbox1_state != CheckBoxState.UNCHECKED:
                if checkbox1_state == CheckBoxState.CHECKED or checkbox1_state is True:
                    keep_add = True
                else:
                    keep_add = False
                selected_filters[filter_name] = [item.element, keep_add, checkbox2_state]  # [First Checkbox State, Second Checkbox State]

        return selected_views, selected_filters
    
    def print_selected(self):
        print('*** Destination Views: ***')
        for view in self.selected_views:
            print(view.Name)

        print('*** Selected Filters: ***')
        for f_name in self.selected_filters.keys():
            keep_remove = 'Keep / Add' if self.selected_filters[f_name][1] else 'Remove'
            print('{} {} - Visible: {} '.format(keep_remove, f_name, self.selected_filters[f_name][2]))

    def commit_transaction(self):
        with Transaction(self.doc, "Batch View Filters") as t:
            t.Start()
            for view in self.selected_views:
                for filter in self.selected_filters.values():
                    filter_id, add_keep, visible = filter[0].Id, filter[1], filter[2]
                    try:
                        if add_keep:
                            # Add the filter if not applied in view 
                            if not view.IsFilterApplied(filter_id):
                                view.AddFilter(filter_id)
                            if not self.is_sheet:
                                # Copy filter overide from active view if not a sheet
                                active_view_overides = self.active_view.GetFilterOverrides(filter_id)
                                view.SetFilterOverrides(filter_id, active_view_overides)
                            # Set the filter's visibility to that selected 
                            view.SetFilterVisibility(filter_id, visible)
                        else:
                            # Remove filter if applied to the view
                            if view.IsFilterApplied(filter_id):
                                view.RemoveFilter(filter_id)

                    except:
                        print(traceback.format_exc())
            t.Commit()

        print('\nExecution Completed.')

        