# Optimized MEP Fabrication Service Extraction for Valves
# Pre-computes all connector positions to avoid nested loops

from pyrevit import *
from Autodesk.Revit.DB import *

# Get current document
uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

# Configuration
Tolerance_mm = 50  # millimeters
PROXIMITY_TOLERANCE = Tolerance_mm / 304.8  # Convert to feet
touching_dist_mm = 5  # millimeters
TOUCHING_DIST_SQ = (touching_dist_mm / 304.8) ** 2  # Convert to feet

def get_connector_manager(element):
    """Get connector manager from an element"""
    try:
        if hasattr(element, 'ConnectorManager'):
            return element.ConnectorManager
        elif hasattr(element, 'MEPModel'):
            return element.MEPModel.ConnectorManager
    except:
        pass
    return None

def get_service_from_element(element):
    """Extract service name from an MEP fabrication element"""

    # Fast attribute lookups first (no Revit API calls)
    if hasattr(element, 'ServiceName') and element.ServiceName is not None:
        return element.ServiceName 

    try:
        service_param = element.LookupParameter("Fabrication Service")
        if service_param and service_param.HasValue:
            return service_param.AsValueString() or service_param.AsString()
    
        service_param = element.LookupParameter("Fabrication Service Name")
        if service_param and service_param.HasValue:
            return service_param.AsValueString() or service_param.AsString()

        if hasattr(element, 'ServiceAbbreviation') and element.ServiceAbbreviation is not None:
            return element.ServiceAbbreviation
            
        service_param = element.LookupParameter("Fabrication Service Abbreviation")
        if service_param and service_param.HasValue:
            return service_param.AsValueString() or service_param.AsString()
    except:
        pass
    
    return None

def build_mep_connector_cache(mep_elements):
    """
    Pre-build cache of all MEP connectors with their positions and services.
    Returns list of tuples: (origin_xyz, service, element_id, element, connector)
    """
    print("Building MEP connector cache...")
    connector_cache = []
    
    for elem in mep_elements:
            
        connector_mgr = get_connector_manager(elem)
        if connector_mgr is None:
            continue
        
        for connector in connector_mgr.Connectors:
            try:
                if connector.ConnectorType == ConnectorType.End or \
                   connector.ConnectorType == ConnectorType.Physical:
                    origin = connector.Origin
                    connector_cache.append({
                        'origin': origin,
                        'element_id': elem.Id.IntegerValue, 
                        'element': elem,
                        'connector': connector
                    })
            except:
                continue
    
    print("  Cached {} MEP connectors".format(len(connector_cache)))
    return connector_cache

def build_valve_connector_cache(valves):
    """
    Pre-build cache of valve connectors grouped by valve.
    Returns dict: {valve_id: [(connector, origin, is_connected), ...]}
    """
    print("Building valve connector cache...")
    valve_cache = {}
    
    for valve in valves:

        connector_mgr = get_connector_manager(valve)
        if connector_mgr is None:
            valve_cache[valve.Id.IntegerValue] = []
            continue
        
        valve_connectors = []
        for connector in connector_mgr.Connectors:
            try:
                if connector.ConnectorType == ConnectorType.End or \
                   connector.ConnectorType == ConnectorType.Physical:
                    origin = connector.Origin
                    is_connected = connector.IsConnected
                    valve_connectors.append({
                        'connector': connector,
                        'origin': origin,
                        'is_connected': is_connected
                    })
            except:
                continue
        
        valve_cache[valve.Id.IntegerValue] = valve_connectors
    
    print("  Cached connectors for {} valves".format(len(valve_cache)))
    return valve_cache

def get_connected_service(valve, valve_connectors):
    """Check if valve has any connected elements and return service"""
    # Loop through each valve connector
    for conn_info in valve_connectors:

        # Skip unconnected
        if not conn_info['is_connected']:
            continue
        
        connector = conn_info['connector']
        connector_set = connector.AllRefs
        
        for ref_connector in connector_set:
            if ref_connector.Owner.Id != valve.Id:
                service = get_service_from_element(ref_connector.Owner) 
                if service:
                    # If one connector is connected, return immediately
                    return {
                        'service': service,
                        'method': 'connected',
                        'distance': 0.0,
                        'element_id': ref_connector.Owner.Id.IntegerValue, # Element ID of connected MEP
                        'valve_connector_loc': conn_info['origin'],
                        'mep_connector_loc': ref_connector.Origin
                    }
    return None

def sq_distance(pt1, pt2):
    """
    Calculate squared distance between two XYZ points
    Returns float('inf') if any axis distance exceeds tolerance to avoid unnecessary calculations.
    """
    dx = pt1.X - pt2.X
    if abs(dx) > PROXIMITY_TOLERANCE:
        return float('inf')
    dy = pt1.Y - pt2.Y
    if abs(dy) > PROXIMITY_TOLERANCE:
        return float('inf')
    dz = pt1.Z - pt2.Z
    if abs(dz) > PROXIMITY_TOLERANCE:
        return float('inf')
    return dx*dx + dy*dy + dz*dz

