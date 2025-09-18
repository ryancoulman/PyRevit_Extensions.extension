from pyrevit import forms, revit
from helefuncs import get_selected_elements
import os

doc = revit.doc
uidoc = revit.uidoc

class ElementViewer(forms.TemplateUserInputWindow):
    """Simple next/prev viewer for Revit elements."""

    def __init__(self, elements):
        self.elements = elements
        self.current_index = 0

        # Pass the XAML file path directly
        xaml_file = os.path.join(os.path.dirname(__file__), "ElementViewer.xaml")
        super(ElementViewer, self).__init__(xaml_file, title="Element Viewer", width=400, height=150)

        # Attach controls
        self.display_tb = self.FindName("display_tb")
        self.next_b = self.FindName("next_b")
        self.prev_b = self.FindName("prev_b")
        self.close_b = self.FindName("close_b")

        # Attach button handlers
        self.next_b.Click += self.next_element
        self.prev_b.Click += self.prev_element
        self.close_b.Click += self.close_window

        # Show first element
        self.update_display()

    def update_display(self):
        if not self.elements:
            self.display_tb.Text = "No elements selected"
            self.next_b.IsEnabled = False
            self.prev_b.IsEnabled = False
            return

        elem = self.elements[self.current_index]
        fam_name = getattr(elem.Symbol.Family, "Name", "Unknown Family") \
                   if hasattr(elem, "Symbol") else "Unknown Family"
        type_name = getattr(elem.Symbol, "Name", "Unknown Type") \
                    if hasattr(elem, "Symbol") else "Unknown Type"
        self.display_tb.Text = "{} : {}".format(fam_name, type_name)

        # Enable/disable buttons at bounds
        self.prev_b.IsEnabled = self.current_index > 0
        self.next_b.IsEnabled = self.current_index < len(self.elements) - 1

    # Button handlers
    def next_element(self, sender, args):
        self.current_index += 1
        self.update_display()

    def prev_element(self, sender, args):
        self.current_index -= 1
        self.update_display()

    def close_window(self, sender, args):
        self.Close()


# Show the viewer
sel = get_selected_elements(doc, uidoc)
viewer = ElementViewer(sel)
viewer.show(modal=False)
