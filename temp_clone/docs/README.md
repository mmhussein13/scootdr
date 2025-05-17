# Scooter Rental Management System Documentation

This directory contains comprehensive documentation for the Scooter Rental Management System.

## Contents

- **user_guide.md**: Complete user guide with instructions for all system features
- **quick_reference.md**: Concise guide for common tasks and shortcuts
- **page_descriptions.md**: Detailed descriptions of each page and its functionality
- **screenshots/**: Directory containing screenshots of various system pages
- **generate_pdf.py**: Script to generate a PDF version of the user guide
- **screenshot_script.py**: Script to automatically capture screenshots of the application

## Using This Documentation

### For End Users

1. Start with the **quick_reference.md** for the most common tasks
2. Refer to the **user_guide.md** for detailed instructions on all features
3. Use the screenshots to familiarize yourself with the interface

### For Administrators

1. Review all documentation to understand the entire system
2. Use the **generate_pdf.py** script to create distributable documentation for your team
3. Update the screenshots as needed using the **screenshot_script.py**

## Generating PDF Documentation

Requirements:
- Python 3.6 or higher
- Python packages: markdown, pdfkit, beautifulsoup4
- wkhtmltopdf installed on your system

To generate a PDF version of the user guide:

```bash
cd docs
python generate_pdf.py
```

This will create a file named `Scooter_Rental_Management_System_User_Guide.pdf` in the docs directory.

## Updating Screenshots

Requirements:
- Python 3.6 or higher
- Python packages: selenium
- Chrome or Chromium web browser
- Chrome WebDriver

To update the screenshots:

```bash
cd docs
python screenshot_script.py
```

This will capture screenshots of all major pages in the application and save them to the `screenshots` directory.

## Contact

For questions or issues regarding this documentation, please contact:
- Email: support@scooterdrsystem.com