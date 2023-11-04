# Import the modules
import zipfile
from kivy.app import App
from kivy.core.window import Window


# Define a function to handle the file drop event
def on_drop(file_path):
    # Check if the file is a zip file
    if zipfile.is_zipfile(file_path):
        # Open the zip file
        zip_file = zipfile.ZipFile(file_path, "r")
        # Print the file name and size
        print(f"File name: {zip_file.filename}")
        print(f"File size: {zip_file.file_size} bytes")
        # Close the zip file
        zip_file.close()
    else:
        # Print an error message
        print("The file is not a zip file")


class WhatsAppChatExtractor(App):
    title = "WhatsApp Chat Extractor"

    def build(self):
        Window.bind(on_dropfile=self._on_file_drop)
        return

    def _on_file_drop(self, window, file_path):
        on_drop(file_path)
        return


if __name__ == "__main__":
    WhatsAppChatExtractor().run()
