# -*- coding: utf-8 -*-
"""Element Visibility Diagnostic Tool
Analyses why a selected element is not visible in the current view.
"""
__title__ = "Why Element\nHidden?"
__doc__ = "Diagnoses visibility issues for selected elements in the current view." \
"\nChecks category, workset, phase, filters, view range, design options, crop region, and temporary hide/isolate." \
"\n\nSelect the element and open the view where visibility is an issue before running."

from pyrevit import revit, DB, forms
from pyrevit import script

# Get logger and output
logger = script.get_logger()
output = script.get_output()


class VisibilityDiagnostic:
    """Main diagnostic class for element visibility analysis."""
    
    def __init__(self, element, view):
        """Initialize diagnostic with element and view.
        
        Args:
            element: Revit element to diagnose
            view: Active view to check visibility in
        """
        self.element = element
        self.view = view
        self.doc = element.Document
        self.issues = []
        self.info = []
        
    def run_diagnostics(self):
        """Run all diagnostic checks."""
        self._check_element_hidden()
        self._check_category_visibility()
        self._check_workset_visibility()
        self._check_phase_visibility()
        self._check_view_filters()
        self._check_view_range()
        self._check_design_options()
        self._check_crop_region()
        self._check_temporary_hide()
        
        return self.issues, self.info
    
    def _check_element_hidden(self):
        """Check if element is explicitly hidden in view."""
        try:
            if self.element.IsHidden(self.view):
                self.issues.append("Element is explicitly HIDDEN in this view")
        except Exception as e:
            logger.debug("Error checking element hidden status: {}".format(e))
    
    def _check_category_visibility(self):
        """Check category visibility settings."""
        try:
            category = self.element.Category
            if not category:
                self.info.append("Element has no category")
                return
            
            # Check if category is visible in view
            if not category.get_Visible(self.view):
                self.issues.append(
                    "Category '{}' is turned OFF in view".format(category.Name)
                )
            else:
                self.info.append(
                    "Category '{}' is visible in view".format(category.Name)
                )
            
            # Check subcategory if exists
            if hasattr(self.element, 'Subcategory') and self.element.Subcategory:
                subcat = self.element.Subcategory
                if not subcat.get_Visible(self.view):
                    self.issues.append(
                        "Subcategory '{}' is turned OFF in view".format(subcat.Name)
                    )
        except Exception as e:
            logger.debug("Error checking category visibility: {}".format(e))
    
    def _check_workset_visibility(self):
        """Check workset visibility if document is workshared."""
        try:
            if not self.doc.IsWorkshared:
                self.info.append("Document is not workshared")
                return
            
            workset_param = self.element.get_Parameter(
                DB.BuiltInParameter.ELEM_PARTITION_PARAM
            )
            
            if not workset_param:
                return
            
            workset_id = workset_param.AsInteger()
            if workset_id == -1:
                return
            
            workset = self.doc.GetWorksetTable().GetWorkset(
                DB.WorksetId(workset_id)
            )
            
            workset_name = workset.Name
            
            # Check workset visibility in view
            workset_visibility = self.view.GetWorksetVisibility(
                DB.WorksetId(workset_id)
            )
            
            if workset_visibility == DB.WorksetVisibility.Hidden:
                self.issues.append(
                    "Workset '{}' is HIDDEN in this view".format(workset_name)
                )
            else:
                self.info.append(
                    "Workset '{}' is visible in view".format(workset_name)
                )
        except Exception as e:
            logger.debug("Error checking workset visibility: {}".format(e))
    
    def _check_phase_visibility(self):
        """Check phase visibility settings."""
        try:
            # Get element phase
            phase_created_param = self.element.get_Parameter(
                DB.BuiltInParameter.PHASE_CREATED
            )
            phase_demolished_param = self.element.get_Parameter(
                DB.BuiltInParameter.PHASE_DEMOLISHED
            )
            
            if not phase_created_param:
                return
            
            phase_created_id = phase_created_param.AsElementId()
            phase_demolished_id = None
            
            if phase_demolished_param:
                phase_demolished_id = phase_demolished_param.AsElementId()
            
            # Get view phase
            view_phase_param = self.view.get_Parameter(
                DB.BuiltInParameter.VIEW_PHASE
            )
            
            if not view_phase_param:
                return
            
            view_phase_id = view_phase_param.AsElementId()
            
            # Get phase names
            phase_created = self.doc.GetElement(phase_created_id)
            view_phase = self.doc.GetElement(view_phase_id)
            
            if not phase_created or not view_phase:
                return
            
            phase_created_name = phase_created.Name
            view_phase_name = view_phase.Name
            
            # Check if element exists in view phase
            if phase_demolished_id and phase_demolished_id != DB.ElementId.InvalidElementId:
                phase_demolished = self.doc.GetElement(phase_demolished_id)
                
                # Compare phase orders
                if self._get_phase_order(phase_demolished_id) <= self._get_phase_order(view_phase_id):
                    self.issues.append(
                        "Element demolished in '{}' phase, before view phase '{}'".format(
                            phase_demolished.Name, view_phase_name
                        )
                    )
                    return
            
            if self._get_phase_order(phase_created_id) > self._get_phase_order(view_phase_id):
                self.issues.append(
                    "Element created in '{}' phase, after view phase '{}'".format(
                        phase_created_name, view_phase_name
                    )
                )
            else:
                self.info.append(
                    "Element exists in view phase '{}'".format(view_phase_name)
                )
        except Exception as e:
            logger.debug("Error checking phase visibility: {}".format(e))
    
    def _get_phase_order(self, phase_id):
        """Get phase order number."""
        try:
            phase = self.doc.GetElement(phase_id)
            if phase:
                return self.doc.Phases.IndexOf(phase)
            return -1
        except:
            return -1
    
    def _check_view_filters(self):
        """Check if any view filters hide the element."""
        try:
            filters = self.view.GetFilters()
            
            if not filters:
                self.info.append("No view filters applied")
                return
            
            hidden_by_filters = []
            
            for filter_id in filters:
                filter_elem = self.doc.GetElement(filter_id)
                if not filter_elem:
                    continue
                
                # Check if filter visibility is off
                visibility = self.view.GetFilterVisibility(filter_id)
                if not visibility:
                    # Check if element passes filter
                    if self._element_passes_filter(filter_elem):
                        hidden_by_filters.append(filter_elem.Name)
            
            if hidden_by_filters:
                self.issues.append(
                    "Hidden by view filter(s): {}".format(
                        ", ".join(hidden_by_filters)
                    )
                )
            else:
                self.info.append("Not hidden by any view filters")
        except Exception as e:
            logger.debug("Error checking view filters: {}".format(e))
    
    def _element_passes_filter(self, filter_elem):
        """Check if element passes a filter's criteria."""
        try:
            # Get filter rules
            param_filter = filter_elem.GetElementFilter()
            if not param_filter:
                return False
            
            # Try to evaluate if element passes filter
            # This is a simplified check - full filter evaluation is complex
            category = self.element.Category
            if not category:
                return False
            
            filter_cats = filter_elem.GetCategories()
            if category.Id in filter_cats:
                return True
            
            return False
        except:
            return False
    
    def _check_view_range(self):
        """Check if element is outside view range."""
        try:
            # Only applicable to plan views
            if not isinstance(self.view, DB.ViewPlan):
                return
            
            view_range = self.view.GetViewRange()
            if not view_range:
                return
            
            # Get element location
            location = self._get_element_elevation()
            if location is None:
                return
            
            # Get view range levels
            top_level_id = view_range.GetLevelId(DB.PlanViewPlane.TopClipPlane)
            bottom_level_id = view_range.GetLevelId(DB.PlanViewPlane.ViewDepthPlane)
            
            top_offset = view_range.GetOffset(DB.PlanViewPlane.TopClipPlane)
            bottom_offset = view_range.GetOffset(DB.PlanViewPlane.ViewDepthPlane)
            
            top_level = self.doc.GetElement(top_level_id)
            bottom_level = self.doc.GetElement(bottom_level_id)
            
            if top_level and bottom_level:
                top_elevation = top_level.Elevation + top_offset
                bottom_elevation = bottom_level.Elevation + bottom_offset
                
                if location > top_elevation or location < bottom_elevation:
                    self.issues.append(
                        "Element elevation ({:.2f}) is outside view range ({:.2f} to {:.2f})".format(
                            location, bottom_elevation, top_elevation
                        )
                    )
                else:
                    self.info.append("Element is within view range")
        except Exception as e:
            logger.debug("Error checking view range: {}".format(e))
    
    def _get_element_elevation(self):
        """Get element elevation/Z coordinate."""
        try:
            location = self.element.Location
            if isinstance(location, DB.LocationPoint):
                return location.Point.Z
            elif isinstance(location, DB.LocationCurve):
                curve = location.Curve
                return (curve.GetEndPoint(0).Z + curve.GetEndPoint(1).Z) / 2.0
            
            # Try bounding box
            bbox = self.element.get_BoundingBox(None)
            if bbox:
                return (bbox.Min.Z + bbox.Max.Z) / 2.0
            
            return None
        except:
            return None
    
    def _check_design_options(self):
        """Check design option visibility."""
        try:
            design_option_param = self.element.get_Parameter(
                DB.BuiltInParameter.DESIGN_OPTION_ID
            )
            
            if not design_option_param:
                return
            
            design_option_id = design_option_param.AsElementId()
            
            if design_option_id == DB.ElementId.InvalidElementId:
                return
            
            design_option = self.doc.GetElement(design_option_id)
            if not design_option:
                return
            
            # Check view design option setting
            view_design_option = self.view.get_Parameter(
                DB.BuiltInParameter.VIEWER_OPTION_VISIBILITY
            )
            
            if view_design_option:
                view_do_id = view_design_option.AsElementId()
                
                if view_do_id != design_option_id and view_do_id != DB.ElementId.InvalidElementId:
                    self.issues.append(
                        "Element in design option '{}' which is not active in view".format(
                            design_option.Name
                        )
                    )
        except Exception as e:
            logger.debug("Error checking design options: {}".format(e))
    
    def _check_crop_region(self):
        """Check if element is outside crop region."""
        try:
            if not self.view.CropBoxActive:
                self.info.append("View crop box is not active")
                return
            
            crop_box = self.view.CropBox
            elem_bbox = self.element.get_BoundingBox(self.view)
            
            if not elem_bbox:
                return
            
            # Simple check if bounding boxes overlap
            if not self._bounding_boxes_overlap(crop_box, elem_bbox):
                self.issues.append("Element is outside view crop region")
            else:
                self.info.append("Element is within crop region")
        except Exception as e:
            logger.debug("Error checking crop region: {}".format(e))
    
    def _bounding_boxes_overlap(self, bb1, bb2):
        """Check if two bounding boxes overlap."""
        return not (
            bb1.Max.X < bb2.Min.X or bb1.Min.X > bb2.Max.X or
            bb1.Max.Y < bb2.Min.Y or bb1.Min.Y > bb2.Max.Y or
            bb1.Max.Z < bb2.Min.Z or bb1.Min.Z > bb2.Max.Z
        )
    
    def _check_temporary_hide(self):
        """Check for temporary hide/isolate."""
        try:
            # Check if view has temporary hide/isolate active
            temp_hide_isolate = self.view.GetIsTemporaryAnalyticalDisplayModeEnabled()
            
            if self.view.IsInTemporaryViewMode(DB.TemporaryViewMode.TemporaryHideIsolate):
                self.info.append("WARNING: View has Temporary Hide/Isolate active")
        except Exception as e:
            logger.debug("Error checking temporary hide: {}".format(e))


