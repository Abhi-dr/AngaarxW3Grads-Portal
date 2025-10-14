from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from accounts.views import logout as account_logout
from django.db.models import Q
from accounts.models import Instructor, Student
from student.models import Notification, Anonymous_Message, Feedback
from practice.models import Sheet, Submission, Question
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
import pandas as pd
import io


# ======================================== Instructor ======================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def index(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    latest_sheet = Sheet.objects.latest('id')
    
    # get the total number of submissions happened today only
    today = datetime.date.today()
    total_submissions_today = Submission.objects.filter(submitted_at__date=today).count()
    
    parameters = {
        "instructor": instructor,
        "latest_sheet": latest_sheet,
    }
    
    return render(request, "instructor/index.html", parameters)
    

# ========================================= MY PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def instructor_profile(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    parameters = {
        "instructor": instructor
    }
    
    return render(request, "instructor/profile/instructor_profile.html", parameters)

# ========================================= EDIT PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def edit_instructor_profile(request):
    
    instructor = Instructor.objects.get(id=request.user.id)
    
    if request.method == "POST":
        instructor.first_name = request.POST.get("first_name")
        instructor.last_name = request.POST.get("last_name")
        instructor.email = request.POST.get("email")
        instructor.college = request.POST.get("college")
        instructor.gender = request.POST.get("gender")
        instructor.linkedin_id = request.POST.get("linkedin_id")
        
        if request.POST.get("dob"):
            instructor.dob = request.POST.get("dob")         
        
        instructor.save()
        
        messages.success(request, "Profile updated successfully!")
        
        return redirect("instructor_profile")
    
    parameters = {
        "instructor": instructor
    }
    
    return render(request, "instructor/profile/edit_instructor_profile.html", parameters)



# ========================================= UPLOAD PROFILE =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def upload_instructor_profile(request):

    if request.method == 'POST':

        instructor = Instructor.objects.get(id=request.user.id)

        instructor.profile_pic = request.FILES['profile_pic']
        
        if instructor.profile_pic.size > 5242880:
            messages.error(request, 'Profile Picture size should be less than 5MB')
            return redirect('instructor_profile')
        
        instructor.save()

        messages.success(request, 'Profile Picture Updated Successfully')

        return redirect('instructor_profile')
    

# ========================================= CHANGE PASSWORD =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def change_instructor_password(request):
        
    instructor = Instructor.objects.get(id=request.user.id)
    
    if instructor.check_password(request.POST.get("old_password")):
        
        if request.POST.get("new_password") == request.POST.get("confirm_password"):
            
            instructor.set_password(request.POST.get("new_password"))
            instructor.save()
            
            messages.success(request, "Password changed successfully! Please login Again!")
            
            return account_logout(request)
        
        else:
            messages.error(request, "New password and confirm password do not match!")
            return redirect("instructor_profile")
    
    else:
        messages.error(request, "Old password is incorrect!")
        return redirect("instructor_profile")


# ========================================= ATTENDANCE VISUALIZER =========================================

@login_required(login_url='login')
@staff_member_required(login_url='login')
def attendance_visualizer(request):
    """Attendance visualizer view for instructors"""
    instructor = Instructor.objects.get(id=request.user.id)
    
    parameters = {
        "instructor": instructor
    }
    
    return render(request, "instructor/attendance_visualizer.html", parameters)

@csrf_exempt
@login_required(login_url='login')
@staff_member_required(login_url='login')
def get_predefined_sheets(request):
    """Get predefined Google Sheets URLs for attendance visualization"""
    try:
        # Define your predefined Google Sheets here
        # Replace these with your actual Google Sheets URLs
        predefined_sheets = [
            {
                'id': 1,
                'name': 'KCC - Section A1',
                'url': 'https://docs.google.com/spreadsheets/d/1qlTzQCKiXI-bUnPXVNTQPDw1jeVg56HTOQ-VEtM7DUI/edit?usp=sharing',
            },
            {
                'id': 2,
                'name': 'KCC - Section A2',
                'url': 'https://docs.google.com/spreadsheets/d/1xXUmsOCobC-WipNCGARxHg8R9dNWM4zm8yfGvlAPSOQ/edit?usp=sharing'
            },
            {
                'id': 3,
                'name': 'KCC - Section A3',
                'url': 'https://docs.google.com/spreadsheets/d/1GmkzQmNAFwpNbN2PJ8RLs2cp_i_e5xiB3Sn5kkXJpso/edit?usp=sharing'
            }
        ]
        
        return JsonResponse({
            'success': True,
            'sheets': predefined_sheets
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error fetching predefined sheets: {str(e)}'
        })

