# Import the modules
from pathlib import Path
import chat_parser
from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.popup import Popup


kv = """
BoxLayout:
    orientation: "vertical"
    Label:
        id: drop_label
        text: "Drop your WhatsApp chat file here"
        opacity: 1
        font_size: 24
        size_hint: 1, 0.1
        text_size: self.size
        valign: "middle"
        halign: "center"
        canvas.before:
            Color:
                rgba: 0, 0, 0, 0.5
            Rectangle:
                pos: self.pos
                size: self.size
<SaveDialog>:
    id: save_dialog
    BoxLayout:
        size_hint: 1, 0.3
        pos_hint: {"top": 1}
        orientation: "vertical"
        FileChooserListView:
            id: file_chooser
            on_selection: root.selected(file_chooser.selection)
        BoxLayout:
            size_hint: 1, 0.2
            Button:
                text: "Cancel"
                on_release: root.cancel()
            Button:
                text: "Save"
                on_release: root.save(file_chooser.path, file_chooser.selection)
"""


class WhatsAppChatExtractor(App):
    title = "WhatsApp Chat Extractor"

    def build(self):
        Window.bind(on_dropfile=self._on_file_drop)

        self.root = Builder.load_string(kv)
        return self.root

    def _on_file_drop(self, window, file_path):
        path_obj = Path(file_path.decode("utf-8"))
        default_output_filepath = path_obj.parent / f"{path_obj.stem}_chat.csv"

        # Show the save dialog
        # save_dialog = SaveDialog()
        # save_dialog.bind(on_save=self._on_save)
        # save_dialog.open()

        # Parse the chat file
        result_path = chat_parser.parse_chat_file(path_obj, default_output_filepath)

        # Show a success message
        self.root.ids.drop_label.text = (
            f"Chat file saved successfully! Location: {result_path}"
        )

    def _on_save(self, instance, path, filename):
        # Parse the chat file
        chat_parser.parse_chat_file(path, filename[0])

        # Show a success message
        self.root.ids.drop_label.text = "Chat file saved successfully!"
        self.root.ids.drop_label.color = (0, 1, 0, 1)


class SaveDialog(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type("on_save")

    def selected(self, selection):
        self.selection = selection

    def save(self, path, filename):
        self.dispatch("on_save", path, filename)
        self.dismiss()

    def cancel(self):
        self.dismiss()

    def on_save(self, path, filename):
        pass


if __name__ == "__main__":
    WhatsAppChatExtractor().run()
