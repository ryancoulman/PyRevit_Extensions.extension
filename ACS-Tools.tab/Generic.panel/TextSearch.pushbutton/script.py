from Autodesk.Revit.DB import Transaction
from pyrevit import revit
from classes import FormHandler, TextHandler, check_selected

doc = revit.doc
uidoc = revit.uidoc
active_view = revit.active_view


if __name__ == "__main__":

    if check_selected(doc, uidoc):
        selected_options = FormHandler.MATCH_ENTIRE_WORD
        search_term = check_selected(doc, uidoc)
    else:
        form_handler = FormHandler(doc, active_view)
        selected_options = form_handler.get_selected_options()
        search_term = form_handler.get_search_string()

    text_handler = TextHandler(doc, active_view, uidoc, selected_options)
    matching_text_notes = text_handler.search_text(search_term)
    
    with Transaction(doc, "Search and Select Text") as t:
        t.Start()
        # Highlight matching text
        text_handler.highlight_selected_text(matching_text_notes, search_term)
        t.Commit()