@csrf_exempt
@login_required(login_url='login')
@staff_member_required(login_url='login')
def process_attendance_excel(request):
    """Process Excel file for attendance visualization"""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            excel_file = request.FILES['excel_file']
            file_name = excel_file.name.lower()
            
            # Read the file based on extension
            if file_name.endswith('.csv'):
                df = pd.read_csv(excel_file)
            elif file_name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(excel_file)
            else:
                return JsonResponse({'success': False, 'error': 'Invalid request'})

            # Get column names
            columns = df.columns.tolist()
            
            # Identify date columns (columns that are not in the standard student info columns)
            standard_columns = ['Sr. No', 'Name', 'Roll Number', 'Phone Number', 'Email']
            date_columns = [col for col in columns if col not in standard_columns]
            
            # Process student data
            students = []
            for _, row in df.iterrows():
                student = {
                    'sr_no': str(row.get('Sr. No', '')),
                    'name': str(row.get('Name', '')),
                    'roll_number': str(row.get('Roll Number', '')),
                    'phone_number': str(row.get('Phone Number', '')),
                    'email': str(row.get('Email', '')),
                    'attendance': {}
                }
                
                # Process attendance for each date
                for date_col in date_columns:
                    attendance_value = str(row.get(date_col, '')).upper()
                    student['attendance'][date_col] = {
                        'present': attendance_value == 'P',
                        'absent': attendance_value == 'A'
                    }
                
                students.append(student)
            
            # Calculate statistics
            total_students = len(students)
            total_present = 0
            total_absent = 0
            
            # Calculate date-wise statistics
            date_stats = {}
            for date_col in date_columns:
                present_count = sum(1 for student in students if student['attendance'][date_col]['present'])
                absent_count = sum(1 for student in students if student['attendance'][date_col]['absent'])
                total_count = present_count + absent_count
                
                date_stats[date_col] = {
                    'present': present_count,
                    'absent': absent_count,
                    'total': total_count,
                    'attendance_percentage': round((present_count / total_count * 100), 2) if total_count > 0 else 0
                }
                
                total_present += present_count
                total_absent += absent_count
            
            # Calculate overall statistics
            total_days = len(date_columns)
            overall_percentage = round((total_present / (total_present + total_absent) * 100), 2) if (total_present + total_absent) > 0 else 0
            
            response_data = {
                'success': True,
                'students': students,
                'date_columns': date_columns,
                'date_stats': date_stats,
                'statistics': {
                    'total_students': total_students,
                    'total_present': total_present,
                    'total_absent': total_absent,
                    'overall_percentage': overall_percentage,
                    'total_days': total_days
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing Excel file: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
@login_required(login_url='login')
@staff_member_required(login_url='login')
def process_google_sheets(request):
    """Process Google Sheets data for attendance visualization"""
    if request.method == 'POST':
        sheets_url = request.POST.get('sheets_url')
        
        if not sheets_url:
            return JsonResponse({'success': False, 'error': 'Please provide a Google Sheets URL'})
        
        try:
            return fetch_sheet_data_from_url(sheets_url)
                
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error processing Google Sheets: {str(e)}'})

def fetch_sheet_data_from_url(sheets_url):
    """Fetch data directly from Google Sheets URL"""
    import requests
    from io import StringIO
    import re
    
    try:
        # Convert various Google Sheets URL formats to CSV export URL
        csv_url = None
        
        if '/spreadsheets/d/' in sheets_url:
            # Extract sheet ID and GID if present
            sheet_id = sheets_url.split('/spreadsheets/d/')[1].split('/')[0]
            
            # Check if URL has a specific GID
            gid_match = re.search(r'[#&]gid=(\d+)', sheets_url)
            if gid_match:
                gid = gid_match.group(1)
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            else:
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        elif 'docs.google.com' in sheets_url and 'key=' in sheets_url:
            # Legacy format
            sheet_id = sheets_url.split('key=')[1].split('&')[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid Google Sheets URL format'})
        
        # Fetch CSV data
        response = requests.get(csv_url, timeout=10)
        
        if response.status_code != 200:
            return JsonResponse({
                'success': False, 
                'error': 'Unable to access Google Sheet. Please ensure it is shared with "Anyone with the link can view".'
            })
        
        if not response.text or len(response.text.strip()) == 0:
            return JsonResponse({
                'success': False, 
                'error': 'The Google Sheet appears to be empty.'
            })
        
        # Parse CSV data
        try:
            df = pd.read_csv(StringIO(response.text))
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'Error parsing sheet data: {str(e)}'})
        
        if df.empty:
            return JsonResponse({'success': False, 'error': 'The sheet contains no data rows.'})
        
        # Process data
        columns = df.columns.tolist()
        standard_columns = ['Sr. No', 'Name', 'Roll Number', 'Phone Number', 'Email']
        date_columns = [col for col in columns if col not in standard_columns]
        
        # Process student data
        students = []
        for _, row in df.iterrows():
            student = {
                'sr_no': str(row.get('Sr. No', '')),
                'name': str(row.get('Name', '')),
                'roll_number': str(row.get('Roll Number', '')),
                'phone_number': str(row.get('Phone Number', '')),
                'email': str(row.get('Email', '')),
                'attendance': {}
            }
            
            # Process attendance for each date
            for date_col in date_columns:
                attendance_value = str(row.get(date_col, '')).upper()
                student['attendance'][date_col] = {
                    'present': attendance_value == 'P',
                    'absent': attendance_value == 'A'
                }
            
            students.append(student)
        
        # Calculate statistics
        total_students = len(students)
        total_present = 0
        total_absent = 0
        
        # Calculate date-wise statistics
        date_stats = {}
        for date_col in date_columns:
            present_count = sum(1 for student in students if student['attendance'][date_col]['present'])
            absent_count = sum(1 for student in students if student['attendance'][date_col]['absent'])
            total_count = present_count + absent_count
            
            date_stats[date_col] = {
                'present': present_count,
                'absent': absent_count,
                'total': total_count,
                'attendance_percentage': round((present_count / total_count * 100), 2) if total_count > 0 else 0
            }
            
            total_present += present_count
            total_absent += absent_count
        
        # Calculate overall statistics
        total_days = len(date_columns)
        overall_percentage = round((total_present / (total_present + total_absent) * 100), 2) if (total_present + total_absent) > 0 else 0
        
        response_data = {
            'success': True,
            'students': students,
            'date_columns': date_columns,
            'date_stats': date_stats,
            'statistics': {
                'total_students': total_students,
                'total_present': total_present,
                'total_absent': total_absent,
                'overall_percentage': overall_percentage,
                'total_days': total_days
            }
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error fetching sheet data: {str(e)}'})

@login_required(login_url='login')
@staff_member_required(login_url='login')
def download_sample_attendance_excel(request):
    """Generate and download a sample Excel file for attendance"""
    from datetime import datetime, timedelta
    
    # Create sample data
    sample_data = {
        'Sr. No': [1, 2, 3, 4, 5],
        'Name': ['John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson', 'David Brown'],
        'Roll Number': ['CS001', 'CS002', 'CS003', 'CS004', 'CS005'],
        'Phone Number': ['9876543210', '9876543211', '9876543212', '9876543213', '9876543214'],
        'Email': ['john@example.com', 'jane@example.com', 'mike@example.com', 'sarah@example.com', 'david@example.com']
    }
    
    # Generate sample dates (last 7 days)
    today = datetime.datetime.now()
    for i in range(7):
        date = today - timedelta(days=6-i)
        date_str = date.strftime('%Y-%m-%d')
        # Add sample attendance data (P for Present, A for Absent)
        sample_attendance = ['P', 'P', 'A', 'P', 'P'] if i % 2 == 0 else ['A', 'P', 'P', 'A', 'P']
        sample_data[date_str] = sample_attendance
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="sample_attendance.xlsx"'
    
    # Write to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Attendance', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Attendance']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return response


# ======================================== EXPORT ATTENDANCE PDF WITH CHARTS ========================================

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import base64
from io import BytesIO
import numpy as np

@csrf_exempt
@login_required(login_url='login')
@staff_member_required(login_url='login')
def export_attendance_pdf(request):
    """Export attendance data with charts as PDF"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        # Get the attendance data from the request
        attendance_data = request.POST.get('attendance_data')
        filtered_data = request.POST.get('filtered_data')
        
        if not attendance_data or not filtered_data:
            return JsonResponse({'success': False, 'error': 'Missing attendance data'})
        
        import json
        attendance_data = json.loads(attendance_data)
        filtered_data = json.loads(filtered_data)
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="attendance_report_{datetime.datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        # Create PDF document
        doc = SimpleDocTemplate(response, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        story = []
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#2c3e50')
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#34495e')
        )
        
        # Title
        story.append(Paragraph("📊 Attendance Analysis Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary Statistics
        total_students = len(filtered_data)
        total_present = sum(len([att for att in student['attendance'].values() if att.get('present', False)]) for student in filtered_data)
        total_absent = sum(len([att for att in student['attendance'].values() if att.get('absent', False)]) for student in filtered_data)
        total_entries = total_present + total_absent
        overall_percentage = (total_present / total_entries * 100) if total_entries > 0 else 0
        
        summary_data = [
            ['📈 Summary Statistics', ''],
            ['Total Students', str(total_students)],
            ['Total Present Entries', str(total_present)],
            ['Total Absent Entries', str(total_absent)],
            ['Overall Attendance %', f'{overall_percentage:.2f}%'],
            ['Report Generated', datetime.datetime.now().strftime('%B %d, %Y at %I:%M %p')]
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Generate Charts
        plt.style.use('seaborn-v0_8')
        fig_width, fig_height = 10, 6
        
        # 1. Attendance Trend Chart
        if attendance_data.get('date_columns'):
            dates = attendance_data['date_columns']
            present_counts = []
            absent_counts = []
            
            for date in dates:
                date_stats = attendance_data.get('date_stats', {}).get(date, {})
                present_counts.append(date_stats.get('present', 0))
                absent_counts.append(date_stats.get('absent', 0))
            
            plt.figure(figsize=(fig_width, fig_height))
            plt.plot(dates, present_counts, marker='o', linewidth=3, markersize=8, color='#27ae60', label='Present')
            plt.plot(dates, absent_counts, marker='s', linewidth=3, markersize=8, color='#e74c3c', label='Absent')
            plt.title('📈 Daily Attendance Trend', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Date', fontsize=12)
            plt.ylabel('Number of Students', fontsize=12)
            plt.legend(fontsize=12)
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            # Save chart to memory
            chart_buffer = BytesIO()
            plt.savefig(chart_buffer, format='png', dpi=300, bbox_inches='tight')
            chart_buffer.seek(0)
            chart_image = Image(chart_buffer, width=6*inch, height=3.6*inch)
            
            story.append(Paragraph("📈 Daily Attendance Trends", heading_style))
            story.append(chart_image)
            story.append(Spacer(1, 20))
            plt.close()
        
        # 2. Attendance Distribution Pie Chart
        attendance_categories = {'Excellent (90%+)': 0, 'Good (75-89%)': 0, 'Average (60-74%)': 0, 'Poor (<60%)': 0}
        
        for student in filtered_data:
            present_days = len([att for att in student['attendance'].values() if att.get('present', False)])
            total_days = len([att for att in student['attendance'].values() if att.get('present', False) or att.get('absent', False)])
            percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            if percentage >= 90:
                attendance_categories['Excellent (90%+)'] += 1
            elif percentage >= 75:
                attendance_categories['Good (75-89%)'] += 1
            elif percentage >= 60:
                attendance_categories['Average (60-74%)'] += 1
            else:
                attendance_categories['Poor (<60%)'] += 1
        
        plt.figure(figsize=(8, 8))
        labels = list(attendance_categories.keys())
        values = list(attendance_categories.values())
        colors_pie = ['#27ae60', '#f39c12', '#e67e22', '#e74c3c']
        
        plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors_pie, 
                explode=(0.05, 0.05, 0.05, 0.05), shadow=True)
        plt.title('🎯 Student Performance Distribution', fontsize=16, fontweight='bold', pad=20)
        
        pie_buffer = BytesIO()
        plt.savefig(pie_buffer, format='png', dpi=300, bbox_inches='tight')
        pie_buffer.seek(0)
        pie_image = Image(pie_buffer, width=5*inch, height=5*inch)
        
        story.append(Paragraph("🎯 Performance Distribution", heading_style))
        story.append(pie_image)
        story.append(PageBreak())
        plt.close()
        
        # 3. Top 10 Students Bar Chart
        student_percentages = []
        for student in filtered_data:
            present_days = len([att for att in student['attendance'].values() if att.get('present', False)])
            total_days = len([att for att in student['attendance'].values() if att.get('present', False) or att.get('absent', False)])
            percentage = (present_days / total_days * 100) if total_days > 0 else 0
            student_percentages.append((student['name'], percentage))
        
        # Sort and get top 10
        student_percentages.sort(key=lambda x: x[1], reverse=True)
        top_10 = student_percentages[:10]
        
        if top_10:
            names = [s[0][:15] + '...' if len(s[0]) > 15 else s[0] for s in top_10]
            percentages = [s[1] for s in top_10]
            
            plt.figure(figsize=(12, 8))
            colors_bar = ['#27ae60' if p >= 90 else '#f39c12' if p >= 75 else '#e67e22' if p >= 60 else '#e74c3c' for p in percentages]
            bars = plt.barh(names, percentages, color=colors_bar)
            
            plt.title('🏆 Top 10 Students by Attendance', fontsize=16, fontweight='bold', pad=20)
            plt.xlabel('Attendance Percentage (%)', fontsize=12)
            plt.xlim(0, 100)
            
            # Add percentage labels on bars
            for bar, percentage in zip(bars, percentages):
                plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                        f'{percentage:.1f}%', va='center', fontsize=10)
            
            plt.tight_layout()
            
            top10_buffer = BytesIO()
            plt.savefig(top10_buffer, format='png', dpi=300, bbox_inches='tight')
            top10_buffer.seek(0)
            top10_image = Image(top10_buffer, width=7*inch, height=5*inch)
            
            story.append(Paragraph("🏆 Top Performers", heading_style))
            story.append(top10_image)
            story.append(Spacer(1, 30))
            plt.close()
        
        # 4. Detailed Student Table
        story.append(Paragraph("📋 Detailed Student Data", heading_style))
        
        # Prepare table data
        table_data = [['Rank', 'Student Name', 'Present Days', 'Absent Days', 'Attendance %']]
        
        for idx, student in enumerate(filtered_data, 1):  # Show all students
            present_days = len([att for att in student['attendance'].values() if att.get('present', False)])
            absent_days = len([att for att in student['attendance'].values() if att.get('absent', False)])
            total_days = present_days + absent_days
            percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            table_data.append([
                str(idx),
                student['name'][::] + '...' if len(student['name']) > 25 else student['name'],
                str(present_days),
                str(absent_days),
                f'{percentage:.1f}%'
            ])
        
        detail_table = Table(table_data, colWidths=[0.8*inch, 3*inch, 1*inch, 1*inch, 1*inch])
        detail_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(detail_table)
        
        # Footer
        story.append(Spacer(1, 30))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            textColor=colors.grey
        )
        story.append(Paragraph(f"📋 Generated by Angaar Attendance Visualizer | {datetime.datetime.now().strftime('%B %d, %Y')}", footer_style))
        
        # Build PDF
        doc.build(story)
        
        return response
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
