# MEP Fabrication Service Extraction for Valves (Connector-Based)
# This script identifies which MEP fabrication service each valve belongs to
# Uses connector locations for more accurate proximity detection

from pyrevit import revit, forms
from Autodesk.Revit.DB import *


# Get current document
uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

# Configuration
Tolerance_mm = 50  # millimeters
# Convert tolerance to feet (Revit internal units)
PROXIMITY_TOLERANCE = Tolerance_mm / 304.8  # feet - can be tighter now that we're using connectors

def get_connector_manager(element):
    """Get connector manager from an element"""
    try:
        # Try MEP elements
        if hasattr(element, 'ConnectorManager'):
            return element.ConnectorManager
        # Try fabrication elements
        elif hasattr(element, 'FabricationConnectorManager'):
            return element.FabricationConnectorManager
        elif hasattr(element, 'MEPModel'): # For Valves
            return element.MEPModel.ConnectorManager
    except:
        pass
    return None

def get_all_connectors(element):
    """Get all connectors from an element with their locations"""
    connectors_info = []
    connector_mgr = get_connector_manager(element)
    
    if connector_mgr is None:
        return connectors_info
    
    for connector in connector_mgr.Connectors:
        try:
            # Only physical connectors have Origin property
            # Check connector type to avoid exceptions Ignore logical connectors etc
            if connector.ConnectorType == ConnectorType.End or \
               connector.ConnectorType == ConnectorType.Physical:
                origin = connector.Origin
                connectors_info.append({
                    'connector': connector,
                    'origin': origin,
                    'is_connected': connector.IsConnected
                })
        except:
            # Skip connectors without Origin (logical connectors, etc.)
            continue
    
    return connectors_info

def get_connected_elements(valve):
    """Get elements directly connected to valve via connectors"""
    connected_elements = []
    connector_mgr = get_connector_manager(valve)
    
    if connector_mgr is None:
        return connected_elements
    
    for connector in connector_mgr.Connectors:
        if connector.IsConnected:
            connector_set = connector.AllRefs
            for ref_connector in connector_set:
                if ref_connector.Owner.Id != valve.Id:
                    connected_elements.append({
                        'element': ref_connector.Owner,
                        'connector': ref_connector,
                        'valve_connector': connector
                    })
    
    return connected_elements

def get_service_from_element(element):
    """Extract service name from an MEP fabrication element"""
    service_name = None
    
    try:
        # For Fabrication Parts
        if hasattr(element, 'ServiceName'):
            service_name = element.ServiceName
        
        # Try parameter lookup
        if service_name is None:
            service_param = element.LookupParameter("Fabrication Service")
            if service_param and service_param.HasValue:
                service_name = service_param.AsValueString() or service_param.AsString()
        
        # Try Service Type parameter
        if service_name is None:
            service_param = element.LookupParameter("Fabrication Service Name")
            if service_param and service_param.HasValue:
                service_name = service_param.AsValueString() or service_param.AsString()

        # Try Service Abbreviation property
        if service_name is None:
            if hasattr(element, 'ServiceAbbreviation'):
                service_name = element.ServiceAbbreviation
                
        # Try Service Abbreviation parameter
        if service_name is None:
            service_param = element.LookupParameter("Fabrication Service Abbreviation")
            if service_param and service_param.HasValue:
                service_name = service_param.AsValueString() or service_param.AsString()

    except:
        pass
    
    return service_name

def find_nearest_service_by_connectors(valve_connectors, all_mep_elements, tolerance):
    """
    Find nearest MEP service by comparing valve connector locations 
    to MEP element connector locations
    """
    nearest_matches = []
    
    for valve_conn_info in valve_connectors:
        # Skip connectors that are already connected
        if valve_conn_info['is_connected']:
            continue
        
        valve_conn_origin = valve_conn_info['origin']
        closest_service = None
        min_distance = float('inf')
        
        for mep_element in all_mep_elements:

            # Skip if same element as valve
            if mep_element.Id == valve_conn_info['connector'].Owner.Id: # Connector.Owner.Id returns valve ID if unconnected
                continue
            
            service = get_service_from_element(mep_element)
            if not service:
                continue
            
            # Get all connectors from this MEP element
            # COULD JUST GET ALL CONNECTORS AT START for all mep elems then would just have to subtract
            # this connector origin from all, sort, and take smallest
            mep_connectors = get_all_connectors(mep_element)
            
            for mep_conn_info in mep_connectors:
                mep_conn_origin = mep_conn_info['origin']
                distance = valve_conn_origin.DistanceTo(mep_conn_origin)
                
                # Check if this is the closest match within tolerance
                if distance <= tolerance and distance < min_distance:
                    min_distance = distance
                    closest_service = {
                        'service': service,
                        'element': mep_element,
                        'element_id': mep_element.Id.IntegerValue,
                        'distance': distance,
                        'valve_connector_origin': valve_conn_origin,
                        'mep_connector_origin': mep_conn_origin,
                        'mep_connector': mep_conn_info['connector'],
                        'valve_connector': valve_conn_info['connector']
                    }
        
        if closest_service:
            nearest_matches.append(closest_service)
    
    # Return the overall closest match if any found
    if nearest_matches:
        return min(nearest_matches, key=lambda x: x['distance'])

    return None

