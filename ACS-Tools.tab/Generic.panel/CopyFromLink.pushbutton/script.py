# -*- coding: utf-8 -*-
"""
Copy all elements from a chosen category in a selected Revit link
into the host model, maintaining coordinates.

"""

from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from System.Collections.Generic import List
from pyrevit import forms, revit

__title__ = "Copy From Link by Category"

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def pick_link_instance(uidoc):
    """Prompt user to pick a Revit link instance inside the model."""
    try:
        ref = uidoc.Selection.PickObject(ObjectType.Element, "Select a Revit link instance")
        element = uidoc.Document.GetElement(ref.ElementId)
        if isinstance(element, RevitLinkInstance):
            return element
        else:
            forms.alert("Selected element is not a Revit link.", exitscript=True)
    except:
        forms.alert("Cancelled by user.", exitscript=True)

def get_category_names(link_doc):
    """Return a list of all valid category names from the linked document."""
    cats = []
    for cat in link_doc.Settings.Categories:
        if cat.AllowsBoundParameters: # filters out system/internal categories like Lines
            cats.append(cat.Name)
    return sorted(cats)

def copy_elements_from_link(link_doc, host_doc, category_name, transform):
    """Copy all elements from a given category in a linked document into host."""
    # Find the category
    cat = None
    for c in link_doc.Settings.Categories:
        if c.Name == category_name:
            cat = c
            break
    if not cat:
        forms.alert("Category '{}' not found.".format(category_name), exitscript=True)

    # collector = FilteredElementCollector(link_doc).OfCategory(BuiltInCategory.OST_RoomSeparationLines)


    collector = (
        FilteredElementCollector(link_doc)
        .OfCategoryId(cat.Id)
        .WhereElementIsNotElementType()
    )

    elems = [e for e in collector if not e.ViewSpecific]

    if not elems:
        forms.alert("No elements found in category '{}'.".format(category_name), exitscript=True)

    # Perform the copy
    ids = List[ElementId]([e.Id for e in elems])

    with revit.Transaction("Copy from Link: {}".format(category_name)):
        copied = ElementTransformUtils.CopyElements(link_doc, ids, host_doc, transform, None)

    return len(copied)

# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

link_instance = pick_link_instance(uidoc)
link_doc = link_instance.GetLinkDocument()

if not link_doc:
    forms.alert("Link is not loaded or cannot access linked document.", exitscript=True)

# Let user pick category from dropdown
categories = get_category_names(link_doc)
selected_category = forms.SelectFromList.show(
    categories,
    title="Select Category to Copy",
    button_name="Copy Elements",
    multiselect=False
)

if not selected_category:
    forms.alert("No category selected.", exitscript=True)

# Copy elements
count = copy_elements_from_link(link_doc, doc, selected_category, link_instance.GetTotalTransform())

forms.alert("Successfully copied {} elements from '{}'.".format(count, selected_category))
