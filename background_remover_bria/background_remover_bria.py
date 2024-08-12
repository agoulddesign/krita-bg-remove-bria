import os
import sys
import json
import tempfile
import urllib.request
import urllib.error
import ssl
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

import krita
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase, InfoObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDockWidget, QApplication, QCheckBox
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QRect

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
        
        self.batch_checkbox = QCheckBox("Batch (all selected layers)")
        layout.addWidget(self.batch_checkbox)
        
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
        api_key = app.readSetting("AGD_BriaAI", "api_key", "")
        self.api_key_input.setText(api_key)

    def save_api_key(self):
        app = Krita.instance()
        app.writeSetting("AGD_BriaAI", "api_key", self.api_key_input.text())

    def remove_background(self):
        # Clear the status_label field
        self.status_label.setText("Preparing file(s) and request(s)...")
        
        # Check if API key is blank
        api_key = self.api_key_input.text()
        if api_key == "":
            self.status_label.setText("Error: API key is blank. Please enter a valid API key.")
            return
        
        application = Krita.instance()
        document = application.activeDocument()
        window = application.activeWindow()

        if not document:
            self.status_label.setText("No active document")
            return

        if not window:
            self.status_label.setText("No active window")
            return

        view = window.activeView()
        if not view:
            self.status_label.setText("No active view")
            return

        nodes = [document.activeNode()] if not self.batch_checkbox.isChecked() else view.selectedNodes()
        if not nodes:
            self.status_label.setText("No active layer or no layers selected")
            return

        # Set batch mode
        document.setBatchmode(True)

        # Create a thread pool
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Submit tasks to the thread pool
            futures = [executor.submit(self.process_node, node, api_key, document) for node in nodes]

            # Update status as tasks complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    self.status_label.setText(f"Processed: {result[:27]}..." if len(result) > 30 else result)
                    QApplication.processEvents()
                except Exception as e:
                    self.status_label.setText(f"Error: {error_msg[:23]}..." if len(error_msg) > 30 else f"Error: {error_msg}")
                    QApplication.processEvents()

        # Unset batch mode
        document.setBatchmode(False)

        self.status_label.setText("All images processed")
            
    def process_node(self, node, api_key, document):
        # Prepare the temporary file path
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"temp_layer_{threading.get_ident()}.jpg")

        # Create an InfoObject for export configuration
        export_params = InfoObject()
        export_params.setProperty("quality", 100)
        export_params.setProperty("forceSRGB", False)
        export_params.setProperty("saveSRGBProfile", False)

        # Save the active node
        node.save(temp_file, 1.0, 1.0, export_params, node.bounds())

        # Prepare the API request
        url = "https://engine.prod.bria-api.com/v1/background/remove"

        try:
            # Prepare the multipart form data
            boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
            data = []
            data.append(f'--{boundary}'.encode())
            data.append(b'Content-Disposition: form-data; name="file"; filename="temp_layer.jpg"')
            data.append(b'Content-Type: image/jpg')
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
            
            # Check if we're on a Unix-like system (macOS or Linux)
            if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
                # Set the SSL certificate file path for macOS and Linux
                cert_file = '/etc/ssl/cert.pem'
                
                # Check if the certificate file exists
                if os.path.exists(cert_file):
                    os.environ['SSL_CERT_FILE'] = cert_file
                else:
                    return f"Warning: Certificate file {cert_file} not found."
                    
            context = ssl.create_default_context()
            
            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                if response.status == 200:
                    # Parse the JSON response
                    response_data = json.loads(response.read().decode('utf-8'))
                    result_url = response_data.get('result_url')
                    
                    if result_url:
                        # Download the image from the URL
                        result_file = os.path.join(temp_dir, f"result_layer_{threading.get_ident()}.png")
                        urllib.request.urlretrieve(result_url, result_file)

                        # Load the image using QImage
                        image = QImage(result_file)
                        if image.isNull():
                            return "Failed to load the result image"

                        # Truncate the active node's name and append " BG Removed"
                        new_layer_name = (node.name() + " NO BG")

                        # Gets the index of the active layer and then hides it
                        node_index = document.rootNode().childNodes().index(node)
                        node.setVisible(False)
                        
                        # Create a new layer and move to same level as old layer
                        new_layer = document.createNode(new_layer_name, "paintlayer")
                        document.rootNode().addChildNode(new_layer, node)
                        
                        # Set the pixel data of the new layer
                        width, height = image.width(), image.height()
                        pixel_data = image.bits().asstring(image.byteCount())
                        new_layer.setPixelData(pixel_data, 0, 0, width, height)
                        
                        document.refreshProjection()
                        return f"Background removed successfully for {node.name()}"
                    else:
                        return "Error: No result URL in response"
                else:
                    return self.handle_error(response.status)

        except urllib.error.HTTPError as e:
            return self.handle_error(e.code)
        except urllib.error.URLError as e:
            if isinstance(e.reason, ssl.SSLCertVerificationError):
                return "SSL Certificate verification failed. You may need to update your certificates."
            else:
                return f"URLError: {str(e)}"
        except json.JSONDecodeError:
            return "Error: Invalid JSON response"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
            
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
        return f"Error: {error_messages.get(status_code, 'Unknown error')}"

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
