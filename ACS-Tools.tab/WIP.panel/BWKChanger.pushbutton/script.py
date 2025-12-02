#////// Configuration - Edit as needed //////#
BWK_SOURCE_NAME = "BWK_ACS_Builderswork Opening (Floor) 2021" # Source BWK Family Name
BWK_DEST_NAME = "BWK_ACS_Builderswork Opening (Floor)" # Destination BWK Family Name
SOURCE_PARAM_NAME = "ACS Builderswork Hole Length" # Name of Parameter in source family to copy value from
DEST_PARAM_NAME = SOURCE_PARAM_NAME # Name of Parameter in source family to copy value from
#////// End of Configuration //////#

#////// Description //////#
__doc__ = """ This script changes all BWK Generic Model elements of a specified source family name in 
the active view to a specified destination family name, keeping the same type names where possible. 
It also copies the value of a specified parameter from the source elements to the destination elements."""
#////// End of Description //////#

# ////// Script //////#
from Autodesk.Revit.DB import *
from pyrevit import revit, forms

__title__ = "BWK\nChanger"

doc = revit.doc
active_view = revit.active_view

def get_generic_models_in_view():
    return FilteredElementCollector(doc, active_view.Id).\
    OfCategory(BuiltInCategory.OST_GenericModel).\
    WhereElementIsNotElementType().\
    ToElements()

def get_generic_models_in_project():
    return FilteredElementCollector(doc).\
    OfCategory(BuiltInCategory.OST_GenericModel).\
    WhereElementIsNotElementType().\
    ToElements()

def collect_bwk_of_source_name():
    generic_models = get_generic_models_in_view()
    bwk_matching = []
    for gm_elem in generic_models:
        # Check family name matches BWK_NAME
        fam_id = gm_elem.GetTypeId()
        fam = doc.GetElement(fam_id)
        fam_name = fam.Family.Name
        if fam_name == BWK_SOURCE_NAME:
            bwk_matching.append(gm_elem)
    if not bwk_matching:
        forms.alert("No BWK elements of family '{}' found in the active view.".format(BWK_SOURCE_NAME), title="Error", exitscript=True)
    return bwk_matching

# Collects destination BWK family types in the project and returns a dictionary of type names to ElementIds
def collect_bwk_of_dest_name():
    generic_models = get_generic_models_in_project()
    dest_family_typeId = {}
    for gm_elem in generic_models:
        # Check family name matches BWK_NAME
        fam_id = gm_elem.GetTypeId()
        fam = doc.GetElement(fam_id)
        fam_name = fam.Family.Name
        if fam_name == BWK_DEST_NAME:
            dest_family_typeId[gm_elem.Name] = fam_id
    if not dest_family_typeId:
        forms.alert("No BWK family types of family '{}' found in the project.".format(BWK_DEST_NAME), title="Error", exitscript=True)
    return dest_family_typeId

def get_length_of_bwk_in_view(bwk_elem):
    param = bwk_elem.LookupParameter(SOURCE_PARAM_NAME)
    if not param:
        print("Parameter: {} not found in element ID {}. No value will be set in the destination element. " \
        "Please manually change the parameter using its Id to find.".format(SOURCE_PARAM_NAME, bwk_elem.Id))
        return None
    if param.StorageType == StorageType.Double:
        return param.AsDouble()
    elif param.StorageType == StorageType.Integer:
        return param.AsInteger()
    elif param.StorageType == StorageType.String:
        return param.AsValueString() or param.AsString()
    elif param.StorageType == StorageType.ElementId:
        return param.AsElementId()
    print("Parameter: {} in element ID {} has an unrecognized storage type. No value will be set in the destination element. " \
    "Please manually change the parameter using its Id to find.".format(SOURCE_PARAM_NAME, bwk_elem.Id))
    return None

def change_family_keep_type(bwk_elem, dest_family):
    if bwk_elem is None:
        print("Error: bwk_elem is None. Skipping.")
        return None
    
    # current type name
    type_name = bwk_elem.Name

    # find matching type in destination family
    if type_name not in dest_family:
        print("Could not find source type '{}' in destination family. Skipping element of Id {}".format(type_name, bwk_elem.Id))
        return None
    dest_type = dest_family[type_name]
    if dest_type is None:
        print("Error: Destination type is None for type name '{}'. Skipping element of Id {}".format(type_name, bwk_elem.Id))
        return None

    # change the element's type
    new_elem_id = bwk_elem.ChangeTypeId(dest_type)
    # Doesnt always create new id (in which case it returns InvalidElementId)
    if new_elem_id == ElementId.InvalidElementId:
        new_elem_id = bwk_elem.Id 

    # print change info
    try:
        old_fam_name = bwk_elem.Symbol.FamilyName + " : " + type_name
        new_fam_name = doc.GetElement(new_elem_id).Symbol.FamilyName + " : " + type_name
        print("Changed {} -> {}".format(old_fam_name, new_fam_name))
    except: 
        print("Changed element Id {} to new family type Id {}".format(bwk_elem.Id, dest_type))

    return new_elem_id

# Set new parameter value on the new BWK element
def set_new_parameter(new_bwk_elem, length_value):
    if length_value is None:
        return
    param = new_bwk_elem.LookupParameter(DEST_PARAM_NAME)
    if param:
        param.Set(length_value)
        print("Changed {} Parameter of family {} {} to {}".format(DEST_PARAM_NAME, new_bwk_elem.Symbol.FamilyName, new_bwk_elem.Name, length_value))
    else:
        print("Parameter: {} not found in element ID {}. Please manually change the parameter using its Id to find.".format(DEST_PARAM_NAME, new_bwk_elem.Id))


if __name__ == "__main__":

    dest_family_typeId = collect_bwk_of_dest_name()
    bwk_matching = collect_bwk_of_source_name()

    dict_lengths = {}

    with Transaction(doc, "Change BWK Family Types") as t:
        t.Start()
        for bwk_elem in bwk_matching:
            length_value = get_length_of_bwk_in_view(bwk_elem)
            if length_value is None:
                continue
            elemId = change_family_keep_type(bwk_elem, dest_family_typeId)
            if elemId is None:
                continue
            dict_lengths[elemId] = length_value
        t.Commit()
    print("Successfully changed {} BWK elements.".format(len(bwk_matching)))

    print("\nSetting new parameter values...")
    with Transaction(doc, "Set New Parameter Values") as t2:
        t2.Start()
        for elemId, length_value in dict_lengths.items():
            new_bwk_elem = doc.GetElement(elemId)
            set_new_parameter(new_bwk_elem, length_value)
        t2.Commit()