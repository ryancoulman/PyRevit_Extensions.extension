from Autodesk.Revit.DB import *
from pyrevit import revit, forms
from System.Collections.Generic import List, ICollection


uidoc = revit.uidoc
doc = revit.doc

BICS = [
    BuiltInCategory.OST_PipeAccessory
]
BICS_LIST = List[BuiltInCategory](BICS)


def get_filterable_params(doc, bic_ids):
    """
    Returns list of tuples:
        (name, built_in_param_id, guid_str)
    """
    results = []

    cat_ids = List[ElementId]([ElementId(bic) for bic in bic_ids])
    print("Collecting filterable parameters for {} categories".format(cat_ids.Count))

    filterable = ParameterFilterUtilities.GetFilterableParametersInCommon(
        doc, cat_ids
    )
    print("Found {} filterable parameters".format(filterable.Count))

    paramBindings = doc.ParameterBindings

    for pid in filterable:
        int_id = pid.IntegerValue

        # --- Case 1: Built-in parameter ---
        # Check safely if the integer corresponds to a known BuiltInParameter enum
        if BuiltInParameter.IsDefined(BuiltInParameter, int_id):
            bip = BuiltInParameter(int_id)

            if bip != BuiltInParameter.INVALID:
                name = LabelUtils.GetLabelFor(bip)
                results.append((name, int_id, ""))   # no GUID for built-ins
                continue

        # --- Case 2: Shared or Project Parameter (ParameterElement) ---
        pe = doc.GetElement(pid)
        if isinstance(pe, ParameterElement):
            definition = pe.GetDefinition()
            name = definition.Name if definition else "<Unnamed>"

            Binding = paramBindings.get_Item(definition)
            if isinstance(Binding, TypeBinding):
                pass

            if isinstance(pe, SharedParameterElement):
                guid_str = str(pe.GuidValue)
            else:
                guid_str = ""

            results.append((name, -1, guid_str))

    return results

def print_results(results):
    for name, int_id, guid_str in results:
        if int_id != -1:
            print("Built-in Parameter: {} (ID: {})".format(name, int_id))
        else:
            print("Parameter: {} (GUID: {})".format(name, guid_str))


def params_from_dummy_element(doc, bic_list):
    bic = bic_list[0]  # Just get params from the first category
    collector = FilteredElementCollector(doc).OfCategory(bic).WhereElementIsNotElementType()
    dummy_elem = collector.FirstElement()
    if not dummy_elem:
        print("No elements found for category: {}".format(bic))
        return []

    params = dummy_elem.Parameters
    param_list = []
    for p in params:
        param_list.append(p)
    return param_list

def compare_param_lists(dummy_list, common_list):
    names1 = set(p.Definition.Name for p in dummy_list)
    names2 = set(p[0] for p in common_list)

    print(len(names1), "parameters in list 1")
    print(len(names2), "parameters in list 2")

    only_in_list1 = names1 - names2
    only_in_list2 = names2 - names1

    # get common parameters
    common_params = names1 & names2

    print("Common parameters ({}):".format(len(common_params)))
    for name in common_params:
        print(" - {}".format(name))

    print("Parameters only in list 1:")
    for name in only_in_list1:
        print(" - {}".format(name))

    print("Parameters only in list 2:")
    for name in only_in_list2:
        print(" - {}".format(name))

def get_all_parameter_names(doc):
    names = set()

    # Built-in parameters
    for bip in BuiltInParameter.GetValues(BuiltInParameter):
        if bip == BuiltInParameter.INVALID:
            continue
        try:
            name = LabelUtils.GetLabelFor(bip)
            if name:
                names.add(name)
        except:
            pass

    # Shared + Project parameters
    elems = FilteredElementCollector(doc).OfClass(ParameterElement)
    for pe in elems:
        d = pe.GetDefinition()
        if d:
            names.add(d.Name)

    return sorted(list(names))

if __name__ == "__main__":
    # results = get_filterable_params(doc, BICS_LIST)
    # print_results(results)
    # # Get parameters from dummy elements
    # params_list = params_from_dummy_element(doc, BICS)
    # # print("\n\nParameters from dummy element:")
    # # for p in params_list:
    # #     print("Parameter from dummy element: {}".format(p.Definition.Name))
    # # compare_param_lists(params_list, results)  # Compare the list to the results from get_filterable_params

    # ordered_results = sorted(results, key=lambda x: x[0])
    # print("\n\nOrdered Filterable Parameters:")
    # for name, int_id, guid_str in ordered_results:
    #     print(name)
    all_param_names = get_all_parameter_names(doc)
    print("All parameter names in document ({}):".format(len(all_param_names)))
    strings = ""
    for name in all_param_names:
        strings += name + "\n"
    print(len(all_param_names))