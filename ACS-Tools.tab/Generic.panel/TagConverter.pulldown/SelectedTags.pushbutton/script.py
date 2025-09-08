from pyrevit import revit
from TagConverterLogic import TagManager, TextStyle
from TagMain import MainHandler

__title__ = "Tag\nConverter"
__doc__ = "Convert annotation tags to plain text"



doc = revit.doc
active_view = revit.active_view
uidoc = __revit__.ActiveUIDocument


def main():

    # Initialise tag manager 
    tag_manager = TagManager(doc, active_view)
    # Get all selected tags 
    tags_to_process = tag_manager.get_selected_annotation_tags(uidoc)
    # Initialize the TextStyle class with the current Revit document
    text_styles = TextStyle(doc)
    # Get the ElementId of the selected text style
    selected_style_id = text_styles.get_selected_style_id()
    # Call main 
    MainHandler(doc, tags_to_process, selected_style_id)


main()
