import argparse
import os
import sys
import struct
import zlib
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align
from rich import print as rprint

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

console = Console()

def print_banner():
    banner = r"""[bold cyan]
╺━┓╻┏━┓┏━┓┏━╸   ┏━┓┏━┓╻  ╻ ╻┏━╸╻  ┏━┓╺┳╸   
┏━┛┃┗━┓╺━┫┃     ┣━┛┃ ┃┃  ┗┳┛┃╺┓┃  ┃ ┃ ┃    
┗━╸╹┗━┛┗━┛┗━╸   ╹  ┗━┛┗━╸ ╹ ┗━┛┗━╸┗━┛ ╹    
[/bold cyan]"""
    console.print(banner)

def inject_pdf_header_into_png(png_data, pdf_data):
    """
    Injects PDF header into a private PNG chunk and wraps PNG data in a PDF stream.
    """
    if png_data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError("Input file is not a valid PNG.")

    # Parse PNG to find where to insert our chunk (after IHDR)
    ptr = 8
    ihdr_len = struct.unpack('>I', png_data[ptr:ptr+4])[0]
    ptr += 4 + 4 + ihdr_len + 4
    
    # Calculate length of data to hide (rest of PNG)
    data_to_hide_len = 4 + len(png_data[ptr:])
    
    # PDF Header + Object Start + Stream Start
    header_str = f"%PDF-1.4\n9999 0 obj\n<< /Length {data_to_hide_len} >>\nstream\n"
    chunk_data = header_str.encode('ascii')
    
    chunk_type = b'pDfH' 
    chunk_len = len(chunk_data)
    
    # CRC
    crc = zlib.crc32(chunk_type)
    crc = zlib.crc32(chunk_data, crc) & 0xffffffff
    
    # Build chunk
    new_chunk = struct.pack('>I', chunk_len) + chunk_type + chunk_data + struct.pack('>I', crc)
    
    console.print("[dim]Injecting PDF header into PNG structure...[/dim]")
    
    part1 = png_data[:ptr]
    part2 = new_chunk
    part3 = png_data[ptr:]
    
    # End stream and append PDF
    pdf_prefix = b'\nendstream\nendobj\n'
    part4 = pdf_prefix + pdf_data
    
    return part1 + part2 + part3 + part4

def inject_pdf_header_into_jpg(jpg_data, pdf_data):
    """
    Injects PDF header into a JPG Comment segment and wraps JPG data in a PDF stream.
    """
    if jpg_data[:2] != b'\xff\xd8':
        raise ValueError("Input file is not a valid JPG.")

    data_to_hide_len = len(jpg_data) - 2
    
    header_str = f"%PDF-1.4\n9999 0 obj\n<< /Length {data_to_hide_len} >>\nstream\n"
    header_bytes = header_str.encode('ascii')
    
    segment_len = 2 + len(header_bytes)
    
    if segment_len > 65535:
        raise ValueError("PDF Header too long for a single JPG comment segment.")
        
    comment_segment = b'\xff\xfe' + struct.pack('>H', segment_len) + header_bytes
    
    console.print("[dim]Injecting PDF header into JPG comments...[/dim]")
    
    part1 = jpg_data[:2] # SOI
    part2 = comment_segment
    part3 = jpg_data[2:] # Rest of JPG
    
    # End stream and append PDF
    pdf_prefix = b'\nendstream\nendobj\n'
    part4 = pdf_prefix + pdf_data
    
    return part1 + part2 + part3 + part4

