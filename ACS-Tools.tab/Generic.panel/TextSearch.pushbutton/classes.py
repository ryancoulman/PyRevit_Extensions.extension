from Autodesk.Revit.DB import FilteredElementCollector, ElementId, TextNote, IndependentTag
from pyrevit import forms
from System.Collections.Generic import List
import re


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
            forms.alert("Contradictory criteria selected.", exitscript=True)
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
    def __init__(self, document, view, ui_document, choosen_options):
        self.uidoc = ui_document
        self.doc = document
        self.active_view = view
        self.selected_options = choosen_options
        # Collect all text notes in active view
        self.text_notes = FilteredElementCollector(self.doc, self.active_view.Id)\
                            .OfClass(TextNote)\
                            .WhereElementIsNotElementType()\
                            .ToElements()
        if (FormHandler.ANNOTATION_TAGS in self.selected_options):
            self.annotation_tags = FilteredElementCollector(self.doc, self.active_view.Id) \
                                .OfClass(IndependentTag) \
                                .WhereElementIsNotElementType() \
                                .ToElements()

    def search_text(self, search_term):

        def checker(text_note, text):
            if (FormHandler.MATCH_ENTIRE_WORD in self.selected_options) and (text.strip() == search_term.strip()):
                matching_text_notes.Add(text_note.Id)
            elif (FormHandler.MATCH_BEGINNING_ONLY in self.selected_options) and text.startswith(search_term):
                matching_text_notes.Add(text_note.Id)
            elif (FormHandler.MATCH_WITHIN_ONLY in self.selected_options) and search_term in text:
                matching_text_notes.Add(text_note.Id)
            elif (FormHandler.MATCH_REGEX in self.selected_options):
                re_search_term = r'{}'.format(search_term)
                if re.search(re_search_term, text):
                    matching_text_notes.Add(text_note.Id)
                
         # List to hold matching elements
        matching_text_notes = List[ElementId]()

        # Set all text to lower case if user did not select 'Match Case'
        if FormHandler.MATCH_CASE not in self.selected_options:
            lower = True
            search_term = search_term.lower()

        for text_note_object in self.text_notes:
            # Get the plain text from the text note object
            plain_text = text_note_object.Text
            # Convert the plain text to lowercase if selected
            if lower:
                plain_text = plain_text.lower()
            # Pass objects to the checker
            checker(text_note_object, plain_text)

        if (FormHandler.ANNOTATION_TAGS in self.selected_options):
            for tag_object in self.annotation_tags:
                # Get the plain text from the text note object
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
            

