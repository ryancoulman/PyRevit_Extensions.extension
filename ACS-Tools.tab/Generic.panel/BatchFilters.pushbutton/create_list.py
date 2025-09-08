from helper_classes import ListItem
from System.Collections.Generic import List

def create_List(dict_elements):
    """Function to create a List<ListItem> to parse it in GUI ComboBox.
    :param dict_elements:   dict of views ({name:view})
    :return:                List<ListItem>"""
    list_of_views = List[type(ListItem())]()
    for name, view in sorted(dict_elements.items()):
        list_of_views.Add(ListItem(name, view))
    return list_of_views