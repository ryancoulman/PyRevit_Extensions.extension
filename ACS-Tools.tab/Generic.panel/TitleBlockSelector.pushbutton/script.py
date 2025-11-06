# -*- coding: utf-8 -*-
"""Select Titleblocks from Selected Sheets
Selects all titleblocks from sheets selected in the Project Browser.
"""
__title__ = "Select\nTitleblocks"
__doc__ = "Selects all titleblocks from sheets selected in the Project Browser." \
"\n\nNote: Titleblocks are selected but may not be highlighted until you open each sheet."


from Autodesk.Revit.DB import (
    FilteredElementCollector, ViewSheet,
    BuiltInCategory, ElementId
)
from pyrevit import revit, forms
from System.Collections.Generic import List



def get_selected_sheets(uidoc):
    """
    Get all selected sheets from the Project Browser.
    
    Args:
        uidoc: The UIDocument instance
        
    Returns:
        list: List of ViewSheet elements
    """
    selection = uidoc.Selection
    selected_ids = selection.GetElementIds()
    
    if not selected_ids:
        return []
    
    doc = uidoc.Document
    sheets = []
    
    for elem_id in selected_ids:
        element = doc.GetElement(elem_id)
        if isinstance(element, ViewSheet):
            sheets.append(element)
    
    return sheets


def get_titleblock_from_sheet_fast(sheet, all_titleblocks):
    """
    Get the titleblock element from a sheet WITHOUT generating graphics.
    Uses the sheet's owner view relationship to find titleblock efficiently.
    
    Args:
        sheet: ViewSheet element
        all_titleblocks: List of all titleblock elements in the project
        
    Returns:
        Element: Titleblock element or None if not found
    """
    sheet_id = sheet.Id
    
    # Find titleblock that belongs to this sheet by checking OwnerViewId
    for tb in all_titleblocks:
        if hasattr(tb, 'OwnerViewId') and tb.OwnerViewId == sheet_id:
            return tb
    
    return None


def collect_titleblocks(doc, sheets):
    """
    Collect all titleblocks from the given sheets.
    
    Args:
        doc: The Document instance
        sheets: List of ViewSheet elements
        
    Returns:
        tuple: (list of titleblock elements, list of sheet numbers without titleblocks)
    """
    titleblocks = []
    sheets_without_titleblocks = []

    # Get all titleblocks in the project
    all_titleblocks = FilteredElementCollector(doc)\
        .OfCategory(BuiltInCategory.OST_TitleBlocks)\
        .WhereElementIsNotElementType()\
        .ToElements()
    
    for sheet in sheets:
        titleblock = get_titleblock_from_sheet_fast(sheet, all_titleblocks)
        
        if titleblock:
            titleblocks.append(titleblock)
        else:
            sheets_without_titleblocks.append(sheet.SheetNumber)
    
    return titleblocks, sheets_without_titleblocks


def select_titleblocks_with_view_activation(uidoc, titleblocks):
    """
    Select titleblocks by opening their parent sheets.
    This ensures proper visual feedback in Revit UI.
    
    Args:
        uidoc: The UIDocument instance
        titleblocks: List of titleblock elements
        
    Returns:
        bool: True if successful
    """
    if not titleblocks:
        return False
    
    doc = uidoc.Document
    
    # Group titleblocks by sheet
    sheets_dict = {}
    for tb in titleblocks:
        sheet_id = tb.OwnerViewId
        if sheet_id not in sheets_dict:
            sheets_dict[sheet_id] = []
        sheets_dict[sheet_id].append(tb.Id)
    
    # Multiple sheets - collect all IDs and select without opening views
    # (Revit limitation: can't visually highlight elements across multiple closed views)
    all_ids = []
    for tb_ids in sheets_dict.values():
        all_ids.extend(tb_ids)
    
    id_collection = List[ElementId](all_ids)
    uidoc.Selection.SetElementIds(id_collection)
    
    return True


def main():
    """Main execution function."""
    # Get current document and UI document
    doc = revit.doc
    uidoc = revit.uidoc
    
    # Get selected sheets from Project Browser
    selected_sheets = get_selected_sheets(uidoc)
    
    if not selected_sheets:
        forms.alert(
            "No sheets selected.\n\n"
            "Please select one or more sheets in the Project Browser.",
            title="No Sheets Selected",
            warn_icon=True
        )
        return
    
    # Collect titleblocks from selected sheets (fast method - no graphics generation)
    titleblocks, sheets_without_titleblocks = collect_titleblocks(doc, selected_sheets)
    
    # Report results
    if not titleblocks:
        forms.alert(
            "No titleblocks found on the selected sheets.",
            title="No Titleblocks Found",
            warn_icon=True
        )
        return
    
    # Select the titleblocks
    select_titleblocks_with_view_activation(uidoc, titleblocks)
    
    # Build result message
    message = "Successfully selected {} titleblock(s) from {} sheet(s).".format(
        len(titleblocks),
        len(selected_sheets)
    )
    message += "\n\nNote: Titleblocks are selected but may not be highlighted in model."
    
    if sheets_without_titleblocks:
        message += "\n\nSheets without titleblocks:\n"
        message += "\n".join("• " + sheet_num for sheet_num in sheets_without_titleblocks)
    
    # Show success message
    forms.alert(message, title="Titleblocks Selected")


# Script entry point
if __name__ == "__main__":
    main()