from Autodesk.Revit.DB import *
from pyrevit import forms 
import clr
import math
clr.AddReference("System.Collections")
from System.Collections.Generic import List

__title__ = "Fab\nReplacer"
"""Replaces selected fabrication parts with new type of fabrication parts (only for straights)"""

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

SERVICE = "CHt (60) Electrical Services: CHt_Lighting & Power"
PALLETTE = (1, "Unistrut Tray PG") # (index, name)
BUTTON =  (0, "Straight PG")
CONDITION = (0, "Unistrut Tray Straight PG")

PALLETE_BUTTON_DICT_MAPPER = { # value: (index, name)
        "Straight EZ": (0, "Straight PG"), # straight parts
        "Fabricated Right Angle Bend EZ": (3, "Bend 90 PG") # 90 degree bends 
}

LEVEL_NAME = "PP-00-DATUM"

SIZE_PARAM = ("Product Entry", "100 Heavy") # (parameter name, desired value)
ELEVATION_PARAM_NAME = "Bottom"
LENGTH_PARAM = "Length"

def get_fabrication_services(FabConfig, old_elem=None):
        """Get all Fabrication Services in the document."""
        def get_button_index(old_elem):
                button_name_param = old_elem.LookupParameter("Product Short Description")
                if not button_name_param:
                        print("Button name parameter not found in old element.")
                        return 
                button_name = button_name_param.AsValueString() or button_name_param.AsString()
                if not button_name:
                        print("Button name not found in old element.")
                        return
                if button_name in PALLETE_BUTTON_DICT_MAPPER:
                        return PALLETE_BUTTON_DICT_MAPPER[button_name][0]
                else:
                        print("Button name '{}' not found in mapper.".format(button_name))
                        return
        def get_service_name(old_elem):
                service_name_param = old_elem.LookupParameter("Fabrication Service")
                if not service_name_param:
                        print("Service name parameter not found in old element.")
                        return SERVICE
                service_name = service_name_param.AsValueString() or service_name_param.AsString()
                return service_name
        
        service_name = get_service_name(old_elem) if old_elem else SERVICE
        matching_service = None
        all_services = FabConfig.GetAllServices()
        for service in all_services:
                if service.Name == service_name:
                        matching_service = service
                        break
        if not matching_service:
                print("Fabrication Service '{}' not found.".format(service_name))
                return 
        
        for i in range(matching_service.PaletteCount):
                palette_name = matching_service.GetPaletteName(i)
        
        button_index = get_button_index(old_elem) if old_elem else BUTTON[0]

        return matching_service.GetButton(PALLETTE[0], button_index)

def get_button_condition(fab_button):
    """Get the condition of a Fabrication Button."""
    for i in range(fab_button.ConditionCount):
        condition_name = fab_button.GetConditionName(i)
        ondtion_description = fab_button.GetConditionDescription(i)
        print("Condition Name: {}, Description: {}, Index: {}".format(condition_name, ondtion_description, i))

def get_elementId_level():
        target_levels = FilteredElementCollector(doc).OfClass(Level).ToElements()
        for level in target_levels:
                if level.Name == LEVEL_NAME:
                        return level.Id
        
        print("Level not found.")
        return None

def get_user_selection():
        selection = uidoc.Selection.GetElementIds()
        if not selection:
                print("No elements selected.")
                return []
        return [doc.GetElement(id) for id in selection]

def set_correct_size(new_elem):
        size_param = new_elem.LookupParameter(SIZE_PARAM[0])

        if not size_param:
                print("Size parameter not found.")
                return
        if size_param.IsReadOnly:
                print("Size parameter is read-only.")
                return
        
        success = size_param.Set(SIZE_PARAM[1])
        if not success:
                print("Failed to set size parameter.")

def set_new_level_or_length(old_elem, new_elem, param_name):
        old_param = old_elem.LookupParameter(param_name)
        if not old_param:
                print("Old element parameter '{}' not found.".format(param_name))
                return  
        param_value = old_param.AsDouble()
        if not param_value:
                print("Old element parameter '{}' value not found.".format(param_name))
                return
        
        new_param = new_elem.LookupParameter(param_name)
        if not new_param:
                print("New element parameter '{}' not found.".format(param_name))
                return
        if new_param.IsReadOnly:
                print("New element parameter '{}' is read-only.".format(param_name))
                return
        
        success = new_param.Set(param_value)
        if not success:
                print("Failed to set new element parameter '{}'.".format(param_name))

def set_new_level(old_elem, new_elem):
        set_new_level_or_length(old_elem, new_elem, ELEVATION_PARAM_NAME)

def set_new_length(old_elem, new_elem):
        if new_elem.IsAStraight:
                set_new_level_or_length(old_elem, new_elem, LENGTH_PARAM)

