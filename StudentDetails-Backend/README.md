# Fact Finding Report Backend

This is the backend for the Fact Finding Report application. It processes student data and generates PDF reports.

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install wkhtmltopdf

pdfkit requires wkhtmltopdf to be installed on your system:

- **Windows**: Download and install from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
- **macOS**: `brew install wkhtmltopdf`
- **Linux**: `sudo apt-get install wkhtmltopdf`

After installation, ensure the wkhtmltopdf executable is in your system PATH.

### 3. Prepare Input Files

Place the following files in the `input` directory:

- `students.csv`: Contains student data
- `registration_photos.zip`: Contains student registration photos
- `application_photos.zip`: Contains student application photos

### 4. Run the Application

```bash
python app.py
```

The server will start on http://127.0.0.1:5000

## API Endpoints

- `GET /load_data`: Loads data from the input files
- `GET /get_students`: Returns a list of all students
- `GET /search_student?roll_number=<roll_number>`: Searches for students by roll number
- `GET /get_student/<roll_number>`: Gets details for a specific student
- `GET /generate_doc/<roll_number>`: Generates and returns a PDF report for a student

## Directory Structure

- `input/`: Contains input data files
  - `students.csv`: Student data
  - `registration_photos.zip`: Registration photos
  - `application_photos.zip`: Application photos
  - `registration_photos/`: Extracted registration photos
  - `application_photos/`: Extracted application photos
- `output/`: Contains generated PDF reports

## Data Processing

All data from the CSV file is processed as strings, regardless of their apparent data type. The application matches students to their photos using the roll number as an identifier.
