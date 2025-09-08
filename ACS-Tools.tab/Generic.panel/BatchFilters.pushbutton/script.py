from view_handler import ViewHandler, FilterHandler
from main_helper import MainHelper
from helper_classes import ListItem
from helper_classes import CheckBoxState
import os

# .NET IMPORTS
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System")
from System.Collections.Generic import List
from System.Windows.Window import DragMove
from System.Windows.Input import MouseButtonState
from System.Windows import Window
import wpf


PATH_SCRIPT = os.path.dirname(__file__)
uidoc = __revit__.ActiveUIDocument
app   = __revit__.Application
doc   = __revit__.ActiveUIDocument.Document
app_year = int(app.VersionNumber)
# active_view = doc.ActiveView  # If user clicks in project browser then that becomes active view 
active_view = uidoc.ActiveGraphicalView # Get the active graphical view instead


class SelectFilters(Window):

    view_handler = ViewHandler(active_view, doc, uidoc)
    views = view_handler.return_initial_views() # Upon form initialisation 'views' will be displayed in first ListBox 

    def __init__(self):
        # Load Resources for WPF form 
        path_xaml_file = os.path.join(PATH_SCRIPT, 'CopyFilters.xaml')
        wpf.LoadComponent(self, path_xaml_file)

        # Update Text
        self.main_title.Text = "Sheet View Mode" if self.view_handler.is_sheet() else "Viewport Mode"
        self.footer_version.Text = "Showing All Project Filters" if self.view_handler.is_sheet() else "Showing Viewport Filters - Visibility Graphics Will Be Copied"

        # Set initial state of the 'Selected Views' checkbox
        self.UI_checkbox_selected.IsChecked = self.view_handler.is_selected_views_present()
        self.UI_checkbox_selected.IsEnabled = self.view_handler.is_selected_views_present()
        # Set initial state of the 'Only views on Sheet' checkbox
        self.UI_checkbox_views.IsChecked = self.view_handler.enable_views_on_sheet() if not self.view_handler.is_selected_views_present() else False
        self.UI_checkbox_views.IsEnabled = self.view_handler.enable_views_on_sheet() 

        # Update first ListBoxes with views 
        self.UI_ListBox_Src_Views.ItemsSource = self.views

        # Populate the second ListBoxes with all filters in project 
        filter_handler = FilterHandler(doc, active_view, self.view_handler.is_sheet())
        self.UI_ListBox_Filters.ItemsSource = filter_handler.return_filters()

        # REVIT
        self.ShowDialog()

    # ====================== GUI ELEMENTS =========================== #

    def button_close(self, sender, e):
        """Stop application by clicking on a <Close> button in the top right corner."""
        self.Close()

    def header_drag(self, sender, e):
        """Drag window by holding LeftButton on the header."""
        if e.LeftButton == MouseButtonState.Pressed:
            DragMove(self)

    def UI_event_checked_views(self, sender, e):
        """EventHandler for 'Only views on Sheet' checkbox"""
        # Views on sheet Only
        if self.UI_checkbox_views.IsChecked and not self.UI_checkbox_selected.IsChecked:
            self.views = self.view_handler.return_views_on_sheet()
        # Views on sheet and Selected views
        elif self.UI_checkbox_views.IsChecked and self.UI_checkbox_selected.IsChecked:
            self.views = self.view_handler.return_selected_and_sheet_views()
        # Selected views only 
        elif not self.UI_checkbox_views.IsChecked and self.UI_checkbox_selected.IsChecked:
            self.views = self.view_handler.return_selected_views()
        # All views
        else:
            self.views = self.view_handler.return_all_views()

        # Update Views Listbox
        self.UI_ListBox_Src_Views.ItemsSource = self.views

    def VisibilityCheckboxChanged(self, sender, e):
        """Event handler for multi selcting visibility checkboxes"""
        # CheckBox sender is the CheckBox that triggered the event
        is_checkbox_checked = sender.IsChecked
        selected_items = self.UI_ListBox_Filters.SelectedItems
        if selected_items.Count > 0:
            for item in selected_items:
                item.IsVisible = is_checkbox_checked
        
        self.UI_ListBox_Filters.Items.Refresh()

    def AddRemoveCheckboxChanged(self, sender, e):
        """Event handler for multi-selecting the three-way checkbox."""
        # The checkbox sender is the CheckBox that triggered the event
        # Get the ListItem associated with the checkbox sender
        changed_item = sender.DataContext  # Assuming sender is bound to ListItem
        # Determine the current ThreeWayState based on the checkbox's current state
        if changed_item.ThreeWayState == CheckBoxState.CHECKED or changed_item.ThreeWayState == True:
            new_state = 0  # Toggle to unchecked
        elif changed_item.ThreeWayState == CheckBoxState.UNCHECKED or changed_item.ThreeWayState == False:
            new_state = 1  # Toggle to indeterminate
        else:
            new_state = 2  # Toggle to checked

        conversion_list = [True, False, None]
        selected_items = self.UI_ListBox_Filters.SelectedItems
        if selected_items.Count > 0:
            for item in selected_items:
                item.ThreeWayState = conversion_list[new_state]
        
        self.UI_ListBox_Filters.Items.Refresh()


    def UI_text_filter_updated(self, sender, e):
        """Function to filter items in the UI_ListBox_Views."""
        filtered_list_of_items = List[type(ListItem())]()
        filter_keyword = self.textbox_filter.Text
        # Restore orginal list
        if not filter_keyword:
            self.UI_ListBox_Src_Views.ItemsSource = self.views
            return
        # Filter items
        for item in self.views:
            if filter_keyword.lower() in item.Name.lower():
                filtered_list_of_items.Add(item)
        # Update views
        self.UI_ListBox_Src_Views.ItemsSource = filtered_list_of_items

    def select_mode(self, mode):
        """Helper function for following buttons:
        - button_select_all
        - button_select_none"""

        list_of_items = List[type(ListItem())]()
        checked = True if mode=='all' else False
        for item in self.UI_ListBox_Src_Views.ItemsSource:
            item.IsChecked = checked
            list_of_items.Add(item)

        self.UI_ListBox_Src_Views.ItemsSource = list_of_items

    def button_select_all(self, sender, e):
        self.select_mode(mode='all')

    def button_select_none(self, sender, e):
        self.select_mode(mode='none')

    # Activates when 'Apply' Button pressed 
    def button_run(self, sender, e):
        self.Close()
        MainHelper(doc, active_view, self.UI_ListBox_Src_Views,self.UI_ListBox_Filters, self.view_handler.is_sheet())


# ===================== MAIN ============================= # 

if __name__ == '__main__':
    SelectFilters()