from Autodesk.Revit.DB import FilteredElementCollector, TextElementType, IndependentTag, BuiltInParameter
from pyrevit import forms
import re 


class TagManager:
    def __init__(self, doc, active_view):
        self.doc = doc
        self.active_view = active_view

    def get_all_tags_in_view(self):
        """Get all annotation tags in the active view."""
        # Collect all tags in the project
        collector = FilteredElementCollector(self.doc).OfClass(IndependentTag)
        # print("Total tags found: {}".format(collector.GetElementCount()))
        # Store all tags to be processed in a list to avoid modifying the collection while iterating
        tags_to_process = []
        for tag in collector:
            if tag.OwnerViewId == self.active_view.Id and not tag.IsHidden(self.active_view):
                tags_to_process.append(tag)

        if not tags_to_process:
            forms.alert("No annotation tags are selected.", exitscript=True)

        print("Processing {} tags in the active view.".format(len(tags_to_process)))

        return tags_to_process
    
    def get_selected_annotation_tags(self, uidoc):
        """Get all annotation tags selected by the user."""
        
        # Get the currently selected elements in the active view
        selected_elements = self.get_selected_elements(uidoc)
        
        # Filter the selected elements to only include annotation tags
        tags_to_process = []
        for tag in selected_elements:
            if isinstance(tag, IndependentTag):
                tags_to_process.append(tag)
        
        if not tags_to_process:
            forms.alert("No annotation tags are selected.", exitscript=True)
        
        print("Processing {} selected tags.".format(len(tags_to_process)))

        return tags_to_process
    
    def get_selected_elements(self, uidoc):
        """Property that retrieves selected views or promt user to select some from the dialog box."""
        doc = uidoc.Document
        selection = uidoc.Selection  

        try:
            selected_elements = [doc.GetElement(e_id) for e_id in selection.GetElementIds()]
            if not selected_elements:
                forms.alert("No elements  were selected.\nPlease, try again.", exitscript=True)
        except:
            return

        return selected_elements


class TextStyle:
    def __init__(self, doc):
        self.text_styles = self.get_all_text_styles(doc)

    def get_all_text_styles(self, doc):
        """Get all text styles in the Revit project using TextElementType."""
        
        # Collect all TextElementType elements
        text_style_elements = FilteredElementCollector(doc).OfClass(TextElementType).ToElements()

        # Dictionary to store unique text style names and objects
        text_styles = {}

        for text_style in text_style_elements:
            # Access the name via the parameter BuiltInParameter.ALL_MODEL_TYPE_NAME
            param = text_style.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME)
            if param:
                text_styles[param.AsString()] = text_style

        # Check if no text styles were found
        if not text_styles:
            forms.alert("No text styles found.", exitscript=True)

        return text_styles

    def sort_text_styles(self, text_style_names):
        """Sort a list of text style names based on the numerical font size."""

        def extract_font_size(text_style_name):
            """Extract the numerical font size from the text style name."""
            # Use a regular expression to find the number at the start of the string
            match = re.match(r"(\d+(\.\d+)?)mm", text_style_name)
            if match:
                # Return the matched number as a float for proper numeric sorting
                return float(match.group(1))
            return float('inf')  # Return a large number if no match (to handle any exceptions)

        # Sort the list using the custom key function
        return sorted(text_style_names, key=extract_font_size)

    
    def select_style(self): 
        # Get all the keys (text style names) from the dictionary and sort 
        sorted_style_names = self.sort_text_styles(list(self.text_styles.keys()))
        # Let the user select from the available text styles
        selected_option = forms.SelectFromList.show(sorted_style_names, multiselect=False, title="Choose Text Style for Plain Text Notes")
        if selected_option:
            # Return the selected text style object
            return self.text_styles[selected_option]
        return None  # Return None if no option was selected

    def get_selected_style_id(self):
        """Get the ElementId of the selected text style."""
        selected_style = self.select_style()  # Get the selected style from the user
        if selected_style:
            # Return the ElementId of the selected text style
            return selected_style.Id
        return None  # Return None if no text style was selected


