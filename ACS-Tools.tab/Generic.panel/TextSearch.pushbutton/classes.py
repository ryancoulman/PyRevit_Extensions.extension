from Autodesk.Revit.DB import FilteredElementCollector, ElementId, TextNote, IndependentTag
from pyrevit.framework import wpf
from System.Windows import Window, MessageBox
from wpf_helper import get_wpf_path
from pyrevit import forms
from System.Collections.Generic import List
import re

MATCH_OPS = {
    "MATCH_ENTIRE": "Entire text",
    "MATCH_BEGINNING": "Beginning only",
    "MATCH_ANYWHERE": "Anywhere within"
}

class SearchData(object):
    '''Class to hold search parameters'''
    def __init__(self, text='Null', match_mode='Null', include_regex=False, match_case=False, include_annotation_tags=False):
        self.text = text
        self.match_mode = match_mode
        self.include_regex = include_regex
        self.match_case = match_case
        self.include_annotation_tags = include_annotation_tags


class FormHandlerNEW(Window):
    def __init__(self):
        xaml_path = get_wpf_path("SearchText.xaml")
        wpf.LoadComponent(self, xaml_path)

        # Populate combo box with options
        self.MatchComboBox.ItemsSource = list(MATCH_OPS.values())
        self.MatchComboBox.SelectedItem = MATCH_OPS["MATCH_ENTIRE"]
        
        # Attach event handler for the Search button
        self.SearchButton.Click += self.SearchButton_Click
        # Attach event handler for window closing
        self.Closing += self.on_closing

        # Initialize search data
        self.search_data = None

        self.ShowDialog()

    def SearchButton_Click(self, sender, args):
        # Get entered text
        entered_text = self.InputTextBox.Text
        if not entered_text:
            MessageBox.Show("Please enter text to search for.", "Input Required")
            return

        # Get selected combo box value
        selected_combo = self.MatchComboBox.SelectedItem
        combo_text = selected_combo.Content if selected_combo else ""

        # Get checkbox states
        is_regex = self.RegexCheckBox.IsChecked
        is_match_case = self.MatchCaseCheckBox.IsChecked
        is_annotation_tags = self.AnnotationTagsCheckBox.IsChecked

           # Create the data object
        self.search_data = SearchData(
            text=entered_text,
            match_mode=combo_text,
            include_regex=is_regex,
            match_case=is_match_case,
            include_annotation_tags=is_annotation_tags
        )

        self.Close()  # Close the form after processing

    def return_search_data(self):
        return self.search_data

    def on_closing(self, sender, args):
        self.Close()
    
class FormHandler():
    MATCH_ENTIRE_WORD = "Match Entire Text Note"
    MATCH_BEGINNING_ONLY = "Match Beginning Only"
    MATCH_WITHIN_ONLY = "Match Anywhere Within Text"
    MATCH_REGEX = "Match Using Regex"
    MATCH_CASE = "Match Case"
    ANNOTATION_TAGS = "Inlclude Annotation Tags"

    def __init__(self, document, view):
        self.doc = document
        self.active_view = view
        self.options = [self.MATCH_ENTIRE_WORD, self.MATCH_BEGINNING_ONLY, self.MATCH_WITHIN_ONLY, self.MATCH_REGEX, self.MATCH_CASE, self.ANNOTATION_TAGS]
        self.selected_options = self.call_form()

    def call_form(self):
        selected_options = forms.SelectFromList.show(self.options, title="Advanced Search Options", multiselect=True)
        # Check the user has not selected contracdictory options 
        count = sum([s in selected_options for s in [self.MATCH_ENTIRE_WORD, self.MATCH_BEGINNING_ONLY, self.MATCH_WITHIN_ONLY, self.MATCH_REGEX]])
        if count > 1:
            c
        if not any(item in [self.MATCH_ENTIRE_WORD, self.MATCH_BEGINNING_ONLY, self.MATCH_WITHIN_ONLY, self.MATCH_REGEX] for item in selected_options):
            forms.alert("Please select how you wish to search the text.", exitscript=True)
        return selected_options

    def get_selected_options(self):
        if self.selected_options:
            return self.selected_options
        else:
            forms.alert('No options selected', exitscript=True)
            return None 
        
    def get_search_string(self):
        search_term = forms.ask_for_string(
            prompt='Enter the text string to search for:', 
            title='Search Text in View'
        )
        if search_term:
            return search_term
        else:
            forms.alert('No text given', exitscript=True)
            return None
        


