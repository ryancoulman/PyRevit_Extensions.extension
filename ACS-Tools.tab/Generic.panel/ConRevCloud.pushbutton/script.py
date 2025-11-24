# -*- coding: utf-8 -*-
# pyRevit script: Convert selected Revision Clouds to Detail Lines (modular, multiple clouds)



# // BIN this off and instead just provide a tool that elects all rev clouds on sheet (and in views) selected in proect browser
# oe open in view. then user can jsut change to current rev 



from Autodesk.Revit.DB import (
    Transaction,
    RevisionCloud,
    Options,
)
from pyrevit import revit, forms

doc = revit.doc
uidoc = revit.uidoc
view = doc.ActiveView

# Options for geometry extraction
opt = Options()
opt.ComputeReferences = False
opt.IncludeNonVisibleObjects = False


def get_selected_revision_clouds():
    """Return all selected RevisionCloud elements."""
    selection = [doc.GetElement(id) for id in uidoc.Selection.GetElementIds()]
    return [el for el in selection if isinstance(el, RevisionCloud)]


def convert_revcloud_to_detail_lines(revcloud, view):
    """
    Convert a single RevisionCloud into detail lines using its geometry arcs.
    Returns list of created DetailCurve element ids.
    """

    geo_elem = revcloud.get_Geometry(opt)
    for gobj in geo_elem:
        if hasattr(gobj, "GetEndPoint"):
            dc = doc.Create.NewDetailCurve(view, gobj)

    # Delete original revision cloud
    doc.Delete(revcloud.Id)



def main():
    revclouds = get_selected_revision_clouds()
    if not revclouds:
        forms.alert("No Revision Clouds selected.", exitscript=True)

    t = Transaction(doc, "Convert Revision Clouds to Detail Lines")
    t.Start()

    for rc in revclouds:
        convert_revcloud_to_detail_lines(rc, view)

    t.Commit()

    forms.alert("Converted {} Revision Clouds to detail lines.".format(len(revclouds)))


if __name__ == "__main__":
    main()
