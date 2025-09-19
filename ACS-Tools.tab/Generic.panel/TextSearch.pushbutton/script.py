from Autodesk.Revit.DB import Transaction
from pyrevit import revit
from classes import FormHandler, TextHandler, check_selected, FormHandlerNEW
from System.Windows import MessageBox

doc = revit.doc
uidoc = revit.uidoc
active_view = revit.active_view


def selected_main():

    form_handler = FormHandlerNEW()

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

# Test function to show search data
def show_search(search_data):
    MessageBox.Show(
        "Text: {}\nMatch: {}\nInclude ReGeX: {}\nMatch Case: {}\nInclude Annotation tags: {}".format(
            search_data.text, search_data.match_mode, search_data.include_regex,
            search_data.match_case, search_data.include_annotation_tags
        ),
        "Search Info"
    )

def main():

    form_handler = FormHandlerNEW()
    search_data = form_handler.return_search_data()
    show_search(search_data)

    # text_handler = TextHandler(doc, active_view, uidoc, search_data)
    # matching_text_notes = text_handler.search_text()

    # with Transaction(doc, "Search and Select Text") as t:
    #     t.Start()
    #     # Highlight matching text
    #     text_handler.highlight_selected_text(matching_text_notes, search_data.text)
    #     t.Commit()


if __name__ == "__main__":
    main()