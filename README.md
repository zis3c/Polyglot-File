# Polyglot File Generator

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

A powerful educational tool designed to create files that are valid in multiple formats simultaneously (e.g., JPEG + PDF), enabling advanced steganography and file structure research.

> [!WARNING]
> **Educational Purposes Only**: This tool is designed for educational purposes and security research. The authors are not responsible for any misuse.

## Features

- 🖼️ **Multi-Format Support**: Generate valid `JPG+PDF` and `PNG+PDF` polyglots.
- 🎨 **Premium UI**: Beautiful ASCII art banner and colored output using `rich`.
- 🖱️ **Interactive Mode**: Easy-to-use wizard for selecting files and output names.
- 🛡️ **Auto-Injection**: Automatically handles complex chunk injection and comment segmentation.
- 🧠 **Smart Validation**: Automatically strips quotes from drag-and-drop paths and verifies files.
- � **Organized Output**: Automatically saves results to a dedicated directory with smart naming.

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/zis3c/Polyglot-File
   cd Polyglot-File
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Interactive Mode
Simply run the script without arguments:
```bash
python polyglot_tool.py
```
Follow the prompts to drag-and-drop your Image and PDF files. The tool handles the rest.

### Command Line Interface
For advanced users or automation:
```bash
python polyglot_tool.py --help
```

**Example Usage:**
```bash
python polyglot_tool.py --image "input.jpg" --pdf "hidden.pdf" --output result.jpg
```

| Argument | Description |
|----------|-------------|
| `--image` | Path to the source JPEG or PNG image |
| `--pdf` | Path to the source PDF document |
| `--output` | (Optional) Desired output filename |
| `--help` | Show the help message and exit |

## How It Works

1. **Parsing**: Validates the input image structure (PNG chunks or JPG markers).
2. **Injection**: 
   - **PNG**: Injects a custom `pDfH` chunk containing the PDF header and startstream.
   - **JPG**: Injects the PDF header into a specially crafted comment (`COM`) segment.
3. **Appending**: Appends the full PDF body after the image data, wrapped in a PDF stream.
4. **Result**: The file is a valid image (ignoring the hidden data) and a valid PDF (starting from the injected header).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
