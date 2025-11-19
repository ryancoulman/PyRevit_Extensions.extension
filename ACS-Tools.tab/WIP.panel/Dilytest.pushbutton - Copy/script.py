# -*- coding: utf-8 -*-

import clr
import os
import time 

dll_path = os.path.join(os.path.dirname(__file__), "ValveGetterQ.dll")
clr.AddReferenceToFileAndPath(dll_path)
from ValveGetter import ValveServiceExtractor

def debug_output(results, elapsed_time, show_details=True):
    """Print summary and detailed results."""
    lines = []
    add = lines.append  # local ref for speed

    add("\n" + "=" * 60)
    add("RESULTS OVERVIEW")
    add("=" * 60 + "\n")
    add("Total Valves: {}".format(len(results)))
    add("Elapsed Time: {:.3f} seconds".format(elapsed_time))

    # Use property access instead of dictionary access
    connected = proximity_conn = proximity_center = not_found = no_connectors = 0
    not_found_ids = []

    for r in results:
        method = r.Method
        if method == 'connected':
            connected += 1
        elif method == 'proximity_connector':
            proximity_conn += 1
        elif method == 'proximity_centerline':
            proximity_center += 1
        elif method == 'no_connectors':
            no_connectors += 1
        elif method == 'not_found': # Connectors but no MEP element found
            not_found += 1
            not_found_ids.append(str(r.ValveId))


    add("  Connected: {}".format(connected))
    add("  Proximity (Connector): {}".format(proximity_conn))
    add("  Proximity (Centerline): {}".format(proximity_center))
    add("  Unassigned Accessories with no Connectors: {}".format(no_connectors))
    add("  Accessories with Connectors but no MEP Element Founds: {}".format(not_found))
    add("  Total Accessories in Categories: {}\n".format(connected + proximity_conn + proximity_center + no_connectors + not_found))

    if not_found_ids:
        add("    Accessory IDs of Connectors with no MEP Element Found:\n {} \n{}".format("-" * 55, "\n".join(not_found_ids)))

    if show_details:
        add("\n" + "=" * 60)
        add("RESULTS DETAILED")
        add("=" * 60 + "\n")
        for r in results:
            add("Valve: {} [ID: {}]".format(r.ValveName, r.ValveId))
            add("  Connected MEP Element ID: {}".format(r.SourceElementId if r.SourceElementId else 'N/A'))
            add("  Service: {}".format(r.Service or 'UNASSIGNED'))
            add("  Method: {}".format(r.Method))
            add("  Valve Connector Origin: {}".format(r.ValveConnectorLocation if r.ValveConnectorLocation else 'N/A'))
            add("  MEP Connector Origin: {}".format(r.MEPConnectorLocation if r.MEPConnectorLocation else 'N/A'))
            add("  Distance: {:.3f} mm".format(r.DistanceMm))
            add("")

    print("\n".join(lines))


uidoc = __revit__.ActiveUIDocument

if __name__ == "__main__":

    start_time = time.time()

    # Wrap C# call in a Revit transaction as cannot initiate transactions from C#
    results = ValveServiceExtractor.ExtractValveServices(
        uidoc,
        writeToParameters=False, 
        toleranceMm=50.0,
        touchingDistMm=5.0
    )

    end_time = time.time()

    # Process results in Python
    debug_output(results, end_time - start_time, show_details=True)