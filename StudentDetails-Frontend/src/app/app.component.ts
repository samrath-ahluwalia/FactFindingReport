import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { HttpClientModule, HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, HttpClientModule, FormsModule, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'StudentDetails-Frontend';
  rollNumber = '';
  studentDetails: any = null;
  students: any[] = [];
  private baseUrl = 'http://127.0.0.1:5000'; // Backend base URL

  csvFile: File | null = null;
  zipFile: File | null = null;

  constructor(private http: HttpClient) {
    this.getAllStudents(); // Load all students on component init
  }

  onFileSelect(event: any, type: string) {
    const file = event.target.files[0];
    if (type === 'csv') {
      this.csvFile = file;
    } else {
      this.zipFile = file;
    }
  }

  submitFiles() {
    if (!this.csvFile || !this.zipFile) {
      alert('Please select both CSV and ZIP files before submitting.');
      return;
    }
  
    const formData = new FormData();
    formData.append('csv_file', this.csvFile);
    formData.append('zip_file', this.zipFile);
  
    this.http.post(`${this.baseUrl}/upload_csv_zip`, formData).subscribe(
      (res: any) => {
        alert('Files uploaded successfully');
        this.students = res.students; // Update the table with new data
      },
      (err: any) => alert(`Error uploading files: ${err.message}`)
    );
  }
  

  searchStudent() {
    if (!this.rollNumber) {
      this.students = [];
      return;
    }
  
    this.http.get(`${this.baseUrl}/search_student?roll_number=${this.rollNumber}`).subscribe(
      (res: any) => this.students = res,
      (err: any) => console.error('Error fetching student data', err)
    );
  }
  

  getAllStudents() {
    this.http.get(`${this.baseUrl}/get_students`).subscribe(
      (res: any) => this.students = res,
      (err: any) => console.error('Error fetching students', err)
    );
  }

  downloadDoc(rollNumber: string) {
    window.open(`${this.baseUrl}/generate_doc/${rollNumber}`, '_blank');
  }
  
}
