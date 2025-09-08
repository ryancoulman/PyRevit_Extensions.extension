from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory, Transaction, XYZ, IndependentTag
from pyrevit import revit, DB

# Start the script
doc = revit.doc

# Define offset distance 
offset_distance = 300 / 304.8
offset_x = -140 / 304.8


# Start a transaction to modify the document
with Transaction(doc, "Tag and Annotate Floor Boxes") as t:
    t.Start()

    # Collect all electrical equipment (floor boxes) in the active view
    view_id = doc.ActiveView.Id
    floor_boxes = FilteredElementCollector(doc, view_id)\
                    .OfCategory(BuiltInCategory.OST_ElectricalFixtures)\
                    .WhereElementIsNotElementType()\
                    .ToElements()
    
    # Loop through each floor box
    print("Number of electrical equipment in view: {}".format(len(floor_boxes)))
    for box in floor_boxes:
        family_name = box.Symbol.Family.Name
        type_name = box.Name

        # Check if the family name starts with 'FB'
        if family_name.startswith('FB'):
            # Write the family name to the 'Comments' parameter
            comments_param = box.LookupParameter('Comments')
            if comments_param is not None:
                box_type = type_name.split()[1]
                box_type = 'JB' if box_type == 'Junction' else box_type
                comments_param.Set(box_type)
            else:
                print("Floor box ID {} has no 'Comments' parameter.".format(box.Id.IntegerValue))

            # Get the location of the floor box
            location = box.Location
            if isinstance(location, DB.LocationPoint):
                # Get the position of the floor box
                box_position = location.Point
                
                # Create the tag location (10mm above the box)
                tag_position = box_position + XYZ(offset_x, offset_distance, 0)
                print("box position: {}, tag position: {}".format(box_position, tag_position))
                
                # Create an annotation tag
                tag = IndependentTag.Create(doc, doc.ActiveView.Id, DB.Reference(box), False, DB.TagMode.TM_ADDBY_CATEGORY, DB.TagOrientation.Horizontal, tag_position)
            else:
                print("Floor box ID {} has no valid location.".format(box.Id.IntegerValue))

    t.Commit()

# End of the script
