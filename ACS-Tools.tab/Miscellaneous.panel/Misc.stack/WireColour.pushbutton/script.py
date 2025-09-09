from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction
from pyrevit import revit


doc = revit.doc

# Function to determine the color based on circuit text
def get_color_from_circuit(circuit_text):
    circuit_text = circuit_text.split('/')[0]  # Use only the first part if split
    color_map = {
        'L1': 'Red',
        'L2': 'Green',
        'L3': 'Blue'
    }
    return color_map.get(circuit_text, 'Unknown')

# Start a transaction (required for modifying elements)
with Transaction(doc, "Update Wire Colors") as t:
    t.Start()

    # Collect all wires in the active view
    view_id = doc.ActiveView.Id
    wires = FilteredElementCollector(doc, view_id).OfCategory(BuiltInCategory.OST_Wire).WhereElementIsNotElementType().ToElements()

    # Loop through each wire
    for wire in wires:
        # Get the circuit text from the wire
        circuit_param = wire.LookupParameter('Circuits')
        
        if circuit_param is not None:
            circuit_text = circuit_param.AsString()
            color = get_color_from_circuit(circuit_text)
            
            # Write the color into the 'SystemCategory' parameter (replace with actual parameter name if different)
            system_category_param = wire.LookupParameter('SystemCategory')
            
            if system_category_param is not None:
                # Set the parameter value to the color
                system_category_param.Set(color)
                print("Wire ID {} Circuit: {}, Color updated to: {}".format(wire.Id.IntegerValue, circuit_text, color))
            else:
                print("Wire ID {} has no SystemCategory parameter.".format(wire.Id.IntegerValue))
        else:
            print("Wire ID {} has no Circuit parameter.".format(wire.Id.IntegerValue))

    print("{} Wires successfully tagged with their respective colour".format(wires.Count))
    t.Commit()

# End of the script
