from Autodesk.Revit.DB import *
from Autodesk.Revit.UI.Selection import ObjectType
from pyrevit import revit, DB, forms

__title__ = "Set\nTriangles"
__doc__ = "Draw triangles indicating set flow direction for selected MEP fabrication parts."

doc = revit.doc
uidoc = revit.uidoc
active_view = doc.ActiveView


def get_element_width(element):
    """Get the width/diameter of the MEP element."""
    # Try to get connector diameter/width
    conn_mgr = element.ConnectorManager
    if conn_mgr:
        connectors = conn_mgr.Connectors
        for conn in connectors:
            if conn.Shape == ConnectorProfileType.Round:
                return conn.Radius * 2
            elif conn.Shape == ConnectorProfileType.Rectangular:
                return conn.Width
    
    # Fallback: try to get from parameters
    width_param = element.LookupParameter("Width")
    if width_param:
        return width_param.AsDouble()
    
    diameter_param = element.LookupParameter("Diameter")
    if diameter_param:
        return diameter_param.AsDouble()
    
    # Default fallback
    return 1.0  # 1 foot default


def get_element_endpoints_and_direction(element):
    """Get start and end points of the element and determine flow direction."""
    conn_mgr = element.ConnectorManager
    if not conn_mgr:
        return None, None
    
    connectors = list(conn_mgr.Connectors)
    if len(connectors) < 2:
        return None, None
    
    # Get the two main connectors
    conn1 = connectors[0]
    conn2 = connectors[1]
    
    point1 = conn1.Origin
    point2 = conn2.Origin
        
    # Determine which point is higher
    if point1.Z > point2.Z:
        high_point = point1
        low_point = point2
    else:
        high_point = point2
        low_point = point1
        
    return high_point, low_point
    

def project_point_to_view(point, view):
    """Project a 3D point onto the view's sketch plane."""
    # Get or create a sketch plane for the view
    sketch_plane = view.SketchPlane
    if sketch_plane:
        plane = sketch_plane.GetPlane()
    else:
        # Create a plane from the view's properties
        view_direction = view.ViewDirection
        view_origin = view.Origin
        plane = Plane.CreateByNormalAndOrigin(view_direction, view_origin)
    
    # Project the point onto the plane
    # Calculate the projection manually
    point_vector = point - plane.Origin
    distance = point_vector.DotProduct(plane.Normal)
    projected = point - (plane.Normal * distance)
    
    return projected


def draw_triangle(view, start_point, end_point, width):
    """Draw a triangle from start to end with base width at start."""
    # Project points to view plane
    start_2d = project_point_to_view(start_point, view)
    end_2d = project_point_to_view(end_point, view)
    
    # Calculate the perpendicular direction for the base
    direction = (end_2d - start_2d).Normalize()
    
    # Get perpendicular vector in the view plane
    # Use cross product with view direction to get perpendicular
    view_normal = view.ViewDirection
    perp = view_normal.CrossProduct(direction).Normalize()
    
    half_width = width / 2.0
    
    # Create the three points of the triangle (all in view plane)
    # Base spans the width at the start point
    base_left = start_2d + perp * half_width
    base_right = start_2d - perp * half_width
    # Apex at the centerline at the end point
    apex = end_2d
    
    # Create detail lines
    lines = []
    
    # Line 1: left base to apex
    line1 = Line.CreateBound(base_left, apex)
    lines.append(doc.Create.NewDetailCurve(view, line1))
    
    # Line 2: apex to right base
    line2 = Line.CreateBound(apex, base_right)
    lines.append(doc.Create.NewDetailCurve(view, line2))
    
    # Line 3: right base to left base (closing the triangle)
    line3 = Line.CreateBound(base_right, base_left)
    lines.append(doc.Create.NewDetailCurve(view, line3))
    
    return lines


if __name__ == "__main__":

    try:
        # Get user selection
        selection = uidoc.Selection.GetElementIds()
        
        if not selection:
            forms.alert("Please select MEP fabrication parts first.", exitscript=True)
        
        elements = [doc.GetElement(elem_id) for elem_id in selection]
        
        # Filter for MEP fabrication parts
        mep_elements = [elem for elem in elements if hasattr(elem, 'ConnectorManager')]
        
        if not mep_elements:
            forms.alert("No valid MEP fabrication parts found in selection.", exitscript=True)
        
        # Start transaction
        with revit.Transaction("Draw Set Triangles"):
            triangles_created = 0
            
            for element in mep_elements:
                # Get element geometry information
                high_point, low_point = get_element_endpoints_and_direction(element)
                
                if not high_point or not low_point:
                    print("Could not get endpoints for element ID: {}".format(element.Id))
                    continue
                
                width = get_element_width(element)
                
                # Draw triangle pointing from high to low
                draw_triangle(active_view, high_point, low_point, width)
                triangles_created += 1
            
            print("Created {} set direction triangles.".format(triangles_created))

    except Exception as e:
        forms.alert("Error: {}".format(str(e)))