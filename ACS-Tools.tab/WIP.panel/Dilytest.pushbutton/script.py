# -*- coding: utf-8 -*-

import clr
import os
from pyrevit import revit
from Autodesk.Revit import DB
from System.Collections.Generic import List
import time 

dll_path = os.path.join(os.path.dirname(__file__), "ValveGetter.dll")
clr.AddReferenceToFileAndPath(dll_path)
from ValveGetter import ValveServiceExtractor

def debug_output(results, elapsed_time, show_details=True):
    """Print summary and detailed results."""
    lines = []
    add = lines.append  # local ref for speed

    add("\n" + "=" * 60)
    add("RESULTS")
    add("=" * 60)
    add("Total Valves: {}".format(len(results)))
    add("Elapsed Time: {:.3f} seconds".format(elapsed_time))

    # Use property access instead of dictionary access
    connected = sum(1 for r in results if r.Method == 'connected')
    proximity_conn = sum(1 for r in results if r.Method == 'proximity_connector')
    proximity_center = sum(1 for r in results if r.Method == 'proximity_centerline')
    not_found = sum(1 for r in results if r.Method == 'not_found')

    add("  Connected: {}".format(connected))
    add("  Proximity (Connector): {}".format(proximity_conn))
    add("  Proximity (Centerline): {}".format(proximity_center))
    add("  Not Found: {}\n".format(not_found))

    if show_details:
        for r in results:
            add("Valve: {} [ID: {}]".format(r.ValveName, r.ValveId))
            add("  Service: {}".format(r.Service or 'UNASSIGNED'))
            add("  Method: {}".format(r.Method))
            if r.DistanceMm and r.DistanceMm > 0:
                add("  Distance: {:.3f} mm".format(r.DistanceMm))
            add("")

    print("\n".join(lines))



# Get document
doc = revit.doc
uidoc = revit.uidoc

if __name__ == "__main__":
    start_time = time.time()
    # Get selected valves (or None for all)
    selection = list(uidoc.Selection.GetElementIds())

    # Call C# method
    results = ValveServiceExtractor.ExtractValveServices(
        doc, 
        List[DB.ElementId](selection) if selection else None,
        toleranceMm=50.0,
        touchingDistMm=5.0
    )
    end_time = time.time()

    # Process results in Python
    debug_output(results, end_time - start_time, show_details=True)