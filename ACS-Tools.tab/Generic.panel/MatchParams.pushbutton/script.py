# -*- coding: utf-8 -*-
import clr
import os
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import forms
from System.Windows import MessageBox

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document


# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def pick_family(uidoc):
    """Prompt user to pick a family instance."""
    try:
        ref = uidoc.Selection.PickObject(ObjectType.Element, "Select a family instance")
        elem = uidoc.Document.GetElement(ref.ElementId)
        if isinstance(elem, FamilyInstance):
            return elem
        else:
            forms.alert("Selected element is not a family instance.", exitscript=True)
    except:
        forms.alert("Cancelled by user.", exitscript=True)


def get_all_family_instances(doc, family_symbol):
    """Return all instances of the same Family (any type) in the project."""
    family_id = family_symbol.Family.Id
    collector = FilteredElementCollector(doc).OfClass(FamilyInstance)
    return [i for i in collector if i.Symbol.Family.Id == family_id]


def get_instances_with_both_params_same_category(doc, family_instance, source_param_name, target_param_name):
    """Return all FamilyInstances in same category with both parameters."""
    if not family_instance or not hasattr(family_instance, "Category"):
        raise ValueError("Must provide a valid FamilyInstance with a category.")

    category_id = family_instance.Category.Id
    matching = []

    for inst in FilteredElementCollector(doc).OfClass(FamilyInstance).WhereElementIsNotElementType():
        if inst.Category and inst.Category.Id == category_id:
            src = inst.LookupParameter(source_param_name)
            tgt = inst.LookupParameter(target_param_name)
            if src and tgt:
                matching.append(inst)
    return matching


def get_instances_with_both_params(doc, source_param_name, target_param_name):
    """Return all FamilyInstances that contain both parameters."""
    matching = []
    for inst in FilteredElementCollector(doc).OfClass(FamilyInstance):
        src = inst.LookupParameter(source_param_name)
        tgt = inst.LookupParameter(target_param_name)
        if src and tgt:
            matching.append(inst)
    return matching


def get_family_parameters(family_instance):
    """Return list of writable parameter names."""
    params = []
    for p in family_instance.Parameters:
        if not p.IsReadOnly:
            params.append(p.Definition.Name)
    return sorted(set(params))


def pick_parameter(family_instance, title="Select Parameter"):
    """Prompt user to pick a parameter name from given family instance."""
    param_names = get_family_parameters(family_instance)
    return forms.SelectFromList.show(param_names, title=title, button_name="Select", multiselect=False)


def copy_parameter_value(source_param, target_param):
    """Copy value from source parameter to target parameter."""
    if not source_param or not target_param or target_param.IsReadOnly:
        return False

    stype = source_param.StorageType
    try:
        if stype == StorageType.String:
            val = source_param.AsString() or ""
            target_param.Set(val)
        elif stype == StorageType.Double:
            target_param.Set(source_param.AsDouble())
        elif stype == StorageType.Integer:
            target_param.Set(source_param.AsInteger())
        elif stype == StorageType.ElementId:
            target_param.Set(source_param.AsElementId() or ElementId.InvalidElementId)
        else:
            return False
    except Exception as e:
        print("Failed to copy parameter: {}".format(e))
        return False
    return True


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

if __name__ == "__main__":
    fam_inst = pick_family(uidoc)
    family = fam_inst.Symbol.Family

    src_param = pick_parameter(fam_inst, "Select Source Parameter to copy from")
    tgt_param = pick_parameter(fam_inst, "Select Target Parameter to paste to")

    if not src_param or not tgt_param:
        forms.alert("No parameters selected.", exitscript=True)

    options = [
        "Only instances of family: {}".format(family.Name),
        "All of same category: {}".format(fam_inst.Category.Name),
        "All instances with both parameters"
    ]

    choice = forms.CommandSwitchWindow.show(
        options,
        message="Select scope for parameter sync",
        title="Parameter Sync Options"
    )

    if not choice:
        forms.alert("Cancelled by user.", exitscript=True)

    if "Only instances of family" in choice:
        matches = get_all_family_instances(doc, fam_inst.Symbol)
    elif "All of same category" in choice:
        matches = get_instances_with_both_params_same_category(doc, fam_inst, src_param, tgt_param)
    else:
        matches = get_instances_with_both_params(doc, src_param, tgt_param)

    count = 0
    t = Transaction(doc, "Sync Family Parameters")
    t.Start()

    for inst in matches:
        src = inst.LookupParameter(src_param)
        tgt = inst.LookupParameter(tgt_param)
        if copy_parameter_value(src, tgt):
            count += 1

    t.Commit()

    MessageBox.Show("Updated {} instances.".format(count))
