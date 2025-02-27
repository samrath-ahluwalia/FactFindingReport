from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os, time, zipfile
import pandas as pd
from werkzeug.utils import secure_filename
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageTemplate, Frame, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import Image
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'students')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model
class Student(db.Model):
    roll_number = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    application_number = db.Column(db.String(50))
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    exam_center = db.Column(db.String(100))
    exam_location = db.Column(db.String(100))
    seat_number = db.Column(db.String(50))
    marks = db.Column(db.Integer)
    high_scorer = db.Column(db.String(10))
    face_match = db.Column(db.String(10))
    abnormal_city_pref = db.Column(db.String(10))
    registration_timing = db.Column(db.String(50))
    hardware_compliance = db.Column(db.String(10))
    exam_completion_time = db.Column(db.String(50))
    fast_answering = db.Column(db.String(10))
    question_navigation = db.Column(db.String(50))
    answer_similarity = db.Column(db.String(10))
    ip_address_change = db.Column(db.String(10))
    account_lock = db.Column(db.String(10))
    multiple_keyboard_mouse = db.Column(db.String(10))
    center_suspicious_cases = db.Column(db.String(50))
    feedback_issue = db.Column(db.String(50))
    suspicious_behaviour = db.Column(db.String(50))

# Initialize Database
with app.app_context():
    db.drop_all()
    db.create_all()

@app.route('/upload_csv_zip', methods=['POST'])
def upload_csv_zip():
    if 'csv_file' not in request.files or 'zip_file' not in request.files:
        return jsonify({'error': 'Both CSV and ZIP files are required'}), 400

    csv_file = request.files['csv_file']
    zip_file = request.files['zip_file']

    if not csv_file.filename.endswith('.csv') or not zip_file.filename.endswith('.zip'):
        return jsonify({'error': 'Invalid file format. Please upload a CSV and a ZIP file'}), 400

    # Process CSV
    try:
        df = pd.read_csv(csv_file, dtype=str)

        required_columns = {col.name for col in Student.__table__.columns}
        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            return jsonify({'error': f'Missing required columns: {missing_columns}'}), 400

        if 'marks' in df.columns:
            df['marks'] = pd.to_numeric(df['marks'], errors='coerce').fillna(0).astype(int)

        boolean_columns = [
            'high_scorer', 'face_match', 'abnormal_city_pref', 'hardware_compliance',
            'fast_answering', 'answer_similarity', 'ip_address_change', 'account_lock',
            'multiple_keyboard_mouse'
        ]
        for col in boolean_columns:
            if col in df.columns:
                df[col] = df[col].replace({'Yes': 'True', 'No': 'False', '': 'False'})

        for _, row in df.iterrows():
            student_data = row.to_dict()
            existing_student = Student.query.get(student_data['roll_number'])

            if existing_student:
                for key, value in student_data.items():
                    setattr(existing_student, key, value)
            else:
                student = Student(**student_data)
                db.session.add(student)

        db.session.commit()

    except Exception as e:
        return jsonify({'error': f'Failed to process CSV file: {str(e)}'}), 400

    # Process ZIP
    try:
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(zip_file.filename))
        zip_file.save(zip_path)
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(app.config['UPLOAD_FOLDER'])
        os.remove(zip_path)
    except zipfile.BadZipFile:
        return jsonify({'error': 'Invalid ZIP file. Unable to extract'}), 400

    # Return updated student data
    students = Student.query.all()
    student_list = [{col.name: getattr(student, col.name) for col in student.__table__.columns} for student in students]

    return jsonify({'message': 'Files uploaded successfully', 'students': student_list}), 200

@app.route('/get_students', methods=['GET'])
def get_students():
    students = Student.query.all()
    return jsonify([{col.name: getattr(student, col.name) for col in student.__table__.columns} for student in students]), 200


@app.route('/search_student', methods=['GET'])
def search_student():
    roll_number = request.args.get('roll_number', '')
    if not roll_number:
        return jsonify([]), 200

    students = Student.query.filter(Student.roll_number.like(f"%{roll_number}%")).all()
    return jsonify([{col.name: getattr(student, col.name) for col in student.__table__.columns} for student in students]), 200



# Get Student Details
@app.route('/get_student/<roll_number>', methods=['GET'])
def get_student(roll_number):
    student = Student.query.get(roll_number)
    if not student:
        return jsonify({'error': f'Student with roll number {roll_number} not found'}), 404
    return jsonify({col.name: getattr(student, col.name) for col in student.__table__.columns}), 200



