# -*- coding: utf-8 -*-
# Minimal ViewHandler for selecting independent views

from pyrevit import forms, revit
from Autodesk.Revit.DB import FilteredElementCollector, Viewport, Transaction, ElementTransformUtils
from helefuncs import ViewHandler
from get_viewSheet import GetViewSheet


doc = revit.doc
master_view = revit.active_view


class ReplaceIndependentWithDependent:
    """
    Replace selected independent views on sheets with dependent views of the active master view.
    Fetches dependent views using GetDependentViewIds() to avoid relying on names.
    """

    def __init__(self, doc, master_view):
        self.doc = doc
        self.master_view = master_view

    def get_viewport_on_sheet(self, sheet, view):
        """Return the viewport on the sheet for a given view."""
        viewports = FilteredElementCollector(self.doc, sheet.Id).OfClass(Viewport).ToElements()
        for vp in viewports:
            if vp.ViewId == view.Id:
                return vp
        return None

    def replace_views(self, independent_views):
        """
        Replace independent viewports with dependent views on sheets.
        :param independent_views: list of independent View objects
        """
        # Get dependent views from master view
        dep_view_ids = self.master_view.GetDependentViewIds()  # returns ICollection[ElementId]
        dependent_views = [self.doc.GetElement(eid) for eid in dep_view_ids]

        # Sort both independent and dependent views alphabetically by Name
        independent_views_sorted = sorted(independent_views, key=lambda v: v.Name)
        dependent_views_sorted = sorted(dependent_views, key=lambda v: v.Name)

        if len(independent_views_sorted) != len(dependent_views_sorted):
            forms.alert("Number of independent and dependent views do not match!", exitscript=True)

        # Replace viewports
        t = Transaction(self.doc, "Replace Independent Views with Dependent Views")
        t.Start()
        try:
            for indep_view, dep_view in zip(independent_views_sorted, dependent_views_sorted):
                sheet = GetViewSheet(indep_view, self.doc).get_sheet()
                if not sheet:
                    forms.alert("No sheet found for view: {}".format(indep_view.Name))
                    continue

                viewport = self.get_viewport_on_sheet(sheet, indep_view)
                if not viewport:
                    forms.alert("No viewport found on sheet {} for view {}".format(sheet.SheetNumber, indep_view.Name))
                    continue
                
                # Get OG viewport location 
                vp_location = viewport.GetBoxCenter()
                # Replace viewport with dependent view
                viewport.ViewId = dep_view.Id
                # Move viewport back to original location
                ElementTransformUtils.MoveElement(doc, viewport.Id, vp_location - viewport.GetBoxCenter())

                # --- Print confirmation ---
                print("Replaced view '{}' on sheet '{}' with dependent view '{}'".format(
                    indep_view.Name,
                    sheet.SheetNumber,
                    dep_view.Name
                ))

            t.Commit()
        except Exception as e:
            t.RollBack()
            forms.alert("Error replacing views: {}".format(str(e)))


# === Usage Example ===
master_view = revit.active_view
vh = ViewHandler(revit.doc)  # your simplified view handler
independent_views = vh.select_independent_views()  # assume this returns a list of independent View objects

replacer = ReplaceIndependentWithDependent(revit.doc, master_view)
replacer.replace_views(independent_views)

