from Autodesk.Revit.DB import View

class SelectionContext:
    """
    Resolves user selection with clear priority and exposes convenient accessors.
    Priority order:
      1. Selected views
      2. Selected elements
      3. Fallback to active view
    """

    # Constants for resolved type
    SELECTED_VIEWS = "selected_views"
    SELECTED_ELEMENTS = "selected_elements"
    ACTIVE_VIEW = "active_view"

    def __init__(self, doc, uidoc):
        self.doc = doc
        self.uidoc = uidoc

        # Fetch selection once
        sel_ids = list(self.uidoc.Selection.GetElementIds())

        # Split into views vs elements
        self._selected_views = []
        self._selected_elements = []
        for eid in sel_ids:
            elem = doc.GetElement(eid)
            if isinstance(elem, View):
                self._selected_views.append(elem)
            else:
                self._selected_elements.append(elem)

        # Determine resolved selection type
        if self._selected_views:
            self._resolved_type = self.SELECTED_VIEWS
        elif self._selected_elements:
            self._resolved_type = self.SELECTED_ELEMENTS
        else:
            self._resolved_type = self.ACTIVE_VIEW

    # --- Properties for convenience ---
    @property
    def selected_views(self):
        return self._selected_views

    @property
    def selected_elements(self):
        return self._selected_elements

    @property
    def active_view(self):
        return self.uidoc.ActiveView

    @property
    def resolved_type(self):
        """Returns the resolved type constant."""
        return self._resolved_type

    @property
    def resolved_targets(self):
        """Return the objects corresponding to the resolved selection type."""
        if self._resolved_type == self.SELECTED_VIEWS:
            return self._selected_views
        elif self._resolved_type == self.SELECTED_ELEMENTS:
            return self._selected_elements
        else:
            return [self.active_view]

    # --- Boolean helpers for cleaner tool scripts ---
    @property
    def has_selected_views(self):
        return self._resolved_type == self.SELECTED_VIEWS

    @property
    def has_selected_elements(self):
        return self._resolved_type == self.SELECTED_ELEMENTS

    @property
    def has_active_view(self):
        return self._resolved_type == self.ACTIVE_VIEW
