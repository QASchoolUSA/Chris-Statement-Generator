from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
import os
from datetime import datetime

import json
import locale

# Set locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    locale.setlocale(locale.LC_ALL, '')

class PDFGenerator:
    def __init__(self, filename="statement.pdf"):
        self.filename = filename
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter

    def format_currency(self, amount):
        if amount < 0:
            return f"({locale.currency(abs(amount), grouping=True)})"
        return locale.currency(amount, grouping=True)

    def _header_footer(self, canvas, doc):
        # Save canvas state
        canvas.saveState()
        
        # Header content
        # Logo placeholder (Top Left)
        # Assuming logo is approx 2 inch wide
        logo_path = "logo.png"  # User needs to provide this
        if os.path.exists(logo_path):
            try:
                canvas.drawImage(logo_path, 30, self.height - 100, width=2*inch, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        else:
            # Draw placeholder
            canvas.setStrokeColor(colors.black)
            canvas.rect(30, self.height - 100, 2*inch, 0.8*inch)
            canvas.setFont("Helvetica", 10)
            canvas.drawString(40, self.height - 60, "SPF Transportation LLC (Logo)")

        # Company Address (Below Logo)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(30, self.height - 120, "8046 S Carnaby CT Hanover Park, IL 60133")
        canvas.drawString(30, self.height - 130, "Phone #: (312)690-3717")

        # Statement Info (Top Right)
        # Use data if available attached to doc, else default
        statement_data = getattr(doc, 'statement_data', {})
        date_str = statement_data.get('date', "12/12/2025")
        truck_num = statement_data.get('truck_number', "196")

        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawRightString(self.width - 30, self.height - 50, "Statement")
        canvas.setFont("Helvetica", 12)
        canvas.drawRightString(self.width - 30, self.height - 65, "FITRIGHT LOGISTICS LLC")
        canvas.drawRightString(self.width - 30, self.height - 80, f"Date: {date_str}")
        canvas.drawRightString(self.width - 30, self.height - 95, f"Truck # {truck_num}")

        # Footer
        canvas.setFont("Helvetica", 8)
        canvas.drawString(30, 30, "SPF Transportation LLC")
        canvas.drawString(30, 20, datetime.now().strftime("%12/%11/%25 %H:%M")) # Example format
        
        canvas.drawCentredString(self.width / 2, 30, "ProTransport Trucking Software")
        canvas.drawCentredString(self.width / 2, 20, "www.pro-transport.com")
        
        canvas.drawRightString(self.width - 30, 20, f"Page {doc.page} Of 1") # Assuming 1 page for now

        canvas.restoreState()

    def generate(self, data):
        doc = SimpleDocTemplate(self.filename, pagesize=letter,
                                rightMargin=30, leftMargin=30,
                                topMargin=150, bottomMargin=50)
        
        # Pass statement info to doc for header
        doc.statement_data = data.get('statement_info', {})

        elements = []
        
        # Styles
        normal_style = self.styles["Normal"]
        bold_style = ParagraphStyle('Bold', parent=normal_style, fontName='Helvetica-Bold', fontSize=10)
        
        # Recipient Info
        recipient = data.get('recipient', {})
        elements.append(Paragraph(f"<b>{recipient.get('name', '')}</b>", normal_style))
        elements.append(Paragraph(f"<b>{recipient.get('address_line_1', '')}</b>", normal_style))
        elements.append(Paragraph(f"<b>{recipient.get('address_line_2', '')}</b>", normal_style))
        elements.append(Spacer(1, 20))

        # Trips Section
        elements.append(Paragraph("<b>Trips :</b>", bold_style))
        elements.append(Spacer(1, 5))
        
        trip_headers = ["Date", "Trip #", "Route", "Description", "Quantity", "Rate", "Amount"]
        
        # Process Trips Data
        processed_trips = [trip_headers]
        total_trips_amount = 0.0
        
        for trip in data.get('trips', []):
            amount = float(trip.get('amount', 0))
            total_trips_amount += amount
            processed_trips.append([
                trip.get('date', ''),
                trip.get('trip_number', ''),
                trip.get('route', ''),
                trip.get('description', ''),
                f"{float(trip.get('quantity', 0)):.2f}",
                f"{float(trip.get('rate', 0)):.4f}",
                self.format_currency(amount)
            ])

        col_widths = [50, 60, 150, 120, 50, 50, 60]
        
        t_trips = Table(processed_trips, colWidths=col_widths)
        t_trips.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (3, -1), 'LEFT'), # Align Route and Description Left
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(t_trips)
        
        # Trips Total
        t_trip_total = Table([["Total:", self.format_currency(total_trips_amount)]], colWidths=[sum(col_widths)-70, 70])
        t_trip_total.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'), # Amount center or right
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.red),
            ('GRID', (1, 0), (1, 0), 0.5, colors.black), # Box around amount
        ]))
        elements.append(t_trip_total)
        elements.append(Spacer(1, 10))

        # Scheduled Deductions Section
        elements.append(Paragraph("<b>Scheduled Deductions :</b>", bold_style))
        elements.append(Spacer(1, 5))
        
        deduction_headers = ["Description", "Date", "Amount"]
        processed_deductions = [deduction_headers]
        total_deductions_amount = 0.0
        
        for ded in data.get('deductions', []):
            amount = float(ded.get('amount', 0))
            total_deductions_amount += amount
            processed_deductions.append([
                ded.get('description', ''),
                ded.get('date', ''),
                self.format_currency(amount)
            ])
        
        # Deductions width
        ded_col_widths = [sum(col_widths)-110, 50, 60]
        
        t_deductions = Table(processed_deductions, colWidths=ded_col_widths)
        t_deductions.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(t_deductions)
        
        # Deductions Total
        t_ded_total = Table([["Total:", self.format_currency(total_deductions_amount)]], colWidths=[sum(ded_col_widths)-70, 70])
        t_ded_total.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.red),
            ('GRID', (1, 0), (1, 0), 0.5, colors.black),
        ]))
        elements.append(t_ded_total)
        elements.append(Spacer(1, 20))

        # Summary Section
        ytd_net = data.get('ytd', {}).get('net', 0.0)
        ytd_gross = data.get('ytd', {}).get('gross', 0.0)
        check_amount = total_trips_amount + total_deductions_amount

        t_summary = Table([
            [f"Total Net Year-To-Date : ", self.format_currency(ytd_net), "", ""],
            [f"Total Gross Year-To-Date : ", self.format_currency(ytd_gross), "Check Amount:", self.format_currency(check_amount)]
        ], colWidths=[150, 100, sum(col_widths)-150-100-70, 70])
        
        t_summary.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (1, 0), (1, 1), colors.blue), # YTD Values Blue
            ('TEXTCOLOR', (3, 1), (3, 1), colors.red), # Check Amount Red
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'), # Label Right aligned
            ('ALIGN', (1, 0), (1, -1), 'LEFT'), # Value Left aligned
            ('ALIGN', (2, 1), (2, 1), 'RIGHT'), # "Check Amount:"
            ('ALIGN', (3, 1), (3, 1), 'CENTER'), # Amount
            ('GRID', (3, 1), (3, 1), 0.5, colors.black), # Box around check amount
        ]))
        
        elements.append(t_summary)
        
        # Add date range at bottom left if needed
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("12.01-12.07", normal_style))

        # Build PDF
        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

if __name__ == "__main__":
    # Load data from json file if exists, else use mock
    data_file = "data.json"
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            data = json.load(f)
    else:
        # Fallback Mock Data
        data = {
            "trips": [],
            "deductions": [],
            "ytd": {"net": 0, "gross": 0}
        }
    
    gen = PDFGenerator("statement.pdf")
    gen.generate(data)
    print("PDF Generated: statement.pdf")
