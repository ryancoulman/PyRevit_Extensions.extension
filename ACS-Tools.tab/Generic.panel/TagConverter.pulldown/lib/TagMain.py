from Autodesk.Revit.DB import Transaction, TextNote
from pyrevit import forms


class MainHandler():
    def __init__(self, doc, tags_to_process, selected_style_id):
        self.doc = doc
        self.tags_to_process = tags_to_process
        self.selected_style_id = selected_style_id
        self.main()


    def main(self):
        with Transaction(self.doc, "Convert Annotation Tags to Plain Text") as t:
            t.Start()

            for tag in self.tags_to_process:
                location = tag.TagHeadPosition
                tag_text = tag.TagText
                
                if location and tag_text:
                    print("Processing tag with text: {}".format(tag_text))
                    
                    # Create a TextNote at the tag's location
                    TextNote.Create(self.doc, self.doc.ActiveView.Id, location, tag_text, self.selected_style_id)
                    
            # Optionally delete original tags
            if self.delete_tags():
                for tag in self.tags_to_process:
                    self.doc.Delete(tag.Id)

            t.Commit()
            print("Transaction committed")

    def delete_tags(self):
        # If the user clicks "ok", the result will be True and the script will stop.
        result = forms.alert(
            "Do you want to delete the original tags? Select 'Cancel' to keep.",
            ok=True,
            cancel=True
        )
        return result