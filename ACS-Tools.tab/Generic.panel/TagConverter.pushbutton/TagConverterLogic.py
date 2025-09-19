from Autodesk.Revit.DB import FilteredElementCollector, TextElementType, IndependentTag, BuiltInParameter, ElementId
from pyrevit import forms
import re 
import os
import json


class TagManager:
    def __init__(self, doc):
        self.doc = doc

    def get_all_tags_in_view(self, view):
        """Get all annotation tags in the view."""
        # Collect all tags in the project
        collector = FilteredElementCollector(self.doc).OfClass(IndependentTag)
        # Store all tags to be processed in a list to avoid modifying the collection while iterating
        tags_to_process = []
        for tag in collector:
            if tag.OwnerViewId == view.Id and not tag.IsHidden(view):
                tags_to_process.append(tag)

        print("##### Processing {} tags in {} ######".format(len(tags_to_process), view.Name))

        return tags_to_process
    
    def get_selected_annotation_tags(self, selected_elements):
        """Get all annotation tags selected by the user."""
        
        # Filter the selected elements to only include annotation tags
        tags_to_process = []
        for tag in selected_elements:
            if isinstance(tag, IndependentTag):
                tags_to_process.append(tag)
        
        if not tags_to_process:
            forms.alert("No annotation tags are selected.", exitscript=True)
        
        print("Processing {} selected tags.".format(len(tags_to_process)))

        return tags_to_process
    


class TextStyle:
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "text_style.json")

    def __init__(self, doc, setting_default=False):
        self.doc = doc
        # Get all text styles in the project
        self.text_styles = self.get_all_text_styles(doc)

        # Read json config and fetch parameters
        self.config = self._load_config()
        default_style_id = self.get_configured_style_id()
        ask_every_time = self.should_ask_every_time()

        # If no default saved OR user wants to be asked each time OR default style not in project, prompt user to select
        if default_style_id is None or ask_every_time or not self.is_default_in_project():
            selected_style = self.select_style()
            if not selected_style:
                forms.alert("No text style selected. Exiting.", exitscript=True)

            self.selected_style_id = selected_style.Id

            # Ask whether to save as default (if they have not shift + click to set default)
            if not setting_default:
                if forms.alert("Use this text style as default?", yes=True, no=True):
                    self.set_default_text_style(self.selected_style_id, ask_every_time=False)
        else:
            self.selected_style_id = default_style_id

    # --- Configuration handling ---

    def _load_config(self):
        if os.path.exists(self.CONFIG_PATH):
            with open(self.CONFIG_PATH, "r") as f:
                return json.load(f)
        return {}

    def save_config(self):
        with open(self.CONFIG_PATH, "w") as f:
            json.dump(self.config, f, indent=4)

    def get_configured_style_id(self):
        val = self.config.get("default_text_style_id")
        return ElementId(int(val)) if val is not None else None

    def should_ask_every_time(self):
        return self.config.get("ask_every_time", True)

    def set_default_text_style(self, style_id, ask_every_time):
        self.config["default_text_style_id"] = style_id.IntegerValue
        self.config["ask_every_time"] = ask_every_time
        self.save_config()

    # ---- Methods to handle text styles ----

    def get_all_text_styles(self, doc):
        """Get all text styles in the Revit project using TextElementType.
        Returns a dictionary with text style names as keys and TextElementType objects as values."""
        
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
    
    def is_default_in_project(self):
        """Check if the default text style is still in the project."""
        default_style_id = self.get_configured_style_id()
        text_style_ids = [ts.Id for ts in self.text_styles.values()]
        if default_style_id and default_style_id in text_style_ids:
            return True
        return False
    
    @property
    def return_selected_style(self):
        """Return the selected text style object."""
        return self.selected_style_id  # May return None if no style was selected


