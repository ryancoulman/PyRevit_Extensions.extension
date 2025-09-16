from pyrevit import revit
from TagConverterLogic import TagManager, TextStyle
from TagMain import MainHandler
from selection_context import SelectionContext


doc = revit.doc
active_view = revit.active_view
uidoc = __revit__.ActiveUIDocument


def main():

     # Initialise tag manager 
    tag_manager = TagManager(doc)
    tags_to_process = []

    context = SelectionContext(doc, uidoc)
    # Return the objects to process
    targets = context.resolved_targets  

    if context.has_selected_views:
        for view in targets:
            tags_to_process.extend(tag_manager.get_all_tags_in_view(view))
    elif context.has_selected_elements:
        tags_to_process.extend(tag_manager.get_selected_annotation_tags(targets))
    elif context.has_active_view:
        tags_to_process.extend(tag_manager.get_all_tags_in_view(targets[0]))


    # Initialize the TextStyle class with the current Revit document
    text_styles = TextStyle(doc)
    # Get the ElementId of the selected text style
    selected_style_id = text_styles.return_selected_style
    # Call main 
    MainHandler(doc, tags_to_process, selected_style_id)


main()
