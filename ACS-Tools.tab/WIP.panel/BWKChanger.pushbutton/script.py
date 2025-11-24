from Autodesk.Revit.DB import *
from pyrevit import revit, forms
from System.Collections.Generic import List


doc = revit.doc
active_view = revit.active_view
BWK_SOURCE_NAME = "BWK_ACS_Builderswork Opening (Floor) 2021"
BWK_DEST_NAME = "BWK_ACS_Builderswork Opening (Floor)"
SOURCE_PARAM_NAME = "ACS Builderswork Hole Length"
DEST_PARAM_NAME = SOURCE_PARAM_NAME

def get_generic_models_in_view(view):
    return FilteredElementCollector(doc, view.Id).\
    OfCategory(BuiltInCategory.OST_GenericModel).\
    WhereElementIsNotElementType().\
    ToElements()

def get_generic_models_in_project():
    return FilteredElementCollector(doc).\
    OfCategory(BuiltInCategory.OST_GenericModel).\
    WhereElementIsNotElementType().\
    ToElements()

def collect_bwk_of_dest_name():
    generic_models = get_generic_models_in_view(active_view)
    bwk_matching = []
    for gm_elem in generic_models:
        # Check family name matches BWK_NAME
        fam_id = gm_elem.GetTypeId()
        fam = doc.GetElement(fam_id)
        fam_name = fam.Family.Name
        if fam_name == BWK_SOURCE_NAME:
            bwk_matching.Add(gm_elem)
    return bwk_matching

def collect_source_bwk_of_name():
    generic_models = get_generic_models_in_project()
    dest_family_typeId = {}
    for gm_elem in generic_models:
        # Check family name matches BWK_NAME
        fam_id = gm_elem.GetTypeId()
        fam = doc.GetElement(fam_id)
        fam_name = fam.Family.Name
        if fam_name == BWK_DEST_NAME:
            dest_family_typeId[gm_elem.Name] = fam_id
    return dest_family_typeId

def get_length_of_bwk_in_view(bwk_elem):
    param = bwk_elem.LookupParameter(SOURCE_PARAM_NAME)
    if param:
        return param.AsDouble()
    return 0.0

def change_family_keep_type(bwk_elem, dest_family):
    # current type name
    type_name = bwk_elem.Name

    dest_type = dest_family[type_name]

    if dest_type is None:
        print("No matching type '{}' in destination family".format(type_name))

    # change the element's type
    old_fam_name = bwk_elem.Symbol.FamilyName + " : " + bwk_elem.Name
    new_elem_id = bwk_elem.ChangeTypeId(dest_type)
    if new_elem_id == ElementId.InvalidElementId:
        new_elem_id = bwk_elem.Id 
    new_fam_name = doc.GetElement(new_elem_id).Symbol.FamilyName + " : " + bwk_elem.Name

    print("Changed {} -> {}".format(old_fam_name, new_fam_name))
    return new_elem_id

def set_new_parameter(new_bwk_elem, length_value):
    param = new_bwk_elem.LookupParameter(DEST_PARAM_NAME)
    if param:
        param.Set(length_value)
        print("Changed element ID {} to new family type with length {}".format(new_bwk_elem.Id, length_value))
    else:
        print("Parameter {} not found in element ID {}".format(DEST_PARAM_NAME, new_bwk_elem.Id))

    comments_param = new_bwk_elem.LookupParameter("Comments")
    if comments_param:
        comments_param.Set("Changed by ACS-Tools BWK Changer")


if __name__ == "__main__":

    dest_family_typeId = collect_source_bwk_of_name()
    bwk_matching = collect_bwk_of_dest_name()

    if not dest_family_typeId:
        forms.alert("No destination BWK family type found in the model.", title="Error", exitscript=True)

    dict_lengths = {}

    with Transaction(doc, "Change BWK Family Types") as t:
        t.Start()
        for bwk_elem in bwk_matching:
            length_value = get_length_of_bwk_in_view(bwk_elem)
            elemId = change_family_keep_type(bwk_elem, dest_family_typeId)
            dict_lengths[elemId] = length_value
        t.Commit()
    print("Successfully changed {} BWK elements.".format(len(bwk_matching)))

    print("Setting new parameter values...")
    with Transaction(doc, "Set New Parameter Values") as t2:
        t2.Start()
        for elemId, length_value in dict_lengths.items():
            new_bwk_elem = doc.GetElement(elemId)
            set_new_parameter(new_bwk_elem, length_value)
        t2.Commit()