def create_polyglot(image_path, pdf_path, output_path=None):
    if not os.path.exists(image_path):
        console.print(f"[bold red]Error:[/bold red] Image file not found: {image_path}")
        return False
    if not os.path.exists(pdf_path):
        console.print(f"[bold red]Error:[/bold red] PDF file not found: {pdf_path}")
        return False

    # Determine Image Type
    with open(image_path, 'rb') as f:
        header = f.read(8)
    
    mode = "Unknown"
    if header.startswith(b'\x89PNG\r\n\x1a\n'):
        mode = "PNG+PDF"
    elif header.startswith(b'\xff\xd8'):
        mode = "JPG+PDF"
    else:
        console.print("[bold red]Error:[/bold red] Unsupported image format. Only JPG and PNG are supported.")
        return False

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task(description=f"Reading files...", total=None)
            
            with open(image_path, 'rb') as f: image_data = f.read()
            with open(pdf_path, 'rb') as f: pdf_data = f.read()
            
            progress.add_task(description=f"Injecting payload ({mode})...", total=None)
            
            if mode == "PNG+PDF":
                combined = inject_pdf_header_into_png(image_data, pdf_data)
            elif mode == "JPG+PDF":
                combined = inject_pdf_header_into_jpg(image_data, pdf_data)
            
            # Output handling
            output_dir = "polyglot_results"
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            if not output_path:
                ext = ".png" if mode == "PNG+PDF" else ".jpg"
                output_path = f"polyglot_output{ext}"
            
            if os.path.dirname(output_path) == "":
                output_path = os.path.join(output_dir, output_path)
                
            progress.add_task(description=f"Writing to disk...", total=None)
            with open(output_path, 'wb') as f:
                f.write(combined)
                
        # Success Panel
        panel = Panel(
            f"[bold green]Polyglot Created Successfully![/bold green]\n\n"
            f"[bold white]Mode:[/bold white] {mode}\n"
            f"[bold white]Output:[/bold white] {output_path}\n"
            f"[bold white]Size:[/bold white] {len(combined):,} bytes",
            title="[bold cyan]Success[/bold cyan]",
            border_style="green"
        )
        console.print(panel)
        return True

    except Exception as e:
        console.print(Panel(f"{e}", title="[bold red]Exception[/bold red]", style="red"))
        return False

def get_valid_path(prompt_text):
    while True:
        path = Prompt.ask(prompt_text).strip()
        # Handle PowerShell drag-and-drop artifact
        if path.startswith('& '):
            path = path[2:].strip()
        path = path.strip('"').strip("'")
        
        if os.path.exists(path):
            return path
        console.print(f"[bold red]Error:[/bold red] File not found: {path}. Please try again.")

def interactive_mode():
    print_banner()
    
    # List files in input_files if exists
    input_dir = "input_files"
    
    image_path = get_valid_path("Enter Image Path (JPG/PNG)")
    pdf_path = get_valid_path("Enter PDF Path")
    
    # Smart Output Name
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    ext = os.path.splitext(image_path)[1]
    default_output = f"{base_name}_polyglot{ext}"
    
    output_name = Prompt.ask("Enter Output Filename", default=default_output)
    
    if Confirm.ask(f"\nProceed to combine [green]{image_path}[/green] + [green]{pdf_path}[/green]?"):
        console.print()
        create_polyglot(image_path, pdf_path, output_name)
    else:
        console.print("[red]Aborted.[/red]")

def main():
    parser = argparse.ArgumentParser(description="Ultimate Polyglot Tool")
    parser.add_argument("--pdf", help="Path to PDF file")
    parser.add_argument("--image", help="Path to Image file (JPG or PNG)")
    # Backwards compatibility args (optional)
    parser.add_argument("--png", help=argparse.SUPPRESS) 
    parser.add_argument("--jpg", help=argparse.SUPPRESS)
    
    parser.add_argument("--output", help="Path for output file")

    # If no args, run interactive
    if len(sys.argv) == 1:
        try:
            interactive_mode()
        except KeyboardInterrupt:
            console.print("\n[bold red]Aborted![/bold red]")
        return

    args = parser.parse_args()
    
    # Handle args normalization
    img_path = args.image or args.png or args.jpg
    
    if not img_path or not args.pdf:
        # If user tried CLI but missed args, show help
        parser.print_help()
        return
        
    print_banner()
    create_polyglot(img_path, args.pdf, args.output)

if __name__ == "__main__":
    main()