@app.route('/generate_doc/<roll_number>', methods=['GET'])
def generate_pdf(roll_number):
    student = Student.query.get(roll_number)
    if not student:
        return jsonify({'error': f'Student with roll number {roll_number} not found'}), 404

    # Define the PDF path and ensure the directory exists
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Fact Finding Report.pdf')
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    # Create the PDF document
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()

    # Custom Styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold',
    )
    heading_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    subheading_style = ParagraphStyle(
        'Subheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=6,
        fontName='Helvetica-Bold',
    )
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=6,
        fontName='Helvetica',
    )

    # Content
    content = []

    # Title
    content.append(Paragraph("Fact-Finding Report", title_style))
    content.append(Spacer(1, 12))

    # Phase 1: Pre-Exam Analysis
    content.append(Paragraph("Phase 1: Pre-Exam Analysis", heading_style))
    content.append(Spacer(1, 6))

    # Face Match Anomalies
    content.append(Paragraph("1. Application Data Verification", subheading_style))
    content.append(Paragraph("• Face Match Anomalies:", body_style))

    # Load photos
    app_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], f"/ph{roll_number}- Application.jpg")
    exam_photo_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{roll_number}- ExamDay.jpg")

    if os.path.exists(app_photo_path) and os.path.exists(exam_photo_path):
        from reportlab.platypus import Image
        app_photo = Image(app_photo_path, width=2.5*inch, height=2.5*inch)
        exam_photo = Image(exam_photo_path, width=2.5*inch, height=2.5*inch)
        face_match_table = Table([
            ["Application Photo", "Exam Day Photo"],
            [app_photo, exam_photo]
        ], colWidths=[2.5 * inch, 2.5 * inch])
    else:
        face_match_table = Table([
            ["Application Photo", "Exam Day Photo"],
            ["Photo not found", "Photo not found"]
        ], colWidths=[2.5 * inch, 2.5 * inch])

    face_match_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),  # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")),  # Light blue rows
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(face_match_table)
    content.append(Paragraph(f"Matched ✅ / Not Matched ✕: {student.face_match}", body_style))
    content.append(Spacer(1, 12))

    # Abnormal City Preference
    content.append(Paragraph("• Abnormal City Preference:", body_style))
    city_table = Table([
        ["Candidate’s Home City", "Exam Centre City"],
        [student.address.split(',')[0], student.exam_location]
    ], colWidths=[2.5 * inch, 2.5 * inch])
    city_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),  # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")),  # Light blue rows
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(city_table)
    content.append(Paragraph(f"Justification: {student.abnormal_city_pref}", body_style))
    content.append(Spacer(1, 12))

    # Registration Timing Analysis
    content.append(Paragraph("2. Registration Timing Analysis", subheading_style))
    content.append(Paragraph(f"• Registered During/After Exam Completion: {student.registration_timing}", body_style))
    content.append(Spacer(1, 12))

    # Hardware & Compliance Issues
    content.append(Paragraph("3. Hardware & Compliance Issues", subheading_style))
    content.append(Paragraph(f"• Node Compliance Issues: {student.hardware_compliance}", body_style))
    content.append(Spacer(1, 12))

    # Phase 2: Post-Exam Analysis
    content.append(Paragraph("Phase 2: Post-Exam Analysis", heading_style))
    content.append(Spacer(1, 6))

    # Exam Audit Logs
    content.append(Paragraph("1. Exam Audit Logs", subheading_style))
    content.append(Paragraph(f"(a) Answering Behaviour & Timing: {student.exam_completion_time}", body_style))
    content.append(Paragraph(f"(b) Answer Similarity with Adjacent Candidates: {student.answer_similarity}", body_style))
    content.append(Paragraph(f"(c) Suspicious IP Address Change: {student.ip_address_change}", body_style))
    content.append(Spacer(1, 12))

    # Incident Reports
    content.append(Paragraph("2. Incident Reports", subheading_style))
    content.append(Paragraph(f"• Account Lock Events: {student.account_lock}", body_style))
    content.append(Paragraph(f"• Multiple Keyboard/Mouse Detected During Exam: {student.multiple_keyboard_mouse}", body_style))
    content.append(Spacer(1, 12))

    # Centre-Based Suspicious Activity
    content.append(Paragraph("3. Centre-Based Suspicious Activity", subheading_style))
    content.append(Paragraph(f"• Exam Centre with High Number of Suspicious Cases: {student.center_suspicious_cases}", body_style))
    content.append(Spacer(1, 12))

    # Candidate Feedback & Complaints
    content.append(Paragraph("4. Candidate Feedback & Complaints", subheading_style))
    content.append(Paragraph(f"• Reported issue: {student.feedback_issue}", body_style))
    content.append(Spacer(1, 12))

    # Final Observations & Conclusion
    content.append(Paragraph("Final Observations & Conclusion", heading_style))
    content.append(Spacer(1, 6))

    observations_table = Table([
        ["Suspicious Behaviour", "Observed?", "Remarks"],
        ["Face Mismatch", student.face_match, ""],
        ["Suspicious Registration Time", student.registration_timing, ""],
        ["Abnormal City Preference", student.abnormal_city_pref, ""],
        ["Fast answering", student.fast_answering, ""],
        ["Same Response Pattern", student.answer_similarity, ""],
        ["IP Address Change", student.ip_address_change, ""],
        ["Account Lock Incidents", student.account_lock, ""],
        ["Multiple Keyboard/Mouse Incidents", student.multiple_keyboard_mouse, ""],
    ], colWidths=[4 * inch, 1 * inch, 3 * inch])
    observations_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F81BD")),  # Blue header
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#DCE6F1")),  # Light blue rows
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    content.append(observations_table)

    # Build PDF
    doc.build(content)

    # Ensure PDF exists before sending
    if not os.path.exists(pdf_path):
        return jsonify({'error': f'PDF generation failed for {roll_number}'}), 500

    # Send the file with the desired name
    return send_file(pdf_path, as_attachment=True, download_name="Fact Finding Report.pdf")

if __name__ == '__main__':
    app.run(debug=True)