def check_selected(doc, uidoc):
    """Return a list of strings for selected TextNotes, or alert if none."""
    sel_ids = uidoc.Selection.GetElementIds()
    text_notes = []
    for eid in sel_ids:
        elem = doc.GetElement(eid)
        if isinstance(elem, TextNote):
            text_notes.append(elem.Text)
    
    if text_notes:
     return text_notes[0]
    else:
        return text_notes        

class TextHandler():
    def __init__(self, document, view, ui_document, search_data):
        self.uidoc = ui_document
        self.doc = document
        self.view = view
        self.search_data = search_data
        # Collect all text notes in given view
        self.text_notes = FilteredElementCollector(self.doc, self.view.Id)\
                            .OfClass(TextNote)\
                            .WhereElementIsNotElementType()\
                            .ToElements()
        if self.search_data.include_annotation_tags:
            self.annotation_tags = FilteredElementCollector(self.doc, self.view.Id) \
                                .OfClass(IndependentTag) \
                                .WhereElementIsNotElementType() \
                                .ToElements()

    def search_text(self):
        
        def checker(text_note, text):
            if match_mode == MATCH_OPS["MATCH_ENTIRE"] and (text.strip() == search_term.strip()):
                matching_text_notes.Add(text_note.Id)
            elif match_mode == MATCH_OPS["MATCH_BEGINNING"] and text.startswith(search_term):
                matching_text_notes.Add(text_note.Id)
            elif match_mode == MATCH_OPS["MATCH_ANYWHERE"] and search_term in text:
                matching_text_notes.Add(text_note.Id)
            elif self.search_data.include_regex:
                re_search_term = r'{}'.format(search_term)
                if re.search(re_search_term, text):
                    matching_text_notes.Add(text_note.Id)
                
        # List to hold matching elements
        matching_text_notes = List[ElementId]()

        # Store search term and match mode for easier access
        search_term = self.search_data.text
        match_mode = self.search_data.match_mode

        # Set all text to lower case if user did not select 'Match Case'
        lower = not self.search_data.match_case
        if lower:
            self.search_data.text = self.search_data.text.lower()

        for text_note_object in self.text_notes:
            # Get the plain text from the text note object
            plain_text = text_note_object.Text
            # Convert the plain text to lowercase if selected
            if lower:
                plain_text = plain_text.lower()
            # Pass objects to the checker
            checker(text_note_object, plain_text)

        if self.search_data.include_annotation_tags:
            for tag_object in self.annotation_tags:
                # Get the plain text from the tag object
                plain_text = tag_object.TagText
                # Convert the plain text to lowercase if selected
                if lower:
                    plain_text = plain_text.lower()
                # Pass objects to the checker
                checker(tag_object, plain_text)

        if matching_text_notes.Count > 0:
            return matching_text_notes
        else:
            forms.alert("No matching text notes found.", title="Search Completed", exitscript=True)
            return None
        
    def highlight_selected_text(self, matching_text_notes, search_term):
        self.uidoc.Selection.SetElementIds(matching_text_notes)
        forms.alert("{} text notes matching '{}' have been found and selected.".format(matching_text_notes.Count, search_term), title="Search Completed")


def checker(text_note, text, search_term, match_mode, use_regex, matching_text_notes):
    if use_regex:
        # Build regex pattern based on match_mode
        if match_mode == MATCH_OPS["MATCH_ENTIRE"]:
            pattern = r'^{}$'.format(re.escape(search_term))
        elif match_mode == MATCH_OPS["MATCH_BEGINNING"]:
            pattern = r'^{}'.format(re.escape(search_term))
        elif match_mode == MATCH_OPS["MATCH_ANYWHERE"]:
            pattern = re.escape(search_term)
        elif match_mode == MATCH_OPS["MATCH_WORD"]:
            pattern = r'\b{}\b'.format(re.escape(search_term))
        else:
            pattern = re.escape(search_term)

        if re.search(pattern, text):
            matching_text_notes.Add(text_note.Id)
    else:
        
        # Your original logic
        if match_mode == MATCH_OPS["MATCH_ENTIRE"] and (text.strip() == search_term.strip()):
            matching_text_notes.Add(text_note.Id)
        elif match_mode == MATCH_OPS["MATCH_BEGINNING"] and text.startswith(search_term):
            matching_text_notes.Add(text_note.Id)
        elif match_mode == MATCH_OPS["MATCH_ANYWHERE"] and search_term in text:
            matching_text_notes.Add(text_note.Id)