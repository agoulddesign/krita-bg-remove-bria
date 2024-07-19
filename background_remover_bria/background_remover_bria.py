import krita
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase, InfoObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDockWidget
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QRect
import tempfile
import os
import urllib.request
import urllib.error
import json
import ssl

class BackgroundRemover(QDockWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Background Remover BriaAI")
        
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(QLabel("API Key:"))
        layout.addWidget(self.api_key_input)
        
        self.remove_bg_button = QPushButton("Remove Background")
        self.remove_bg_button.clicked.connect(self.remove_background)
        layout.addWidget(self.remove_bg_button)
        
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        self.setWidget(widget)

        # Load saved API key
        self.load_api_key()

        # Connect textChanged signal to save_api_key method
        self.api_key_input.textChanged.connect(self.save_api_key)

    def load_api_key(self):
        app = Krita.instance()
        api_key = app.readSetting("BackgroundRemoverBriaAI", "api_key", "")
        self.api_key_input.setText(api_key)

    def save_api_key(self):
        app = Krita.instance()
        app.writeSetting("BackgroundRemoverBriaAI", "api_key", self.api_key_input.text())

    def remove_background(self):
    
        # Check if API key is blank
        api_key = self.api_key_input.text()
        if api_key == "":
            self.status_label.setText("Error: API key is blank. Please enter a valid API key.")
            return
        
        application = Krita.instance()
        document = application.activeDocument()
        if not document:
            self.status_label.setText("No active document")
            return

        active_node = document.activeNode()
        if not active_node:
            self.status_label.setText("No active layer")
            return

        # Prepare the temporary file path
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, "temp_layer.png")

        # Create an InfoObject for export configuration
        export_params = InfoObject()
        export_params.setProperty("alpha", True)
        export_params.setProperty("compression", 9)
        export_params.setProperty("forceSRGB", False)
        export_params.setProperty("indexed", False)
        export_params.setProperty("interlaced", False)
        export_params.setProperty("saveSRGBProfile", False)
        export_params.setProperty("transparencyFillcolor", [0, 0, 0, 0])

        # Save the active node
        active_node.save(temp_file, 1.0, 1.0, export_params, active_node.bounds())

        # Prepare the API request
        url = "https://engine.prod.bria-api.com/v1/background/remove"
        api_key = self.api_key_input.text()

        try:
            self.status_label.setText("Sending request to the server...")

            # Prepare the multipart form data
            boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
            data = []
            data.append(f'--{boundary}'.encode())
            data.append(b'Content-Disposition: form-data; name="file"; filename="temp_layer.png"')
            data.append(b'Content-Type: image/png')
            data.append(b'')
            with open(temp_file, 'rb') as f:
                data.append(f.read())
            data.append(f'--{boundary}--'.encode())
            data.append(b'')
            body = b'\r\n'.join(data)

            # Create and send the request
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'api_token': api_key
            }
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            
            context = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                self.status_label.setText("Waiting for server response...")

                if response.status == 200:
                    # Parse the JSON response
                    response_data = json.loads(response.read().decode('utf-8'))
                    result_url = response_data.get('result_url')
                    
                    if result_url:
                        self.status_label.setText("Downloading processed image...")

                        # Download the image from the URL
                        result_file = os.path.join(temp_dir, "result_layer.png")
                        urllib.request.urlretrieve(result_url, result_file)

                        # Load the image using QImage
                        image = QImage(result_file)
                        if image.isNull():
                            self.status_label.setText("Failed to load the result image")
                            return

                        # Truncate the active node's name and append " BG Removed"
                        new_layer_name = (active_node.name()[:20] + " NO BG")

                        # Create a new layer
                        new_layer = document.createNode(new_layer_name, "paintlayer")
                        document.rootNode().addChildNode(new_layer, None)
                        
                        # Set the pixel data of the new layer
                        width, height = image.width(), image.height()
                        pixel_data = image.bits().asstring(image.byteCount())
                        new_layer.setPixelData(pixel_data, 0, 0, width, height)
                        
                        document.refreshProjection()
                        self.status_label.setText("Background removed successfully")
                    else:
                        self.status_label.setText("Error: No result URL in response")
                else:
                    self.handle_error(response.status)

        except urllib.error.HTTPError as e:
            self.handle_error(e.code)
        except urllib.error.URLError as e:
            self.status_label.setText(f"URLError: {str(e)}")
        except json.JSONDecodeError:
            self.status_label.setText("Error: Invalid JSON response")
        except Exception as e:
            self.status_label.setText(f"Unexpected error: {str(e)}")
            
        finally:
            # Clean up temporary files
            if os.path.exists(temp_file):
                os.remove(temp_file)
            if 'result_file' in locals() and os.path.exists(result_file):
                os.remove(result_file)

    def handle_error(self, status_code):
        error_messages = {
            206: "File value was not provided.",
            400: "Request doesn't contain file part.",
            405: "Method not allowed.",
            415: "Unsupported media type.",
            460: "Failed to download image.",
            500: "Internal server error.",
            506: "Insufficient data. The given input is not supported by the Bria API."
        }
        self.status_label.setText(f"Error: {error_messages.get(status_code, 'Unknown error')}")

    def canvasChanged(self, canvas):
        pass

class BackgroundRemoverExtension(krita.Extension):

    def __init__(self, parent):
        super().__init__(parent)

    def setup(self):
        pass

    def createActions(self, window):
        pass

Krita.instance().addExtension(BackgroundRemoverExtension(Krita.instance()))

def createInstance():
    return BackgroundRemover()

Application.addDockWidgetFactory(
    DockWidgetFactory("background_remover_bria",
                      DockWidgetFactoryBase.DockRight,
                      createInstance))