def sq_distance_no_check(pt1, pt2):
    """Calculate squared distance between two XYZ points without any checks."""
    dx = pt1.X - pt2.X
    dy = pt1.Y - pt2.Y
    dz = pt1.Z - pt2.Z
    return dx*dx + dy*dy + dz*dz

def best_match_data(mep_elem, valve_conn, mep_conn_origin, distance_sq, method):
    """Helper to create best match data dict"""
    # Get element id safely
    elem_id = getattr(mep_elem.Id, "IntegerValue", None) if hasattr(mep_elem, "Id") else None
    return {
        'service': get_service_from_element(mep_elem),
        'element_id': elem_id,
        'valve_connector_loc': valve_conn['origin'],
        'mep_connector_loc': mep_conn_origin,
        'distance': distance_sq ** 0.5,
        'method': 'proximity_' + method
    }

def find_nearest_by_connectors(valve_connectors, mep_connector_cache, tolerance_sq, touching_dist_sq):
    """
    Find nearest service by comparing to cached MEP connectors.
    Uses squared distance to avoid expensive sqrt operations.
    """
    best_match_mep_conn = None
    best_match_valve_conn = None
    min_distance_sq = float('inf')
    
    # Loop through each valve connector and find overall closest MEP connector
    for valve_conn in valve_connectors:

        # Single pass through MEP connector cache
        for mep_conn in mep_connector_cache:

            # Calculate squared distance (avoid sqrt)
            distance_sq = sq_distance(valve_conn['origin'], mep_conn['origin'])

            # Track best match (no sqrt yet, just store data)
            if distance_sq < min_distance_sq:
                min_distance_sq, best_match_valve_conn, best_match_mep_conn = distance_sq, valve_conn, mep_conn

                # Early exit if essentially touching 
                if distance_sq < touching_dist_sq:
                    return best_match_data(mep_conn['element'], 
                                            valve_conn, mep_conn['origin'], distance_sq, 'connector')
            
    # Only compute actual distance for the best match
    if min_distance_sq < tolerance_sq:
        return best_match_data(best_match_mep_conn['element'], best_match_valve_conn, 
                                            best_match_mep_conn['origin'], min_distance_sq, 'connector')

    return None


def find_nearest_by_centerline(valve_connectors, mep_elements, tolerance_sq, touching_dist_sq):
    """
    Fallback: Find nearest service by projecting onto MEP element centerlines.
    Only called if connector search fails.
    """
    best_match_mep_elem = None
    best_match_valve_conn = None
    best_match_point = None
    min_distance_sq = float('inf')
    
    for valve_conn in valve_connectors:
        
        for mep_elem in mep_elements:
            
            # Check if element has location before accessing
            if not hasattr(mep_elem, "Location") or not mep_elem.Location:
                continue
            location = mep_elem.Location
            
            if isinstance(location, LocationCurve):
                # Get the curve (centerline of pipe/duct/conduit)
                curve = location.Curve

                # Project the valve connector point onto the curve
                try:
                    # Cheaper check to skip if too far from curve endpoints (with tolerance) before calling Project
                    if sq_distance_no_check(valve_conn['origin'], curve.Origin) > ((curve.Length/2) * 1.5)**2:
                        continue
                    # This finds the closest point on the curve to the valve connector
                    result = curve.Project(valve_conn['origin'])
                    if result and hasattr(result, "XYZPoint"):
                        closest_point = result.XYZPoint
                        distance_sq = sq_distance(valve_conn['origin'], closest_point)
                        
                        if distance_sq < min_distance_sq:
                            min_distance_sq, best_match_valve_conn, best_match_mep_elem, best_match_point = distance_sq, valve_conn, mep_elem, closest_point

                            # Early exit if essentially touching 
                            if distance_sq < touching_dist_sq:
                                return best_match_data(mep_elem, valve_conn, 
                                                        closest_point, distance_sq, 'centerline')

                except:
                    # Could add in some more complex handling here if projection fails 
                    continue

            # For point-based elements (equipment, etc.)
            elif isinstance(location, LocationPoint):
                point = location.Point
                distance_sq = sq_distance(valve_conn['origin'], point)
                
                if distance_sq < min_distance_sq:
                    min_distance_sq, best_match_valve_conn, best_match_mep_elem, best_match_point = distance_sq, valve_conn, mep_elem, point

                    # Early exit if essentially touching 
                    if distance_sq < touching_dist_sq:
                        return best_match_data(mep_elem, valve_conn, 
                                                point, distance_sq, 'centerline')


    if min_distance_sq < tolerance_sq:
        return best_match_data(best_match_mep_elem, best_match_valve_conn, 
                                            best_match_point, min_distance_sq, 'centerline')
    
    return None

