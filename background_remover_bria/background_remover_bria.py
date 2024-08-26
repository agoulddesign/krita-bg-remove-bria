import os
import sys
import ssl
import json
import time
import tempfile
import urllib.request
import urllib.error
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed

import krita
from krita import Krita, DockWidgetFactory, DockWidgetFactoryBase, InfoObject
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDockWidget, QApplication, QCheckBox, QSpinBox, QTextEdit, QProgressDialog
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QRect, Qt

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
        self.batch_checkbox.stateChanged.connect(self.toggle_batch_mode)  # Connect to toggle_batch_mode method
        layout.addWidget(self.batch_checkbox)
        
        self.auto_thread_checkbox = QCheckBox("Threads (Auto)")
        self.auto_thread_checkbox.setChecked(True)  # Default is auto
        self.auto_thread_checkbox.stateChanged.connect(self.toggle_thread_count)
        self.auto_thread_checkbox.setVisible(False)  # Initially hidden
        layout.addWidget(self.auto_thread_checkbox)
        
        self.thread_count_spinbox = QSpinBox()
        self.thread_count_spinbox.setMinimum(1)
        self.thread_count_spinbox.setValue(os.cpu_count() or multiprocessing.cpu_count())  # Default to max threads
        self.thread_count_spinbox.setVisible(False)  # Initially hidden
        layout.addWidget(self.thread_count_spinbox)
        
        self.debug_checkbox = QCheckBox("Debug Mode")
        self.debug_checkbox.stateChanged.connect(self.toggle_debug_mode)
        layout.addWidget(self.debug_checkbox)

        self.open_temp_dir_button = QPushButton("Open Temp Directory")
        self.open_temp_dir_button.clicked.connect(self.open_temp_directory)
        self.open_temp_dir_button.setVisible(False)
        layout.addWidget(self.open_temp_dir_button)

        self.remove_bg_button = QPushButton("Remove Background")
        self.remove_bg_button.clicked.connect(self.remove_background)
        layout.addWidget(self.remove_bg_button)
        
        self.status_label = QTextEdit()
        self.status_label.setReadOnly(True)
        self.status_label.setLineWrapMode(QTextEdit.WidgetWidth)
        layout.addWidget(self.status_label)
        
        self.setWidget(widget)

        # Load saved API key
        self.load_api_key()

        # Connect textChanged signal to save_api_key method
        self.api_key_input.textChanged.connect(self.save_api_key)
        
    #Toggle visibility of thread count settings based on batch mode state.
    def toggle_batch_mode(self):
        if self.batch_checkbox.isChecked():
            self.auto_thread_checkbox.setVisible(True)
            self.toggle_thread_count()  # Adjust visibility of the spinbox based on auto thread checkbox
        else:
            self.auto_thread_checkbox.setVisible(False)
            self.thread_count_spinbox.setVisible(False)
        
    def toggle_thread_count(self):
        if self.auto_thread_checkbox.isChecked():
            self.thread_count_spinbox.setVisible(False)
        else:
            self.thread_count_spinbox.setVisible(True)

    def toggle_debug_mode(self):
        self.open_temp_dir_button.setVisible(self.debug_checkbox.isChecked())

    def open_temp_directory(self):
        temp_dir = tempfile.gettempdir()
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.call(['open', temp_dir])
        elif sys.platform.startswith('win'):  # Windows
            os.startfile(temp_dir)
        else:  # Linux and other Unix-like
            subprocess.call(['xdg-open', temp_dir])

    def load_api_key(self):
        app = Krita.instance()
        
        # Check for the old API key setting
        old_api_key = app.readSetting("BackgroundRemoverBriaAI", "api_key", "")
        if old_api_key:
            # If the old key is found, save it to the new setting and delete the old setting
            app.writeSetting("AGD_BriaAI", "api_key", old_api_key)
            app.writeSetting("BackgroundRemoverBriaAI", "api_key", "")  # Clear the old key
            self.api_key_input.setText(old_api_key)
        else:
            # If no old key is found, just load the new key
            new_api_key = app.readSetting("AGD_BriaAI", "api_key", "")
            self.api_key_input.setText(new_api_key)

    def save_api_key(self):
        app = Krita.instance()
        app.writeSetting("AGD_BriaAI", "api_key", self.api_key_input.text())
        self.status_label.setText("API Key saved")

    def remove_background(self):
        start_time = time.time()

        # Create a progress dialog
        progress = QProgressDialog("Removing background...", "Cancel", 0, 100, Krita.instance().activeWindow().qwindow())
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()

        # Clear the status_label field
        self.status_label.setText("Preparing file(s) and request(s)...")
        QApplication.processEvents()

        # Check if API key is blank
        api_key = self.api_key_input.text()
        if api_key == "":
            self.status_label.setText("Error: API key is blank. Please enter a valid API key.")
            progress.close()
            return

        application = Krita.instance()
        document = application.activeDocument()
        window = application.activeWindow()

        if not document:
            self.status_label.setText("No active document")
            progress.close()
            return

        if not window:
            self.status_label.setText("No active window")
            progress.close()
            return

        view = window.activeView()
        if not view:
            self.status_label.setText("No active view")
            progress.close()
            return

        nodes = [document.activeNode()] if not self.batch_checkbox.isChecked() else view.selectedNodes()
        if not nodes:
            self.status_label.setText("No active layer or no layers selected")
            progress.close()
            return

        # Check if we're on a Unix-like system (macOS or Linux)
        if sys.platform.startswith('darwin') or sys.platform.startswith('linux'):
            # Set the SSL certificate file path for macOS and Linux
            cert_file = '/etc/ssl/cert.pem'
            
            # Check if the certificate file exists
            if os.path.exists(cert_file):
                os.environ['SSL_CERT_FILE'] = cert_file
            else:
                self.status_label.setText(f"Warning: Certificate file {cert_file} not found.")
                QApplication.processEvents()
                
        context = ssl.create_default_context()

        # Setup for error handling
        processed_count = 0
        success_count = 0
        total_count = len(nodes)
        error_messages = []
        
        # Determine max_workers based on user selection
        if self.auto_thread_checkbox.isChecked():
            max_workers = os.cpu_count() or multiprocessing.cpu_count()
        else:
            max_workers = self.thread_count_spinbox.value()
        
        # Set batch mode
        document.setBatchmode(True)

        progress.setValue(10)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_node, node, api_key, document, context) for node in nodes]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    processed_count += 1
                    if "successfully" in result.lower():
                        success_count += 1
                    else:
                        error_messages.append(result)
                    self.status_label.append(f"Processed {processed_count}/{total_count}: {result}")
                    progress.setValue(10 + int(90 * processed_count / total_count))
                except Exception as e:
                    processed_count += 1
                    error_messages.append(f"Error: {str(e)}")
                finally:
                    QApplication.processEvents()

        # Unset batch mode
        document.setBatchmode(False)

        # End timing the process
        end_time = time.time()

        # Calculate the total time taken in milliseconds
        total_time_ms = int((end_time - start_time) * 1000)

        # Final status update
        final_status = f"Completed. Processed {success_count}/{total_count} successfully. ({total_time_ms}ms)"
        if error_messages:
            final_status += f"\nErrors: {'; '.join(error_messages)}"
        
        # Add the result from process_node function
        for result in futures:
            final_status += f"\n{result.result()}"
        
        self.status_label.setText(final_status)
        progress.setValue(100)
        progress.close()

    def process_node(self, node, api_key, document, context):
        # Prepare the temporary file path
        temp_dir = tempfile.gettempdir()
        temp_file = os.path.join(temp_dir, f"temp_layer_{threading.get_ident()}.jpg")
        result_file = None

        # Create an InfoObject for export configuration
        export_params = InfoObject()
        export_params.setProperty("quality", 100)  # Use maximum quality for JPEG
        export_params.setProperty("forceSRGB", True)  # Force sRGB color space
        export_params.setProperty("saveProfile", False)  # Don't save color profile
        export_params.setProperty("alpha", True)  # Ensure alpha channel is included
        export_params.setProperty("flatten", True)  # Prevent flattening of the image

        # Save the active node as JPG
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
            
            with urllib.request.urlopen(req, timeout=30, context=context) as response:
                if response.status == 200:
                    # Parse the JSON response
                    response_data = json.loads(response.read().decode('utf-8'))
                    result_url = response_data.get('result_url')
                    
                    if result_url:
                        # Download the image from the URL
                        result_file = os.path.join(temp_dir, f"result_layer_{threading.get_ident()}.png")
                        urllib.request.urlretrieve(result_url, result_file)

                        # Rename layer
                        new_layer_name = (node.name() + " NO BG")

                        # Get the color space of the original document
                        original_color_space = document.colorModel()

                        if original_color_space != "RGBA":
                            # Create a new document with the downloaded image
                            app = Krita.instance()
                            temp_doc = app.createDocument(0, 0, "temp_doc", "RGBA", "U8", "", 300.0)
                            temp_layer = temp_doc.createNode("temp_layer", "paintlayer")
                            temp_doc.rootNode().addChildNode(temp_layer, None)
                            
                            # Load the image into the layer
                            image = QImage(result_file)
                            temp_layer.setPixelData(image.constBits().asstring(image.byteCount()), 0, 0, image.width(), image.height())

                            # Convert the temporary document to the original color space
                            temp_doc.setColorSpace(original_color_space, document.colorDepth(), document.colorProfile())
                            temp_doc.refreshProjection()

                            # Copy the layer to the original document
                            copied_layer = temp_layer.clone()
                            document.rootNode().addChildNode(copied_layer, node)
                            copied_layer.setName(new_layer_name)

                            # Close the temporary document
                            temp_doc.close()

                            result = f"Background removed successfully for {node.name()} (Converted to {original_color_space}, please note that colors may not look like the original image)"
                        else:
                            # For RGBA documents, directly create a new layer with the image
                            new_layer = document.createNode(new_layer_name, "paintlayer")
                            
                            # Load the image into the layer
                            image = QImage(result_file)
                            new_layer.setPixelData(image.constBits().asstring(image.byteCount()), 0, 0, image.width(), image.height())
                            
                            document.rootNode().addChildNode(new_layer, node)
                            result = f"Background removed successfully for {node.name()}"

                        # Hide the original layer
                        node.setVisible(False)

                        document.refreshProjection()
                        
                        if self.debug_checkbox.isChecked():
                            result += f"\nDebug: Temporary files saved at {temp_file} and {result_file}"
                        else:
                            os.remove(result_file)
                        
                        return result
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
            if os.path.exists(temp_file) and not self.debug_checkbox.isChecked():
                os.remove(temp_file)

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
