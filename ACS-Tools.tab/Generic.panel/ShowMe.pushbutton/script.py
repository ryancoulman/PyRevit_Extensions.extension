from pyrevit import revit, forms
from Autodesk.Revit.DB import ElementId
from pyrevit.framework import wpf
from System.Windows import Window, MessageBox
from wpf_helper import get_wpf_path
from System.Collections.Generic import List

doc = revit.doc
uidoc = revit.uidoc

def get_selected_elements():
    '''Returns a dictionary of currently selected elements {Family Name + Type (ID): elemID}'''
    # Get selected elements from the current Revit selection
    selected_elements = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds()]

    if not selected_elements:
        # Alert if nothing is selected
        forms.alert("No elements selected", title="Element Viewer", exitscript=True)
        return
    
    selected_dict = {}
    for elem in selected_elements:
        # Get family and type names, handle missing attributes
        fam_name = getattr(elem.Symbol.Family, "Name", "Unknown Family") \
                   if hasattr(elem, "Symbol") else "Unknown Family"
        type_name = getattr(elem, "Name") \
                    if hasattr(elem, "Name") else "Unknown Type"
        key_name = "{} : {} (ID: {})".format(fam_name, type_name, elem.Id.IntegerValue)
        selected_dict[key_name] = elem

    return selected_dict


class ElementViewer(Window):
    def __init__(self, elements=None):
        # Load WPF UI from XAML
        xaml_path = get_wpf_path("ElementViewer.xaml")
        wpf.LoadComponent(self, xaml_path)

        self.elements = elements
        self.currentIndex = 0

        # Set up listbox with element keys
        self.listbox = self.FindName("elements_lb")
        self.listbox.ItemsSource = self.elements.keys()

        if self.listbox.Items.Count > 0:
            self.listbox.SelectedIndex = self.currentIndex

        # Attach button and listbox event handlers
        self.prev_b.Click += self.prev_b_click
        self.next_b.Click += self.next_b_click
        self.show_b.Click += self.show_b_click
        self.listbox.SelectionChanged += self.listbox_selection_changed
        self.Closing += self.on_closing

    def prev_b_click(self, sender, args):
        # Select previous element in the list
        if self.listbox.Items.Count == 0:
            return
        self.currentIndex = (self.currentIndex - 1 + self.listbox.Items.Count) % self.listbox.Items.Count
        self.listbox.SelectedIndex = self.currentIndex

    def next_b_click(self, sender, args):
        # Select next element in the list
        if self.listbox.Items.Count == 0:
            return
        self.currentIndex = (self.currentIndex + 1) % self.listbox.Items.Count
        self.listbox.SelectedIndex = self.currentIndex

    def show_b_click(self, sender, args):
        # Show the selected element in Revit
        selected_elem_name = self.listbox.SelectedItem
        selected_elem = self.elements[selected_elem_name]
        try:
            uidoc.ShowElements(selected_elem)
        except Exception as e:
            MessageBox.Show("Could not show element: {}.\nError: {}".format(selected_elem_name, e))

    def listbox_selection_changed(self, sender, args):
        # Update current index when selection changes by user clicking on a row
        if self.listbox.Items.Count == 0:
            return
        self.currentIndex = self.listbox.SelectedIndex

    def on_closing(self, sender, e):
        # Close the window
        self.Close()


if __name__ == "__main__":
    # Main entry: get selected elements and show the viewer window
    selected_dict = get_selected_elements()
    if selected_dict:
        ElementViewer(selected_dict).ShowDialog()
    else:
        forms.alert("No elements selected", title="Element Viewer", exitscript=True)