def process_all_valves(valves, valve_cache, mep_connector_cache, mep_elements, tolerance, touching_dist_sq):
    """
    Single loop through all valves with hierarchical search:
    1. Check connected
    2. Check proximity to connectors
    3. Check proximity to centerlines
    """
    print("\nProcessing valves...")
    results = []

    # Pre-compute squared tolerance for distance comparisons
    tolerance_sq = tolerance * tolerance
    
    step = max(1, len(valves) // 10)  # ~10% intervals
    for i, valve in enumerate(valves):
        if i % step == 0 and i > 0:
            print("  Processed {}/{}...".format(i, len(valves)))
        
        valve_id = valve.Id.IntegerValue
        valve_connectors = valve_cache.get(valve_id, [])
        
        result = {
            'valve_id': valve_id,
            'valve_name': valve.Name,
            'service': None,
            'method': 'no_connectors',
            'distance': None,
            'source_element_id': None,
            'valve_connector_location': None,
            'mep_connector_location': None
        }
        
        if not valve_connectors:
            results.append(result)
            continue
        
        # Step 1: Check if connected
        connected = get_connected_service(valve, valve_connectors)
        if connected:
            result.update(connected)
            result['valve_connector_location'] = connected['valve_connector_loc']
            result['mep_connector_location'] = connected['mep_connector_loc']
            results.append(result)
            continue
        
        # Step 2: Check connector proximity
        nearest = find_nearest_by_connectors(valve_connectors, mep_connector_cache, tolerance_sq, touching_dist_sq)
        if nearest:
            result.update(nearest)
            result['valve_connector_location'] = nearest['valve_connector_loc']
            result['mep_connector_location'] = nearest['mep_connector_loc']
            results.append(result)
            continue
        
        # Step 3: Check centerline proximity (fallback)
        nearest = find_nearest_by_centerline(valve_connectors, mep_elements, tolerance_sq, touching_dist_sq)
        if nearest:
            result.update(nearest)
            result['valve_connector_location'] = nearest['valve_connector_loc']
            result['mep_connector_location'] = nearest['mep_connector_loc']
        else:
            result['method'] = 'not_found'
        
        results.append(result)
    
    return results

def get_all_mep_fabrication_elements():
    """Get all MEP fabrication elements in the model"""
    fab_parts = FilteredElementCollector(doc)\
        .OfClass(FabricationPart)\
        .WhereElementIsNotElementType()\
        .ToElements()
    
    pipework = [f for f in fab_parts if f.Category and f.Category.Name == "MEP Fabrication Pipework"]
    return pipework

def debug_output(results, show_details=True):
    """Print summary and detailed results."""
    lines = []
    add = lines.append  # local ref for speed

    add("\n" + "=" * 60)
    add("RESULTS")
    add("=" * 60)
    add("Total Valves: {}".format(len(results)))

    connected = sum(1 for r in results if r['method'] == 'connected')
    proximity_conn = sum(1 for r in results if r['method'] == 'proximity_connector')
    proximity_center = sum(1 for r in results if r['method'] == 'proximity_centerline')
    not_found = sum(1 for r in results if r['method'] == 'not_found')

    add("  Connected: {}".format(connected))
    add("  Proximity (Connector): {}".format(proximity_conn))
    add("  Proximity (Centerline): {}".format(proximity_center))
    add("  Not Found: {}\n".format(not_found))

    if show_details:
        for result in results:
            add("Valve: {} [ID: {}]".format(result['valve_name'], result['valve_id']))
            add("  Service: {}".format(result['service'] or 'UNASSIGNED'))
            add("  Method: {}".format(result['method']))
            if result['distance'] is not None:
                add("  Distance: {:.3f} mm".format(result['distance'] * 304.8))
            add("")  

    print("\n".join(lines))


def main():
    # Get all valves
    print("="*60)
    print("VALVE SERVICE EXTRACTION")
    print("="*60)
    
    all_valves = []
    valve_categories = [
        BuiltInCategory.OST_PipeAccessory,
        # BuiltInCategory.OST_MechanicalEquipment,
        # BuiltInCategory.OST_PlumbingFixtures,
        # BuiltInCategory.OST_PipeFitting
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

    valves = []
    for v in all_valves:
        try:
            if 'valve' in v.Name.lower():
                valves.append(v)
            elif v.LookupParameter("Family"):
                family_name = v.LookupParameter("Family").AsValueString()
                if family_name and 'valve' in family_name.lower():
                    valves.append(v)
        except:
            continue
    
    # Use selection if available
    selection_ids = uidoc.Selection.GetElementIds()
    if selection_ids:
        valves = [doc.GetElement(id) for id in selection_ids]
        print("\nProcessing {} selected valves".format(len(valves)))
    else:
        print("\nProcessing {} valves from model".format(len(valves)))
    
    # Get MEP elements
    print("\nCollecting MEP fabrication elements...")
    mep_elements = get_all_mep_fabrication_elements()
    print("Found {} MEP elements".format(len(mep_elements)))
    
    # Pre-build caches (one-time cost)
    mep_connector_cache = build_mep_connector_cache(mep_elements)
    valve_cache = build_valve_connector_cache(valves)
    
    # Process all valves in single loop
    results = process_all_valves(valves, valve_cache, mep_connector_cache, 
                                   mep_elements, PROXIMITY_TOLERANCE, TOUCHING_DIST_SQ)
    
    # Output summary
    debug_output(results, show_details=True)
    
    # return results

if __name__ == '__main__':
    results = main()



# Excess metadata includes XYZ location of valve and MEP connector 