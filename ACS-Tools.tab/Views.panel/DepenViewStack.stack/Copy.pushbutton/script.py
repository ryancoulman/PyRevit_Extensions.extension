# -*- coding: utf-8 -*-
# Minimal ViewHandler for selecting independent views

from pyrevit import forms, revit
import clr
from Autodesk.Revit.DB import FilteredElementCollector, View, Element, Transaction, ElementTransformUtils, CategoryType, ElementId


# Create a .NET List for ElementId
clr.AddReference("System.Collections")
from System.Collections.Generic import List

from helefuncs import ViewHandler

doc = revit.doc
uidoc = __revit__.ActiveUIDocument
master_view = revit.active_view

## MODIFICATON: Pyrevit has tool Select-> Detil elements which esily gets all 2d detail elements in view much better than my tool 
## so get logic from there and implement 
    
## TO DO ## 
# - Add option for user to edit the annotation categories list. just store in writable json file user can edit 
# - Cannot get view refs with this method 
# - No tag catogry. will have to get all annotation catogries then filter for tags 


class AnnotationCopier(object):
    """Copy all view-specific annotation elements (including system-family wires)
    from one or multiple independent views to a master view.
    """

    def __init__(self, doc, master_view):
        self.doc = doc
        if not isinstance(master_view, View):
            forms.alert("Master view must be a Revit View.", exitscript=True)
        self.master_view = master_view

    def get_annotation_categories(self):
        """Return all annotation categories in the document."""
        return [cat for cat in self.doc.Settings.Categories if cat.CategoryType == CategoryType.Annotation]

    def get_annotations_from_view_null(self, view):
        """Return all annotation elements in a given view, including wires."""
        ann_cats = self.get_annotation_categories()
        elements = []
        for cat in ann_cats:
            elems = FilteredElementCollector(self.doc, view.Id)\
                        .OfCategoryId(cat.Id)\
                        .WhereElementIsNotElementType()\
                        .ToElements()
            elements.extend(elems)

        # 2. Wires (model elements, not annotations)
        wires = FilteredElementCollector(self.doc, view.Id)\
                    .OfCategoryId(self.doc.Settings.Categories.get_Item("Wires").Id)\
                    .WhereElementIsNotElementType()\
                    .ToElements()
        elements.extend(wires)

        return list(set(elements))
    
    def get_annotations_from_viewOLD(self, view):
        """Return only the important annotation elements from a view."""
        important_cats = [
            "Text Notes",
            "Detail Lines",
            "View Reference",
            "Dimensions",
            "Lines",
            "Filled Regions",
            "Generic Annotations",
            "Tags",
            "Wires"  # system-family
        ]

        elements = []

        for cat_name in important_cats:
            try:
                cat = self.doc.Settings.Categories.get_Item(cat_name)
            except:
                continue  # skip if category not present in this project

            elems = FilteredElementCollector(self.doc, view.Id) \
                        .OfCategoryId(cat.Id) \
                        .WhereElementIsNotElementType() \
                        .ToElementIds()
            elements.extend(elems)

        return elements  # return ElementIds directly
    
    def get_annotations_from_view(self, view):
        """Return only the important annotation elements from a view."""
        # Collect all elements in current view 
        collector1 = FilteredElementCollector(doc, view.Id).WhereElementIsNotElementType()
        # Filter out types of 'Other' 
        collector = [el for el in collector1 if el.Category is not None]

        # List to hold view-specific element IDs
        view_specific_ids = []

        for el in collector:
            try:
                if el.ViewSpecific:   # property on Element
                    view_specific_ids.append(el.Id)
            except Exception as e:
                # some elements may not expose ViewSpecific
                pass

        return view_specific_ids


    def copy_annotations(self, source_views):
        """Copy all annotations from source_views to the master_view."""
        if not source_views:
            forms.alert("No source views provided.", exitscript=True)

        all_copied = {}
        t = Transaction(self.doc, "Copy Annotations to Master View")
        t.Start()
        try:
            for view in source_views:
                elements = self.get_annotations_from_view(view)
                if not elements:
                    continue

                element_ids = List[ElementId](elements)
                # uidoc.Selection.SetElementIds(element_ids)
                copied_ids = ElementTransformUtils.CopyElements(
                    view,
                    element_ids,
                    self.master_view,
                    None,
                    None
                )
                all_copied[view.Name] = [self.doc.GetElement(eid) for eid in copied_ids]
            t.Commit()
        except Exception as e:
            t.RollBack()
            raise e

        return all_copied





# Assume you already have independent views selected
vh = ViewHandler(doc)  # your simplified view handler
independent_views = vh.select_independent_views()

# Copy all annotations
copier = AnnotationCopier(doc, master_view)
copied_dict = copier.copy_annotations(independent_views)

# Print summary
for view_name, elems in copied_dict.items():
    print("Copied {} elements from '{}'".format(len(elems), view_name))