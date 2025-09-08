# -*- coding: utf-8 -*-
from pyrevit import forms
from Autodesk.Revit.DB import (
    ParameterValueProvider,
    BuiltInParameter,
    BuiltInCategory,
    ElementId,
    FilterStringEquals,
    FilterStringRule,
    ElementParameterFilter,
    FilteredElementCollector,
)

'''Class to return the sheet that the view is placed on from active view'''
class GetViewSheet():
    def __init__(self, active_view, document, print_sheet=False):
        self.active_view = active_view
        self.document = document
        self.sheet = self.get_sheet_from_view(document, active_view)
        
        if self.sheet and print_sheet:
            print('Sheet Found: {} - {}'.format(self.sheet.SheetNumber, self.sheet.Name))
        elif not self.sheet and print_sheet:
            forms.alert('No sheet associated with the given view: {}'.format(active_view.Name), exitscript=True)
        
    def create_string_equals_filter(self, key_parameter, element_value):
        """Function to create ElementParameterFilter based on FilterStringRule."""
        f_parameter = ParameterValueProvider(ElementId(key_parameter))
        f_rule = FilterStringRule(f_parameter, FilterStringEquals(), element_value)
        return ElementParameterFilter(f_rule)

    def get_sheet_from_view(self, doc, view):
        """Function to get ViewSheet associated with the given ViewPlan"""
        my_filter = self.create_string_equals_filter(
            key_parameter=BuiltInParameter.SHEET_NUMBER,
            element_value=view.get_Parameter(BuiltInParameter.VIEWER_SHEET_NUMBER).AsString()
        )
        return FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Sheets) \
                                            .WhereElementIsNotElementType() \
                                            .WherePasses(my_filter).FirstElement()
    
    def get_sheet(self):
        """Function to return the sheet, can be called after object initialization."""
        return self.sheet
