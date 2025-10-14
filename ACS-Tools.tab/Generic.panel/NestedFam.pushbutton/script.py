# -*- coding: utf-8 -*-

import clr
import os
# Get the path to your DLL — assuming it's in the same folder as this script
dll_path = os.path.join(os.path.dirname(__file__), "NestedFamily.dll")
# Add the reference so .NET knows about your assembly
clr.AddReferenceToFileAndPath(dll_path)
# Now you can safely import your C# class
from NestedFamily import NestedFamilyOptnsWindow
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import forms
from System.Windows import MessageBox



uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document



# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------

def pick_nested_family(uidoc):
    """Prompt user to pick a nested family instance."""
    ref = uidoc.Selection.PickObject(ObjectType.Element, "Select instance of nested family")
    elem = uidoc.Document.GetElement(ref.ElementId)
    if isinstance(elem, FamilyInstance) and elem.SuperComponent is not None:
        return elem
    else:
        forms.alert("Selected element is not a nested family instance.", exitscript=True)


def get_family_parameters(family_instance):
    """Return a list of writable parameter names from a family instance."""
    params = []
    for p in family_instance.Parameters:
        if not p.IsReadOnly:
            params.append(p.Definition.Name)
    return sorted(set(params))


def pick_parameter(family_instance, title="Select Parameter"):
    """Prompt user to pick a parameter name from the given family instance."""
    param_names = get_family_parameters(family_instance)
    return forms.SelectFromList.show(param_names,
                                     title=title,
                                     button_name="Select",
                                     multiselect=False)


def get_all_nested_instances(doc, nested_family_symbol):
    """Return all instances of a given nested family type in the project."""
    collector = FilteredElementCollector(doc).OfClass(FamilyInstance)
    return [i for i in collector if i.Symbol.Id == nested_family_symbol.Id]


def copy_parameter_value(source_param, target_param):
    """Copy value from source parameter to target parameter if compatible."""
    if not source_param or not target_param or target_param.IsReadOnly:
        return False

    stype = source_param.StorageType

    try:
        if stype == StorageType.String:
            val = source_param.AsString() or ""
            target_param.Set(str(val))
        elif stype == StorageType.Double:
            val = source_param.AsDouble()
            target_param.Set(float(val))
        elif stype == StorageType.Integer:
            val = source_param.AsInteger()
            target_param.Set(int(val))
        elif stype == StorageType.ElementId:
            val = source_param.AsElementId()
            if val is None:
                val = ElementId.InvalidElementId
            target_param.Set(ElementId(val.IntegerValue))
        else:
            return False
    except Exception as e:
        print("Failed to copy parameter: {}".format(e))
        return False

    return True


# ------------------------------------------------------------
# Main Logic
# ------------------------------------------------------------

if __name__ == "__main__":
    nested_inst = pick_nested_family(uidoc)
    super_inst = nested_inst.SuperComponent

    nested_family = nested_inst.Symbol.Family
    super_family = super_inst.Symbol.Family

    # --- Call WPF form from DLL ---
    confirmed, apply_to_all_supers, super_to_nested, same_param = NestedFamilyOptnsWindow.ShowDialogAndReturn(
        super_family.Name, nested_family.Name
    )

    if not confirmed:
        forms.alert("Operation cancelled.", exitscript=True)

    # --- Parameter selection ---
    if same_param:
        # Use same parameter name
        param_name = pick_parameter(nested_inst, "Select parameter to sync")
        source_param_name = target_param_name = param_name
    else:
        # Choose source and target separately
        source_param_name = pick_parameter(super_inst, "Select Source Parameter")
        target_param_name = pick_parameter(nested_inst, "Select Target Parameter")


    # --- Collect nested instances ---  
    all_nested_instances = get_all_nested_instances(doc, nested_inst.Symbol)

    count_updated = 0
    t = Transaction(doc, "Sync Nested Family Parameters")
    t.Start()

    for n in all_nested_instances:
        parent = n.SuperComponent
        if not parent:
            continue

        # Filter based on scope choice
        if not apply_to_all_supers:
            if parent.Symbol.Family.Id != super_family.Id:
                continue

        # Determine copy direction
        if super_to_nested:
            source = parent
            target = n
        else:
            source = n
            target = parent

        source_param = source.LookupParameter(source_param_name)
        target_param = target.LookupParameter(target_param_name)

        if copy_parameter_value(source_param, target_param):
            count_updated += 1

    t.Commit()

    MessageBox.Show("Updated {} nested family instances.".format(count_updated))
