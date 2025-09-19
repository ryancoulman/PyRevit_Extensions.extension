# -*- coding: utf-8 -*-
# pyRevit config script: set default text style (Shift+Click)

from pyrevit import revit, forms
from TagConverterLogic import TextStyle   # shared class with JSON handling

doc = revit.doc

# Init TextStyle manager
ts = TextStyle(doc, setting_default=True)

# Force user to pick a style (ignores any saved defaults)
selected_style = ts.select_style()

if selected_style:
    # Ask user whether they want to be asked each time
    ask = forms.alert(
        "Default text style set to:\n\n{}\n\nWould you like to be asked each time?".format(
            selected_style.LookupParameter("Type Name").AsString()
        ),
        title="Text Style Saved",
        options=["Yes, ask each time", "No, use this as default"],
    )

    if ask == "Yes, ask each time":
        ts.set_default_text_style(selected_style.Id, ask_every_time=True)
    else:
        ts.set_default_text_style(selected_style.Id, ask_every_time=False)

else:
    forms.alert("No text style was selected. Default not set.", title="Cancelled")
