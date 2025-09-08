from Autodesk.Revit.DB import Transaction, TransactionGroup, ElementId, ViewSheet
from pyrevit import revit, forms
from functions import is_dependent_view, check_view_template, get_revit_link_instances, get_link_visibility_status, get_view_template, get_original_link_visibility
from __init__ import template_name

# Access Revit document and active view
doc = revit.doc
active_view = revit.active_view

def is_viewport(view):
    # Check if the active view is a a viewport (not sheet view)
    if isinstance(view, ViewSheet):
        forms.alert("The active view is a sheet view. Please open a viewport to run this script.", exitscript=True)


def main():
    
    global active_view
    # Check that the user is within a viewport 
    is_viewport(active_view)
    # Check if the active view is dependent and set active_view accordingly.
    active_view, _ = is_dependent_view(doc, active_view)
    # Check if View Template applied 
    check_view_template(active_view)
    # Get all Revit links and their visibility status
    revit_links, link_type_ids = get_revit_link_instances(doc)
    visibility_status = get_link_visibility_status(active_view, revit_links)

    # Get the view template
    view_template = get_view_template(doc, template_name)

    # Use a TransactionGroup to group all changes together
    with TransactionGroup(doc, "Turn off Link Annotation Categories") as tg:
        tg.Start()

        # First transaction: Apply the view template
        with Transaction(doc, "Apply View Template") as t1:
            t1.Start()
            active_view.ViewTemplateId = view_template
            t1.Commit()

        # Get the original visibility state of Revit links
        filtered_link_types = get_original_link_visibility(doc, visibility_status, link_type_ids)

        # Second transaction: Remove view template and hide elements
        with Transaction(doc, "Hide Revit Links in View") as t2:
            t2.Start()

            # Remove the view template
            active_view.ViewTemplateId = ElementId.InvalidElementId  

            # Unhide the RevitLinkType elements in the active view
            active_view.UnhideElements(filtered_link_types)

            t2.Commit()

        # Commit the entire group to apply all changes at once
        tg.Assimilate()
    
    forms.alert("Annotation categories for Revit links have been turned off and visibility restored.", exitscript=False)

# Run the script
main()
