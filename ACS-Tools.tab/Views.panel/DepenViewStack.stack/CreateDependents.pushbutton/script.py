# -*- coding: utf-8 -*-
# ScopeBoxSelector class for pyRevit
# Usage:
#   selected_scopeboxes = ScopeBoxSelector(revit.doc).get_selected()

from pyrevit import forms, DB, revit
from Autodesk.Revit.Exceptions import ArgumentException, InvalidOperationException


__title__ = "Create Dependents"

class ScopeBoxSelector(object):
    """Helper for fetching and selecting scope boxes in Revit."""

    def __init__(self, doc):
        self.doc = doc
        self._scope_boxes = self._collect_scope_boxes()

    def _collect_scope_boxes(self):
        """Collect all scope boxes in the project."""
        return DB.FilteredElementCollector(self.doc) \
            .OfCategory(DB.BuiltInCategory.OST_VolumeOfInterest) \
            .WhereElementIsNotElementType() \
            .ToElements()

    def get_scopebox_dict(self):
        """Return dict of {name: element} for scope boxes"""
        return {sb.Name: sb for sb in self._scope_boxes}

    
    def get_search_string(self):
        search_term = forms.ask_for_string(
            prompt='Enter base name of dependent views:', 
            title='Dependent view name = base name + scope name'
        )
        if search_term:
            return search_term
        else:
            forms.alert('No text given', exitscript=True)
            return None

    def get_selected(self, multiselect=True):
        """Show selection form and return selected scope box elements."""
        if not self._scope_boxes:
            forms.alert("No scope boxes found in this project.", exitscript=True)

        sb_dict = self.get_scopebox_dict()

        selected_names = forms.SelectFromList.show(
            sorted(sb_dict.keys()),
            multiselect=multiselect,
            title="Select Scope Boxes",
            button_name="Select"
        )

        if not selected_names:
            return []

        return [sb_dict[name] for name in selected_names]
    

class DependentViewCreator(object):
    """Helper for creating dependent views from a master view."""

    def __init__(self, doc, master_view, base_name):
        self.doc = doc
        self.master_view = master_view
        self.base_name = base_name 

    def create_dependents(self, scope_boxes):
        """Create dependent views for given scope boxes.
        Returns list of new dependent View objects.
        """
        if not scope_boxes:
            return []

        new_views = []
        t = DB.Transaction(self.doc, "Create Dependent Views")
        t.Start()
        try:
            for sb in scope_boxes:
                # Duplicate as dependent
                dep_view_id = self.master_view.Duplicate(DB.ViewDuplicateOption.AsDependent)
                dep_view = self.doc.GetElement(dep_view_id)

                # Apply scope box
                scope_param = dep_view.get_Parameter(DB.BuiltInParameter.VIEWER_VOLUME_OF_INTEREST_CROP)
                if scope_param and not scope_param.IsReadOnly:
                    scope_param.Set(sb.Id)

                # Rename view: "MasterName - ScopeBoxName"
                new_name = "{} - {}".format(self.base_name, sb.Name)

                success = False
                suffix = 1
                # If non unique name is given, try adding suffixes
                while not success:
                    try:
                        dep_view.Name = new_name
                        success = True
                    except ArgumentException:
                        # Name already exists → try a new suffix
                        new_name = "{} - {} Copy {}".format(self.base_name, sb.Name, suffix)
                        suffix += 1
                    except InvalidOperationException as e:
                        forms.alert('Element cannot be changed: {}'.format(e), exitscript=True)
                        break


                new_views.append(dep_view)

            t.Commit()
        except Exception as e:
            t.RollBack()
            raise e

        return new_views

# Import class from wherever you put it
# from mymodule.scopebox_selector import ScopeBoxSelector

# Step 1: Select scope boxes
selector = ScopeBoxSelector(revit.doc)
selected_scopeboxes = selector.get_selected()
base_name = selector.get_search_string()

# Step 2: Create dependents from current view
creator = DependentViewCreator(revit.doc, revit.active_view, base_name)
new_views = creator.create_dependents(selected_scopeboxes)

# Step 3: Feedback
for v in new_views:
    print("Created dependent view:", v.Name)

