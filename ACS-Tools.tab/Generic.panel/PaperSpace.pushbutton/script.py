# Import necessary Revit API modules
from pyrevit import revit, DB, forms
from Autodesk.Revit.UI import RevitCommandId, PostableCommand

__title__ = "Paper\nSpace"
__doc__ = ' Description: Convert from model view to sheet view. Similar to AutoCads paperspace button.'

# Access the active document and active view
doc = revit.doc
uidoc = revit.uidoc
uiapp = __revit__  # Get the application context from pyRevit
active_view = doc.ActiveView

# Check if the active view is not a sheet view (i.e., you're inside a viewport)
if not isinstance(active_view, DB.ViewSheet):
    # Find the viewport that contains the active view
    viewports = DB.FilteredElementCollector(doc).OfClass(DB.Viewport).ToElements()

    for viewport in viewports:
        if viewport.ViewId == active_view.Id:
            # Get the sheet that contains this viewport
            sheet = doc.GetElement(viewport.SheetId)
            
            # Now trigger the 'Deactivate View' command to return to the sheet view
            uiapp.PostCommand(RevitCommandId.LookupPostableCommandId(PostableCommand.DeactivateView))
            break
else:
    forms.alert('Already in Sheet View!')
