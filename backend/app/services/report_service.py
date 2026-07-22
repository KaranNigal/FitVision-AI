import io
import csv
import pandas as pd
from typing import List
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from app.models.models import Workout, WorkoutExercise

def generate_workout_csv(workouts: List[Workout]) -> bytes:
    """
    Generate CSV file of all workout details.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write Headers
    writer.writerow([
        "Workout ID", "Date", "Duration (sec)", "Calories Burned", 
        "Workout Score", "Difficulty", "Exercise Name", 
        "Variation", "Total Reps", "Valid Reps", "Invalid Reps", 
        "Avg Speed (sec)", "Best Streak"
    ])
    
    for workout in workouts:
        date_str = workout.date.strftime("%Y-%m-%d %H:%M:%S") if workout.date else ""
        for ex in workout.exercises:
            writer.writerow([
                workout.id,
                date_str,
                workout.duration_seconds,
                workout.calories_burned,
                workout.score,
                workout.difficulty,
                ex.exercise_name,
                ex.variation,
                ex.total_reps,
                ex.valid_reps,
                ex.invalid_reps,
                ex.average_speed_seconds,
                ex.best_streak
            ])
            
    return output.getvalue().encode("utf-8")


def generate_workout_excel(workouts: List[Workout]) -> bytes:
    """
    Generate professional multi-sheet Excel file of workout summary and details.
    """
    summary_data = []
    exercise_data = []
    
    for w in workouts:
        date_str = w.date.strftime("%Y-%m-%d %H:%M:%S") if w.date else ""
        summary_data.append({
            "Workout ID": w.id,
            "Date": date_str,
            "Duration (Min)": round(w.duration_seconds / 60, 2),
            "Calories Burned": w.calories_burned,
            "Workout Score (%)": w.score,
            "Difficulty": w.difficulty,
            "Notes": w.notes or ""
        })
        
        for ex in w.exercises:
            exercise_data.append({
                "Workout ID": w.id,
                "Exercise": ex.exercise_name,
                "Variation": ex.variation,
                "Total Reps": ex.total_reps,
                "Valid Reps": ex.valid_reps,
                "Invalid Reps": ex.invalid_reps,
                "Accuracy (%)": round((ex.valid_reps / ex.total_reps * 100) if ex.total_reps > 0 else 0.0, 1),
                "Avg Speed (Sec/Rep)": round(ex.average_speed_seconds, 2),
                "Best Streak": ex.best_streak
            })

    df_summary = pd.DataFrame(summary_data)
    df_exercises = pd.DataFrame(exercise_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name="Workout Summary", index=False)
        df_exercises.to_excel(writer, sheet_name="Exercise Logs", index=False)
        
    return output.getvalue()


def generate_workout_pdf(user_name: str, workouts: List[Workout]) -> bytes:
    """
    Generate high-quality PDF report with ReportLab.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        textColor=colors.HexColor('#1E293B'),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=30
    )
    
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.HexColor('#0F172A'),
        spaceBefore=15,
        spaceAfter=10
    )
    
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#334155')
    )
    
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=cell_style,
        fontName='Helvetica-Bold'
    )

    story = []
    
    # Header Section
    story.append(Paragraph("FitVision AI Analytics Report", title_style))
    story.append(Paragraph(f"Athlete: {user_name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Summary Metrics Calculation
    total_workouts = len(workouts)
    total_duration = sum(w.duration_seconds for w in workouts)
    total_calories = sum(w.calories_burned for w in workouts)
    avg_score = int(sum(w.score for w in workouts) / total_workouts) if total_workouts > 0 else 0
    
    summary_data = [
        [
            Paragraph("Total Workouts", cell_bold),
            Paragraph("Total Active Time", cell_bold),
            Paragraph("Total Calories", cell_bold),
            Paragraph("Average Score", cell_bold)
        ],
        [
            Paragraph(str(total_workouts), cell_style),
            Paragraph(f"{round(total_duration / 60, 1)} Mins", cell_style),
            Paragraph(f"{round(total_calories, 0)} kcal", cell_style),
            Paragraph(f"{avg_score}%", cell_style)
        ]
    ]
    
    summary_table = Table(summary_data, colWidths=[120, 140, 130, 120])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F1F5F9')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
    ]))
    
    story.append(Paragraph("Overall Performance Summary", section_style))
    story.append(summary_table)
    story.append(Spacer(1, 20))
    
    # Detailed Workout Log Table
    story.append(Paragraph("Detailed Workout Logs", section_style))
    
    log_headers = [
        Paragraph("Date", cell_bold),
        Paragraph("Exercises Details", cell_bold),
        Paragraph("Duration", cell_bold),
        Paragraph("Calories", cell_bold),
        Paragraph("Score", cell_bold)
    ]
    
    log_table_data = [log_headers]
    
    for w in workouts:
        date_str = w.date.strftime("%b %d, %Y") if w.date else ""
        ex_details = []
        for ex in w.exercises:
            acc = round((ex.valid_reps / ex.total_reps * 100) if ex.total_reps > 0 else 0.0, 0)
            ex_details.append(f"{ex.exercise_name} ({ex.variation}): {ex.valid_reps} Reps - {acc}% Acc")
            
        ex_paragraph = Paragraph("<br/>".join(ex_details) if ex_details else "No exercises logged", cell_style)
        
        log_table_data.append([
            Paragraph(date_str, cell_style),
            ex_paragraph,
            Paragraph(f"{round(w.duration_seconds / 60, 1)}m", cell_style),
            Paragraph(f"{int(w.calories_burned)} kcal", cell_style),
            Paragraph(f"{w.score}%", cell_style)
        ])
        
    log_table = Table(log_table_data, colWidths=[90, 240, 60, 60, 60])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F8FAFC')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    
    story.append(log_table)
    
    # Build Document
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
