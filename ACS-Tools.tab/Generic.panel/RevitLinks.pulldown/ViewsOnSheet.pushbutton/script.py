from Autodesk.Revit.DB import Transaction, TransactionGroup, ElementId
from pyrevit import revit, forms
from functions import is_dependent_view, check_view_template, get_revit_link_instances, get_link_visibility_status, get_view_template, get_original_link_visibility
from get_sheets import is_sheet_view, get_views_on_sheet, select_views
from __init__ import template_name

# Get the active document and the active view (assuming it's a sheet)
document = revit.doc
active_view = revit.active_view

def sheet_logic(sheet_view, doc):
    # Check if active view is a sheet view
    is_sheet_view(sheet_view)
    # Get all the views on the current sheet (ignoring schedules and legends)
    views_on_sheet = get_views_on_sheet(doc, sheet_view)
    # Allow the user to select target views 
    selected_views = select_views(views_on_sheet)
    return selected_views

def view_visibility_logic(selected_views, revit_links, link_type_ids):
    ignore_all = False 
    view_information = {}
    for i, selected_view in enumerate(selected_views): 
        # Check if the active view is dependent and set parent as active_view if user agrees
        control_view, dependent = is_dependent_view(document, selected_view)
        if dependent:
            selected_views[i] = control_view
            selected_view = control_view
        # Check if View Template applied 
        ignore_all = check_view_template(selected_view, True, ignore_all)
        # Get visibility status of revit links in view
        visibility_status = get_link_visibility_status(selected_view, revit_links)
        # Get a list of the revit links to unhide 
        links_to_unhide = get_original_link_visibility(document, visibility_status, link_type_ids)
        view_information[selected_view] = links_to_unhide
    return selected_view, view_information


def main():
    # --- SHEET & FORM LOGIC ---

    # Get all the views within the sheet 
    selected_views = sheet_logic(active_view, document)

    # --- VISIBILITY GRAPHICS LOGIC ---
    
    # Get the view template
    view_template = get_view_template(document, template_name)
    # Get all Revit links in the project
    revit_links, link_type_ids = get_revit_link_instances(document)
    # Get the links to uhide in each view (and replace any dependent child views with parent view)
    selected_view, view_information = view_visibility_logic(selected_views, revit_links, link_type_ids)

    # --- COMMIT TRANSACTIONS ---

    # Use a TransactionGroup to group all changes together
    with TransactionGroup(document, "Turn off Link Annotation Categories") as tg:
        tg.Start()

        # First transaction: Apply the view template
        with Transaction(document, "Apply View Template to all Views") as t1:
            t1.Start()
            for selected_view in selected_views:
                selected_view.ViewTemplateId = view_template
            t1.Commit()

        # Second transaction: Remove view template and hide elements
        with Transaction(document, "Hide Revit Links in View") as t2:
            t2.Start()
            for selected_view in selected_views:
                # Remove the view template
                selected_view.ViewTemplateId = ElementId.InvalidElementId  
                # Unhide the RevitLinkType elements in the active view
                selected_view.UnhideElements(view_information[selected_view])
            t2.Commit()

        # Commit the entire group to apply all changes at once
        tg.Assimilate()
    
    forms.alert("Revit links Annotation categories for all selected views have been turned off", exitscript=False)


main()