def set_new_loc_curve(old_elem, new_elem):
        old_loc = old_elem.Location
        new_loc = new_elem.Location


        """For straight parts (ducts/pipes)"""
        if isinstance(old_loc, LocationCurve) and isinstance(new_loc, LocationCurve):
                old_curve = old_loc.Curve
                new_curve = new_loc.Curve
                
                # Get old part's endpoints
                old_start = old_curve.GetEndPoint(0)
                old_end = old_curve.GetEndPoint(1)
                
                # Get new part's current endpoints
                new_start = new_curve.GetEndPoint(0)
                new_end = new_curve.GetEndPoint(1)
                
                # Step 1: Move the new element so its start point matches old start point
                translation = old_start - new_start
                ElementTransformUtils.MoveElement(doc, new_elem.Id, translation)
                
                # Step 2: Rotate to align the direction
                # Recalculate new curve after movement
                new_loc = new_elem.Location  # Refresh location
                new_curve = new_loc.Curve
                new_start_after_move = new_curve.GetEndPoint(0)
                new_end_after_move = new_curve.GetEndPoint(1)
                
                # Calculate direction vectors
                old_direction = (old_end - old_start).Normalize()
                new_direction = (new_end_after_move - new_start_after_move).Normalize()
                
                # Calculate rotation angle
                angle = new_direction.AngleTo(old_direction)
                
                if abs(angle) > 0.0001:  # Only rotate if there's a meaningful difference
                        # Create rotation axis through the start point
                        # Cross product gives us the perpendicular axis
                        cross = new_direction.CrossProduct(old_direction)
                        
                        if cross.GetLength() > 0.0001:  # Vectors aren't parallel
                                axis_direction = cross.Normalize()
                                axis = Line.CreateBound(old_start, old_start + axis_direction)
                                ElementTransformUtils.RotateElement(doc, new_elem.Id, axis, angle)
                        elif new_direction.DotProduct(old_direction) < 0:  # 180 degree flip
                                # Create arbitrary perpendicular axis
                                if abs(old_direction.Z) < 0.9:
                                        axis_direction = old_direction.CrossProduct(XYZ.BasisZ).Normalize()
                                else:
                                        axis_direction = old_direction.CrossProduct(XYZ.BasisX).Normalize()
                                axis = Line.CreateBound(old_start, old_start + axis_direction)
                                ElementTransformUtils.RotateElement(doc, new_elem.Id, axis, math.pi)
                
        elif isinstance(old_loc, LocationPoint) and isinstance(new_loc, LocationPoint):
                # Get the old element's position
                old_point = old_loc.Point
                # Move the new element to the old position
                new_point = new_loc.Point
                translation = old_point - new_point
                ElementTransformUtils.MoveElement(doc, new_elem.Id, translation)
                # Match rotation
                old_rotation = old_loc.Rotation
                new_rotation = new_loc.Rotation
                
                if abs(old_rotation - new_rotation) > 0.0001:  # If different
                        rotation_diff = old_rotation - new_rotation
                        # Rotate around Z axis at the element's location
                        axis = Line.CreateBound(old_point, old_point + XYZ.BasisZ)
                        ElementTransformUtils.RotateElement(doc, new_elem.Id, axis, rotation_diff)

        elif isinstance(old_loc, Location) and isinstance(new_loc, Location):
                print("Both elements have generic Location. Manual adjustment may be needed.")

def check_elevations(old_elem, new_elem):
        old_param = old_elem.LookupParameter(ELEVATION_PARAM_NAME)
        new_param = new_elem.LookupParameter(ELEVATION_PARAM_NAME)
        if not old_param or not new_param:
                print("Elevation parameter not found in one of the elements.")
                return
        old_elev = old_param.AsDouble()
        new_elev = new_param.AsDouble()
        if abs(old_elev - new_elev) > 0.0001:
                print("Elevation mismatch: Old Elevation = {}, New Elevation = {}".format(old_elev, new_elev))

if __name__ == "__main__":

        fab_config = FabricationConfiguration.GetFabricationConfiguration(doc)
        level_elementId = get_elementId_level()

        selected_elems = get_user_selection()
        with Transaction(doc, "Create Fabrication Button") as t:
                t.Start()
                for old_elem in selected_elems:
                        fab_button = get_fabrication_services(fab_config, old_elem)
                        new_fab_elem = FabricationPart.Create(doc, fab_button, CONDITION[0], level_elementId)
                        set_correct_size(new_fab_elem)
                        set_new_length(old_elem, new_fab_elem)
                        set_new_loc_curve(old_elem, new_fab_elem)
                        set_new_level(old_elem, new_fab_elem)
                        check_elevations(old_elem, new_fab_elem)
                t.Commit()
        
        print("Created Fabrication Element with ID: {}".format(new_fab_elem.Id.IntegerValue))