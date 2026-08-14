Credit Card Statement Analyzer - macOS Installation Guide

1. Extract the entire folder to a local folder on the Mac, such as Applications or Documents.
2. Double-click "Install Credit Card Analyzer.command".
3. If macOS blocks the file on first launch, Control-click it, choose "Open", and confirm again.
4. The installer creates an isolated Python environment and installs all application dependencies inside this folder. It does not modify the system Python installation.
5. If Ollama is not installed, the installer opens the official Ollama download page. Install Ollama, then run the installer again to download the local categorization model.
6. For future launches, double-click "Start Credit Card Analyzer.command". The application opens automatically in the browser.

Important Notes

- Ollama and llama3.2:3b provide local AI merchant categorization. Statement information is not uploaded to the cloud for classification.
- The first model download requires an internet connection and approximately 2 GB of disk space. The model can be used offline afterward.
- The application, Python environment, and model are independent. Deleting the application folder does not automatically remove the Ollama model.
- This package supports both Apple Silicon and Intel Macs. Required components are selected for the current Mac during installation.
