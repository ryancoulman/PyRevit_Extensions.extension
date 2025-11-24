# -*- coding: utf-8 -*-
"""Straighten Tag Leaders
Makes tag leaders orthogonal (horizontal or vertical)
"""
__title__ = "Straighten\nLeaders"
__author__ = "Your Name"

from Autodesk.Revit.DB import *
from pyrevit import revit, DB, forms

doc = revit.doc
uidoc = revit.uidoc

def straighten_leader(tag):
    """Make a tag's leader orthogonal for each tagged reference"""
    if not tag.HasLeader:
        return False
    
    # Get all tagged references
    references = tag.GetTaggedReferences()
    
    if not references or len(references) == 0:
        return False
    
    modified = False
    
    for ref in references:
        try:
            # Get leader end point (at the tag head)
            tag.LeaderEndCondition = LeaderEndCondition.Free
            leader_end = tag.GetLeaderEnd(ref)
            tag.LeaderEndCondition = LeaderEndCondition.Attached
            leader_x_pos = leader_end.X

            tag_text_y_pos = tag.TagHeadPosition.Y

            dummy_z = leader_end.Z  # Keep original Z coordinate
            
            new_elbow = XYZ(leader_x_pos, tag_text_y_pos, dummy_z)

            tag.SetLeaderElbow(ref, new_elbow)
            modified = True
            
        except Exception as e:
            print("Error processing reference for tag {}: {}".format(tag.Id, str(e)))
            continue
    
    return modified

# Get current selection
selection = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds()]

if not selection:
    forms.alert("Please select tags with leaders first.", exitscript=True)

# Filter for tags only
tags = [el for el in selection if isinstance(el, IndependentTag)]

if not tags:
    forms.alert("No tags found in selection.", exitscript=True)

# Process tags
t = Transaction(doc, "Straighten Tag Leaders")
t.Start()

count = 0
for tag in tags:
    try:
        if straighten_leader(tag):
            count += 1
    except Exception as e:
        print("Error processing tag {}: {}".format(tag.Id, str(e)))

t.Commit()

# Report results
if count > 0:
    forms.alert("{} tag leader(s) straightened.".format(count))
else:
    forms.alert("No tag leaders were modified.")