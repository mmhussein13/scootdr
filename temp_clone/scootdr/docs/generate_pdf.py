import datetime
import os
import markdown
from bs4 import BeautifulSoup
from weasyprint import HTML, CSS

def generate_pdf_from_markdown(markdown_file, output_pdf):
    """
    Convert a markdown file to PDF using WeasyPrint
    """

    # Read the markdown file
    with open(markdown_file, 'r') as file:
        markdown_text = file.read()

    # Convert markdown to HTML
    html = markdown.markdown(
        markdown_text,
        extensions=['tables', 'fenced_code', 'codehilite']
    )

    # Add CSS styling and wrap in HTML structure
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Scooter Rental Management System - User Guide</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 2cm;
                color: #333;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #1a5276;
                margin-top: 20px;
                margin-bottom: 10px;
            }}
            h1 {{
                text-align: center;
                font-size: 24pt;
                border-bottom: 2px solid #1a5276;
                padding-bottom: 10px;
            }}
            h2 {{
                font-size: 18pt;
                border-bottom: 1px solid #ddd;
                padding-bottom: 5px;
            }}
            h3 {{
                font-size: 14pt;
            }}
            p, ul, ol {{
                margin-bottom: 10px;
            }}
            code {{
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 4px;
                font-family: Consolas, monospace;
            }}
            pre {{
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
                font-family: Consolas, monospace;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            img {{
                max-width: 100%;
                height: auto;
                margin: 10px auto;
                display: block;
                border: 1px solid #ddd;
            }}
            hr {{
                border: none;
                height: 1px;
                background-color: #ddd;
                margin: 20px 0;
            }}
            .footer {{
                text-align: center;
                font-size: 9pt;
                color: #777;
                margin-top: 30px;
                border-top: 1px solid #ddd;
                padding-top: 10px;
            }}
        </style>
    </head>
    <body>
        {html}
        <div class="footer">
            <p>Scooter Rental Management System - User Guide © {datetime.datetime.now().year}</p>
            <p>Generated on {datetime.datetime.now().strftime('%Y-%m-%d')}</p>
        </div>
    </body>
    </html>
    """

    # Fix image paths
    soup = BeautifulSoup(styled_html, 'html.parser')
    markdown_dir = os.path.dirname(os.path.abspath(markdown_file))

    for img in soup.find_all('img'):
        src = img.get('src')
        if src and not src.startswith(('http://', 'https://')):
            img['src'] = os.path.abspath(os.path.join(markdown_dir, src))

    # Convert the updated HTML with fixed image paths to PDF
    HTML(string=str(soup), base_url=markdown_dir).write_pdf(output_pdf)

    print(f"✅ PDF generated: {output_pdf}")

if __name__ == "__main__":
    markdown_file = "user_guide.md"
    output_pdf = "Scooter_Rental_Management_System_User_Guide.pdf"
    generate_pdf_from_markdown(markdown_file, output_pdf)
