
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, ElementId, RevitLinkType
from pyrevit import forms
from System.Collections.Generic import List


# If Dependent Child view script will not work -> Get parent view 
def is_dependent_view(doc, view):
    """Check if the given view is a dependent child view."""
    dependent = False 
    if view.GetPrimaryViewId() != ElementId.InvalidElementId:
        dependent = True 
        # If it's a dependent view, return the parent (primary) view.
        parent_view_id = view.GetPrimaryViewId()
        parent_view = doc.GetElement(parent_view_id)
        return parent_view, dependent
    else:
        # If it's not dependent, return the original view.
        return view, dependent

def check_view_template(view, multi_views=False, ignore_all=False):

    # Check if the view has a template applied and "Ignore All" is not selected
    if view.ViewTemplateId != ElementId.InvalidElementId and not ignore_all:
        # Use CommandSwitchWindow to present three options
        optionA = 'Remove Template & Proceed'
        optionB = 'Remove View Template for all Selected Views & Proceed'
        optionC = 'Cancel'
        if not multi_views: 
            options = [optionA, optionC]
        else:
            # 'Ignore all' option if multiple views
            options = [optionA, optionB, optionC]

        selected_option = forms.CommandSwitchWindow.show(
            options,
            message="{} has a view template applied. Do you want to continue?".format(view.Name)
        )

        # Handle the user's choice
        if selected_option == optionC:
            forms.alert("Script cancelled.", exitscript=True)
        elif selected_option == optionB:
            ignore_all = True  
        # If 'Proceed', just continue without any action

        return ignore_all  # Return the state for the next check
    

def get_revit_link_instances(doc):
    """Get all Revit link instances in the project."""
    # Filter all Revit links in the project
    link_types = FilteredElementCollector(doc).OfClass(RevitLinkType).ToElements()
    # Collect all RevitLinkType ids in the document
    link_type_ids = FilteredElementCollector(doc) \
        .OfCategory(BuiltInCategory.OST_RvtLinks) \
        .OfClass(RevitLinkType) \
        .ToElementIds()  

    if not link_types or not link_type_ids:
        forms.alert("No Revit links found in the current view.", exitscript=True)

    return link_types, link_type_ids


def get_link_visibility_status(view, link_types):
    """Get the current visibility status of all Revit links in the current view."""
    visibility_status = {}
    
    for link in link_types:
        try:
            # Check if the link is hidden in the active view
            is_hidden = link.IsHidden(view)  
            # Store the visibility state in the dictionary
            visibility_status[link.Id] = is_hidden  
        except Exception as e:
            print("Error getting visibility for Revit link {}: {}".format(link.Id, str(e)))
    
    return visibility_status

def get_view_template(doc, template_name):
    """Get the view template by name."""
    view_templates = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).ToElements()
    template = None

    for v in view_templates:
        if v.Name == template_name and v.IsTemplate:
            template = v
            break
    
    if template is None:
        forms.alert("View template '{}' not found. Ensure template name exactly matches.".format(template_name), exitscript=True)

    return template.Id

def get_original_link_visibility(doc, visibility_status, link_type_ids):
    """Restore the visibility of Revit link types based on original status."""

    # Initialize an empty ICollection[ElementId]
    filtered_link_types = List[ElementId]()  

    # Filter the link_types based on the original visibility status. 
    for link_type_id in link_type_ids:
        # If link shown originally in view then add to filtered_link_types list to be unhidden 
        if not visibility_status[link_type_id]:  
            filtered_link_types.Add(link_type_id)  # Add to ICollection

    if filtered_link_types.Count == 0:
        print("No RevitLinkType elements met the condition.")
    
    return filtered_link_types