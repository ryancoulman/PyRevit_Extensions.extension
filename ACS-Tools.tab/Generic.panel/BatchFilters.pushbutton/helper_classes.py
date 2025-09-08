from enum import Enum

class CheckBoxState(Enum):
    '''Custom class to handle multi-state of three-way checkbox'''
    CHECKED = True
    UNCHECKED = False
    INDETERMINATE = None 

class ListItem:
    """Helper Class for displaying selected sheets in custom GUI form."""

    def __init__(self, Name='Unnamed', element=None, checked=False, visible=False, IsThreeWay=CheckBoxState.UNCHECKED):
        # Use global `is_sheet_view` to determine if the checkbox should be enabled
        self.Name = Name
        self.IsChecked = checked   
        self.IsVisible = visible
        self.ThreeWayState = IsThreeWay  
        self.element = element
