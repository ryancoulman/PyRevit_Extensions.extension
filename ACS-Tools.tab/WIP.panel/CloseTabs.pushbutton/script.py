"""Close all open views except the current active view"""
from pyrevit import revit

uidoc = revit.uidoc

# Get all open UI views
uiviews = uidoc.GetOpenUIViews()

# Find the active view
active_view_id = uidoc.ActiveView.Id

# Close all views except the active one
for uiview in uiviews:
    if uiview.ViewId != active_view_id:
        uiview.Close()