def find_nearest_service_by_centerline(valve_connectors, all_mep_elements, tolerance):
    """
    Fallback function: Find nearest MEP service by comparing valve connector 
    locations to MEP element centerlines/curves (for valves placed through pipes that have not been cut correctly)
    """
    nearest_matches = []

    for valve_conn_info in valve_connectors:
        # Skip connectors that are already connected
        if valve_conn_info['is_connected']:
            continue

        # Adjust tolerance based on valve radius (if available)
        max_valve_radius = valve_conn_info['connector'].Owner.LookupParameter("Maximum Size")
        if max_valve_radius and max_valve_radius.HasValue:
            tolerance = max_valve_radius.AsDouble() 
        
        valve_conn_origin = valve_conn_info['origin']
        closest_service = None
        min_distance = float('inf')
        
        for mep_element in all_mep_elements:
            # Skip if same element as valve
            if mep_element.Id == valve_conn_info['connector'].Owner.Id:
                continue
            
            service = get_service_from_element(mep_element)
            if not service:
                continue

            if not hasattr(mep_element, "Location") or not mep_element.Location:
                continue
            # Get the location curve/centerline of the MEP element
            location = mep_element.Location
            distance = None
            closest_point = None
            
            if isinstance(location, LocationCurve):
                # Get the curve (centerline of pipe/duct/conduit)
                curve = location.Curve
                
                # Project the valve connector point onto the curve
                # This finds the closest point on the curve to the valve connector
                try:
                    result = curve.Project(valve_conn_origin)
                    if result:
                        closest_point = result.XYZPoint
                        distance = valve_conn_origin.DistanceTo(closest_point)
                except:
                    # Could add in some more complex handling here if projection fails 
                    continue
                        
            elif isinstance(location, LocationPoint):
                # For point-based elements (equipment, etc.)
                point = location.Point
                distance = valve_conn_origin.DistanceTo(point)
                closest_point = point
            
            # Check if this is the closest match within tolerance
            if distance is not None and distance <= tolerance and distance < min_distance:
                min_distance = distance
                closest_service = {
                    'service': service,
                    'element': mep_element,
                    'element_id': mep_element.Id.IntegerValue,
                    'distance': distance,
                    'valve_connector_origin': valve_conn_origin,
                    'mep_connector_origin': closest_point,
                    'mep_connector': None,  # No specific connector in this case
                    'valve_connector': valve_conn_info['connector'],
                    'method_detail': 'centerline'
                }
        
        if closest_service:
            nearest_matches.append(closest_service)
    
    # Return the overall closest match if any found
    if nearest_matches:
        return min(nearest_matches, key=lambda x: x['distance'])
    
    return None

def get_all_mep_fabrication_elements():
    """Get all MEP fabrication elements in the model"""
    # Fabrication parts
    fab_parts = FilteredElementCollector(doc)\
        .OfClass(FabricationPart)\
        .WhereElementIsNotElementType()\
        .ToElements()
    
    # Filter to only pipework
    pipework = [f for f in fab_parts if f.Category and f.Category.Name == "MEP Fabrication Pipework"]

    return pipework

def process_valve(valve, all_mep_elements):
    """Process a single valve to determine its service using connector-based logic"""
    result = {
        'valve_id': valve.Id.IntegerValue,
        'valve_name': valve.Name,
        'service': None,
        'method': None,  # 'connected' or 'proximity'
        'distance': None,
        'source_element_id': None,
        'valve_connector_location': None,
        'mep_connector_location': None
    }
    
    # Get all valve connectors
    valve_connectors = get_all_connectors(valve)
    
    if not valve_connectors:
        result['method'] = 'no_connectors'
        return result

    # Step 1: If direct connections then use and return service of connected element 
    connected_elements = get_connected_elements(valve)
    
    for conn_info in connected_elements:
        service = get_service_from_element(conn_info['element'])
        if service:
            result['service'] = service
            result['method'] = 'connected'
            result['source_element_id'] = conn_info['element'].Id.IntegerValue
            result['distance'] = 0.0
            result['valve_connector_location'] = conn_info['valve_connector'].Origin
            result['mep_connector_location'] = conn_info['connector'].Origin
            return result
    
    # Step 2: If not connected, search by connector proximity
    nearest_service = find_nearest_service_by_connectors(
        valve_connectors, 
        all_mep_elements, 
        PROXIMITY_TOLERANCE
    )
    
    if nearest_service:
        result['service'] = nearest_service['service']
        result['method'] = 'proximity'
        result['distance'] = nearest_service['distance']
        result['source_element_id'] = nearest_service['element_id']
        result['valve_connector_location'] = nearest_service['valve_connector_origin']
        result['mep_connector_location'] = nearest_service['mep_connector_origin']
    else:
        result['method'] = 'not_found'

    # Step 3: If still not found, try centerline proximity (for valves placed through pipes)
    if not nearest_service:
        nearest_service = find_nearest_service_by_centerline(
            valve_connectors,
            all_mep_elements,
            PROXIMITY_TOLERANCE
        )
    
    if nearest_service:
        result['service'] = nearest_service['service']
        result['method'] = 'proximity_' + nearest_service.get('method_detail', 'unknown')
        result['distance'] = nearest_service['distance']
        result['source_element_id'] = nearest_service['element_id']
        result['valve_connector_location'] = nearest_service['valve_connector_origin']
        result['mep_connector_location'] = nearest_service['mep_connector_origin']
    else:
        result['method'] = 'not_found'
    
    return result

