import Autodesk.Revit.DB as DB
from pyrevit import forms 
import clr
clr.AddReference("System.Collections")
from System.Collections.Generic import List

uidoc = __revit__.ActiveUIDocument
doc = uidoc.Document

cats = [DB.BuiltInCategory.OST_FabricationContainment, 
        DB.BuiltInCategory.OST_FabricationDuctwork, 
        DB.BuiltInCategory.OST_FabricationPipework]
multicatfilter = DB.ElementMulticategoryFilter(List[DB.BuiltInCategory](cats))
elems = DB.FilteredElementCollector(doc).WhereElementIsNotElementType().OfClass(DB.FabricationPart).ToElementIds()
# select all elms in revit model 

# uidoc.Selection.SetElementIds(elems)
print("have slected {} elements".format(len(elems)))