def get_selection():
    """Get currently selected element."""
    selection = revit.get_selection()
    element_ids = selection.get_element_ids()
    
    if not element_ids:
        forms.alert("Please select an element first.", exitscript=True)
    
    if len(element_ids) > 1:
        forms.alert("Please select only ONE element.", exitscript=True)
    
    element_id = list(element_ids)[0]
    return revit.doc.GetElement(element_id)


def format_results(issues, info):
    """Format and display diagnostic results."""
    output.print_md("# Element Visibility Diagnostic Results")
    output.print_md("---")
    
    if issues:
        output.print_md("## ⚠️ POTENTIAL ISSUES FOUND:")
        for i, issue in enumerate(issues, 1):
            output.print_md("{}. **{}**".format(i, issue))
    else:
        output.print_md("## ✅ No visibility issues detected!")
        output.print_md("The element should be visible based on all checked settings.")
    
    if info:
        output.print_md("\n## ℹ️ Additional Information:")
        for item in info:
            output.print_md("- {}".format(item))


def main():
    """Main execution function."""
    # Get active view
    active_view = revit.active_view
    
    if not active_view:
        forms.alert("No active view found.", exitscript=True)
    
    # Get selected element
    element = get_selection()
    
    # Display element info
    output.print_md("**Element ID:** {}".format(element.Id))
    output.print_md("**Element Category:** {}".format(
        element.Category.Name if element.Category else "None"
    ))
    output.print_md("**Active View:** {} ({})".format(
        active_view.Name, active_view.ViewType
    ))
    output.print_md("---\n")
    
    # Run diagnostics
    diagnostic = VisibilityDiagnostic(element, active_view)
    issues, info = diagnostic.run_diagnostics()
    
    # Display results
    format_results(issues, info)


if __name__ == "__main__":
    main()