# Main execution
def main():
    # Get all valves in the model
    all_valves = []
    
    # Try different valve categories
    valve_categories = [
        BuiltInCategory.OST_PipeAccessory,
        BuiltInCategory.OST_MechanicalEquipment,
        BuiltInCategory.OST_PlumbingFixtures,
        BuiltInCategory.OST_PipeFitting
    ]
    
    for category in valve_categories:
        try:
            valves = FilteredElementCollector(doc)\
                .OfCategory(category)\
                .WhereElementIsNotElementType()\
                .ToElements()
            all_valves.extend(valves)
        except:
            continue
    
    # Filter to actual valves (adjust this filter based on your naming conventions)
    # valves = []
    # for v in all_valves:
    #     try:
    #         if 'valve' in v.Name.lower():
    #             valves.append(v)
    #         elif v.LookupParameter("Family"):
    #             family_name = v.LookupParameter("Family").AsValueString()
    #             if family_name and 'valve' in family_name.lower():
    #                 valves.append(v)
    #     except:
    #         continue

    selection_ids = uidoc.Selection.GetElementIds()
    valves = [doc.GetElement(id) for id in selection_ids]
    
    # Get all MEP elements
    print("Collecting MEP fabrication elements...")
    all_mep_elements = get_all_mep_fabrication_elements()
    print("Found {} MEP elements".format(len(all_mep_elements)))
    
    # Process each valve
    print("\nProcessing {} valves...".format(len(valves)))
    results = []
    for i, valve in enumerate(valves):
        if i % 10 == 0:
            print("  Processing valve {}/{}...".format(i+1, len(valves)))
        result = process_valve(valve, all_mep_elements)
        results.append(result)
    
    # Output results
    print("\n" + "="*60)
    print("VALVE SERVICE EXTRACTION RESULTS (Connector-Based)")
    print("="*60 + "\n")
    print("Total Valves Processed: {}".format(len(results)))
    
    connected_count = sum(1 for r in results if r['method'] == 'connected')
    proximity_count = sum(1 for r in results if r['method'] == 'proximity')
    unassigned_count = sum(1 for r in results if r['service'] is None)
    
    print("  Connected: {}".format(connected_count))
    print("  By Proximity: {}".format(proximity_count))
    print("  Unassigned: {}\n".format(unassigned_count))
    
    # Detailed output
    for result in results:
        print("Valve ID: {} | Name: {}".format(result['valve_id'], result['valve_name']))
        print("  Service: {}".format(result['service'] or 'UNASSIGNED'))
        print("  Method: {}".format(result['method']))
        if result['distance'] is not None:
            print("  Distance: {:.3f} mm".format(result['distance'] * 304.8))  # Convert to mm for display
        if result['valve_connector_location']:
            loc = result['valve_connector_location']
            print("  Valve Connector: ({:.2f}, {:.2f}, {:.2f})".format(loc.X, loc.Y, loc.Z))
        if result['mep_connector_location']:
            loc = result['mep_connector_location']
            print("  MEP Connector: ({:.2f}, {:.2f}, {:.2f})".format(loc.X, loc.Y, loc.Z))
        print()
    
    return results

# Run the script
if __name__ == '__main__':
    results = main()
    
    # Optional: Write results back to Revit parameters
    # You would need to create a shared parameter on valves called "Assigned Service"
    """
    TransactionManager.Instance.EnsureInTransaction(doc)
    
    for result in results:
        if result['service']:
            valve = doc.GetElement(ElementId(result['valve_id']))
            service_param = valve.LookupParameter("Assigned Service")
            if service_param and not service_param.IsReadOnly:
                service_param.Set(result['service'])
    
    TransactionManager.Instance.TransactionTaskDone()
    """