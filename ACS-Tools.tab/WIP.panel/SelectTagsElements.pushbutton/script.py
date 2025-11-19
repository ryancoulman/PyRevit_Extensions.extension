# -*- coding: utf-8 -*-

__title__ = "Select\nTags/Elements"
__doc__ = "Toggle Selection Between Tags and Their Host Elements." \
"\nSelects all tags of selected elements or all hosts of selected tags."

from Autodesk.Revit.DB import (
    FilteredElementCollector,
    IndependentTag
)
from pyrevit import revit, forms


def get_tags_in_view(view):
    """Get all IndependentTag elements in the current view.
    
    Args:
        view: The view to search for tags
        
    Returns:
        List of IndependentTag elements
    """
    return (FilteredElementCollector(revit.doc, view.Id)
            .OfClass(IndependentTag)
            .ToElements())


def get_tagged_elements_from_tags(tags):
    """Get all unique host elements from a collection of tags.
    
    Args:
        tags: Collection of IndependentTag elements
        
    Returns:
        List of unique element IDs that are tagged
    """
    tagged_ids = set()
    for tag in tags:
        tagged_id = tag.TaggedLocalElementId
        if tagged_id and tagged_id.IntegerValue != -1:
            tagged_ids.add(tagged_id)
    return list(tagged_ids)


def get_tags_for_elements(element_ids, view):
    """Get all tags that reference the given elements in the current view.
    
    Args:
        element_ids: Collection of element IDs to find tags for
        view: The view to search for tags
        
    Returns:
        List of IndependentTag element IDs that tag the given elements
    """
    element_id_set = set(element_ids)
    all_tags = get_tags_in_view(view)
    
    matching_tag_ids = []
    for tag in all_tags:
        tagged_id = tag.Id
        if tagged_id in element_id_set:
            matching_tag_ids.append(tag.Id)
    
    return matching_tag_ids


def partition_selection(selection):
    """Separate selection into tags and non-tags.
    
    Args:
        selection: Collection of element IDs
        
    Returns:
        Tuple of (tag_ids, element_ids) lists
    """
    tags = []
    elements = []
    
    for elem in selection:
        # elem = revit.doc.GetElement(elem_id)
        if isinstance(elem, IndependentTag):
            tags.append(elem.Id)
        else:
            elements.append(elem.Id)
    
    return tags, elements


def main():
    """Main execution function."""
    # Get current selection
    selection = revit.get_selection()
    
    if not selection:
        forms.alert("Please select elements or tags first.", exitscript=True)
    
    # Get active view
    active_view = revit.active_view
    
    # Partition selection into tags and elements
    tag_ids, element_ids = partition_selection(selection)
    
    # Determine action based on selection type
    if tag_ids and element_ids:
        forms.alert(
            "Selection contains both tags and elements.\n"
            "Please select only tags OR only elements.",
            exitscript=True
        )
    
    new_selection = []
    
    if tag_ids:
        # Selected tags -> find their host elements
        tags = [revit.doc.GetElement(tid) for tid in tag_ids]
        new_selection = get_tagged_elements_from_tags(tags)
        
        if not new_selection:
            forms.alert("No valid tagged elements found.", exitscript=True)
        
        action_msg = "Selected {} element(s) from {} tag(s)".format(
            len(new_selection), len(tag_ids)
        )
    
    elif element_ids:
        # Selected elements -> find their tags in current view
        new_selection = get_tags_for_elements(element_ids, active_view)
        
        if not new_selection:
            forms.alert(
                "No tags found for selected elements in current view.",
                exitscript=True
            )
        
        action_msg = "Selected {} tag(s) from {} element(s)".format(
            len(new_selection), len(element_ids)
        )
    
    else:
        forms.alert("No valid selection found.", exitscript=True)
    
    # Update selection
    revit.get_selection().set_to(new_selection)
    
    # Print result
    print(action_msg)


if __name__ == '__main__':
    main()