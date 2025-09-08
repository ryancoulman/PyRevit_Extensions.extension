
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Viewport, ViewType, ViewSheet, ParameterFilterElement
from pyrevit import forms
from create_list import create_List
from get_viewSheet import GetViewSheet
from helefuncs import get_selected_views

class ViewHandler:
    def __init__(self, active_view, doc, uidoc):
        # Initialise variables 
        self.active_view = active_view
        self.doc = doc
        self.uidoc = uidoc
        self.is_sheet_view = isinstance(active_view, ViewSheet)
        self.enable_sheet_views = self.is_sheet_view
        self.is_selected_views = False

        # Collect all views in project (including view templates) 
        all_views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).ToElements()
        all_views_with_filters      = [v for v in all_views if v.GetFilters() and not v.IsTemplate]
        if get_selected_views(uidoc, doc):
            selected_views = get_selected_views(uidoc, doc)
            selected_views = [v for v in selected_views if v.GetFilters() and not v.IsTemplate]
            self.is_selected_views = True
        if self.is_sheet_view:
            views_on_current_sheet = self.get_views_on_sheet(self.active_view)
        else:
            get_view_sheet = GetViewSheet(active_view, doc, print_sheet=False)
            if get_view_sheet.get_sheet():
                # Get other views on sheet if the view is placed on a sheet 
                sheet_view = get_view_sheet.get_sheet()
                views_on_current_sheet = self.get_views_on_sheet(sheet_view)
                # Update to enable views on sheet 
                self.enable_sheet_views = True

        # Check there is at least one view else exit script
        self.check_if_views(all_views_with_filters)
        # Create Dict of Views
        dict_all_views = self.get_dict_views(all_views_with_filters)
        # Convert Dict into List[ListItem]() for ListBox
        self.List_all_views = create_List(dict_all_views)

        if self.enable_sheet_views:
            dict_views_on_sheet = self.get_dict_views(views_on_current_sheet)
            self.List_views_on_sheet = create_List(dict_views_on_sheet)
        if self.is_selected_views:
            dict_selected_views = self.get_dict_views(selected_views)
            self.List_selected_views = create_List(dict_selected_views)
        if self.enable_sheet_views and self.is_selected_views:
            dict_selected_and_sheet_views = self.get_dict_views(views_on_current_sheet + selected_views)
            self.List_selected_and_sheet_views = create_List(dict_selected_and_sheet_views)

    def get_views_on_sheet(self, view):
            # Collect all views on the sheet
            views_on_sheet = FilteredElementCollector(self.doc, view.Id).OfClass(Viewport).ToElements()
            # Filter views to only contain views with filters and remove view templates 
            views_on_current_sheet = [self.doc.GetElement(v.ViewId) for v in views_on_sheet if self.doc.GetElement(v.ViewId).ViewType != ViewType.Legend and self.doc.GetElement(v.ViewId).ViewType != ViewType.Schedule]
            return views_on_current_sheet

    def is_sheet(self):
        return self.is_sheet_view
    
    def is_selected_views_present(self):
        return self.is_selected_views 
    
    def enable_views_on_sheet(self):
        return self.enable_sheet_views 

    def check_if_views(self, all_views_with_filters):
        if not all_views_with_filters:
            forms.alert("There are no Views or ViewTemplates with Filters applied to them! "
                        "\nPlease add some View Filters and Try Again.", exitscript=True)
            
    def get_dict_views(self, view_selection):
        """ Function to get and sort Views in a dict based on a mode setting.
            return:     dict of views with [ViewType] as a prefix."""
        
        dict_views = {}

        for view in view_selection:
            if view.ViewType == ViewType.FloorPlan:
                dict_views['[FLOOR] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.CeilingPlan:
                dict_views['[CEIL] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.ThreeD:
                dict_views['[3D] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Section:
                dict_views['[SEC] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Elevation:
                dict_views['[EL] {}'.format(view.Name)] = view

            elif view.ViewType ==ViewType.DraftingView:
                dict_views['[DRAFT] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.AreaPlan:
                dict_views['[AREA] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Rendering:
                dict_views['[CAM] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Legend:
                dict_views['[LEG] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.EngineeringPlan:
                dict_views['[STR] {}'.format(view.Name)] = view

            elif view.ViewType == ViewType.Walkthrough:
                dict_views['[WALK] {}'.format(view.Name)] = view

            else:
                dict_views['[?] {}'.format(view.Name)] = view

        return dict_views
    
    def return_views_on_sheet(self):
        if self.enable_sheet_views:
            return self.List_views_on_sheet
        else:
            return None
    
    def return_selected_views(self):
        if self.is_selected_views:
            return self.List_selected_views
        else:
            return None
        
    def return_selected_and_sheet_views(self):
        if self.enable_sheet_views and self.is_selected_views:
            return self.List_selected_and_sheet_views
        else:
            return None
    
    def return_all_views(self):
        return self.List_all_views
    
    def return_initial_views(self):
        if self.enable_sheet_views and self.is_selected_views:
            return self.List_selected_and_sheet_views
        elif self.enable_sheet_views and not self.is_selected_views:
            return self.List_views_on_sheet
        elif not self.enable_sheet_views and self.is_selected_views:
            return self.is_selected_views
        else:
            return self.List_all_views
    

class FilterHandler:
    def __init__(self, doc, active_view, is_sheet_view):
        if is_sheet_view: # return all filters in project 
            all_filters = FilteredElementCollector(doc).OfClass(ParameterFilterElement).ToElements()
        else:
            # Only get filters in active view 
            filters_in_active_view_ids = active_view.GetFilters()
            all_filters = [doc.GetElement(filter_id) for filter_id in filters_in_active_view_ids]
        
        dict_filters = {f.Name: f for f in all_filters}
        self.List_filters = create_List(dict_filters)

    def return_filters(self):
        return self.List_filters