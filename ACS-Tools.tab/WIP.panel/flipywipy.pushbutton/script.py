import clr
clr.AddReference('RevitAPI')
clr.AddReference('RevitAPIUI')
from Autodesk.Revit.DB import *
from Autodesk.Revit.UI import *
from Autodesk.Revit.UI.Selection import ObjectType
from System.Collections.Generic import List

# Get the active document and UI document
uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

def get_element_direction(elem):
    """Get the primary direction vector of an element"""
    
    # For Grid lines
    if isinstance(elem, Grid):
        curve = elem.Curve
        direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
        return XYZ(direction.X, direction.Y, 0).Normalize()
    
    # For Family Instances with FacingOrientation
    if isinstance(elem, FamilyInstance) and elem.FacingOrientation:
        facing = elem.FacingOrientation
        return XYZ(facing.X, facing.Y, 0).Normalize()
    
    # For Detail Lines or Model Lines
    if isinstance(elem, CurveElement):
        curve = elem.GeometryCurve
        direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
        return XYZ(direction.X, direction.Y, 0).Normalize()
    
    # For Walls
    if isinstance(elem, Wall):
        loc_curve = elem.Location
        if isinstance(loc_curve, LocationCurve):
            curve = loc_curve.Curve
            direction = (curve.GetEndPoint(1) - curve.GetEndPoint(0)).Normalize()
            return XYZ(direction.X, direction.Y, 0).Normalize()
    
    return None

def get_element_location(elem):
    """Get the location point of an element"""
    loc = elem.Location
    if isinstance(loc, LocationPoint):
        return loc.Point
    elif isinstance(loc, LocationCurve):
        # Use midpoint of curve
        curve = loc.Curve
        return curve.Evaluate(0.5, True)
    return None

def align_element_in_place(source_elem, target_elem):
    """Align source element to match target's direction without changing position"""
    
    # Get directions
    source_dir = get_element_direction(source_elem)
    target_dir = get_element_direction(target_elem)
    
    if not source_dir or not target_dir:
        return False, "Could not determine direction"
    
    # Get source location
    source_point = get_element_location(source_elem)
    if not source_point:
        return False, "Could not determine location"
    
    # Calculate signed angle around Z axis
    cross = source_dir.CrossProduct(target_dir)
    angle = source_dir.AngleTo(target_dir)
    
    # If cross product points down (negative Z), reverse the angle
    if cross.Z < 0:
        angle = -angle
    
    # Skip if already aligned
    if abs(angle) < 1e-6:
        return False, "Already aligned"
    
    # Create rotation axis at element's location
    axis = Line.CreateBound(source_point, source_point + XYZ.BasisZ)
    
    # Perform rotation
    try:
        ElementTransformUtils.RotateElement(doc, source_elem.Id, axis, angle)
        return True, "Success"
    except Exception as e:
        return False, str(e)

# Main execution
try:
    # Check if user has pre-selected elements
    selected_ids = uidoc.Selection.GetElementIds()
    source_elems = []
    
    if selected_ids.Count > 0:
        # Use current selection as source elements
        source_elems = [doc.GetElement(id) for id in selected_ids]
        uidoc.Selection.SetElementIds(List[ElementId]())  # Clear selection
    else:
        # Prompt user to select source elements
        source_refs = uidoc.Selection.PickObjects(ObjectType.Element, "Select source element(s)")
        source_elems = [doc.GetElement(ref.ElementId) for ref in source_refs]
    
    if not source_elems:
        TaskDialog.Show("No elements selected", "No source elements were selected.")
    else:
        # Prompt user to select target element
        target_ref = uidoc.Selection.PickObject(ObjectType.Element, "Select target element (direction reference)")
        target_elem = doc.GetElement(target_ref.ElementId)
        
        # Perform alignment for all source elements
        t = Transaction(doc, "Align In Place")
        t.Start()
        
        success_count = 0
        fail_count = 0
        skip_count = 0
        
        for source_elem in source_elems:
            success, msg = align_element_in_place(source_elem, target_elem)
            if success:
                success_count += 1
            elif "Already aligned" in msg:
                skip_count += 1
            else:
                fail_count += 1
        
        t.Commit()
        
        # Show summary
        result_msg = "{} element(s) aligned".format(success_count)
        if skip_count > 0:
            result_msg += ", {} already aligned".format(skip_count)
        if fail_count > 0:
            result_msg += ", {} failed".format(fail_count)
        
        # TaskDialog.Show("Align In Place Complete", result_msg)
    
except Exception as e:
    TaskDialog.Show("Error", str(e))