import os

def find_extension_root():
    """
    Traverse upwards from this file until a folder ending with '.extension' is found.
    Peform top down search of WPF folder.
    """
    folder = os.path.abspath(os.path.dirname(__file__))
    while folder != os.path.dirname(folder):  # stop at filesystem root
        if folder.endswith(".extension"):
            return folder
        folder = os.path.dirname(folder)
    raise FileNotFoundError("Could not find the extension root folder (.extension)")

def get_wpf_path(xaml_name):
    """
    Get the path to the WPF folder within the extension.
    """
    ext_root = find_extension_root()
    wpf_dir = os.path.join(ext_root, "WPF")
    xaml_path = os.path.join(wpf_dir, xaml_name)
    if not os.path.exists(xaml_path):
        raise FileNotFoundError("XAML file not found: {}".format(xaml_path))
    return xaml_path

