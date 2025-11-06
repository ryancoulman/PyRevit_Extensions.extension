# -*- coding: utf-8 -*-

__title__ = "Close\nTabs"
__doc__ = "Closes all tabs except the currently active one."

from pyrevit import revit

def get_open_views():
    """Get all currently open UIViews.
    
    Returns:
        list: List of UIView objects
    """
    uidoc = revit.uidoc
    return uidoc.GetOpenUIViews()


def get_active_view():
    """Get the currently active view.
    
    Returns:
        DB.View: The active view object
    """
    return revit.doc.ActiveView


def close_views(views_to_close):
    """Close a list of UIViews.
    
    Args:
        views_to_close (list): List of UIView objects to close
    """
    for uiview in views_to_close:
        uiview.Close()


def main():
    """Main execution function."""
    
    # Get active view and open views
    active_view = get_active_view()
    open_views = get_open_views()
    
    if len(open_views) <= 1:
        print("**Only one tab is open. Nothing to close.**")
        return
    
    # Filter out the active view from the list
    views_to_close = [
        uiview for uiview in open_views 
        if uiview.ViewId != active_view.Id
    ]
    
    # Close all other views 
    if len(views_to_close) < len(open_views):
        close_views(views_to_close)
    else:
        print("**Error: Could not fetch active view**")


if __name__ == "__main__":
    main()