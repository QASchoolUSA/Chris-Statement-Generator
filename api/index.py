from http.server import BaseHTTPRequestHandler
import json
import locale
import io
import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfgen import canvas

# Set locale for currency formatting
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass # Fallback if no locale supported

class PDFGenerator:
    def __init__(self, buffer):
        self.buffer = buffer
        self.styles = getSampleStyleSheet()
        self.width, self.height = letter

    def format_currency(self, amount):
        try:
            if amount < 0:
                return f"({locale.currency(abs(amount), grouping=True)})"
            return locale.currency(amount, grouping=True)
        except:
             return f"${amount:,.2f}"

    def _header_footer(self, canvas, doc):
        canvas.saveState()
        
        # Logo (Top Left)
        # Try to find logo.png in the same directory as the script
        logo_path = os.path.join(os.path.dirname(__file__), 'logo.png')
        
        if os.path.exists(logo_path):
            try:
                # Draw logo - adjusting width/height to fit approx 2 inches wide
                # preserveAspectRatio=True is important
                canvas.drawImage(logo_path, 30, self.height - 110, width=2.5*inch, height=1*inch, preserveAspectRatio=True, mask='auto')
            except Exception as e:
                # Fallback if image fails to load
                canvas.setFont("Helvetica-Bold", 14)
                canvas.drawString(40, self.height - 60, "SPF Transportation LLC")
        else:
            # Fallback if file not found
            canvas.setFont("Helvetica-Bold", 14)
            canvas.drawString(40, self.height - 60, "SPF Transportation LLC")
        
        # Company Address
        canvas.setFont("Helvetica", 8)
        canvas.drawString(30, self.height - 120, "8046 S Carnaby CT Hanover Park, IL 60133")
        canvas.drawString(30, self.height - 130, "Phone #: (312)690-3717")

        # Statement Info
        statement_data = getattr(doc, 'statement_data', {})
        date_str = statement_data.get('date', datetime.now().strftime("%m/%d/%Y"))
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
        canvas.drawString(30, 20, datetime.now().strftime("%m/%d/%y %H:%M"))
        
        canvas.drawCentredString(self.width / 2, 30, "ProTransport Trucking Software")
        canvas.drawCentredString(self.width / 2, 20, "www.pro-transport.com")
        
        canvas.drawRightString(self.width - 30, 20, f"Page {doc.page} Of 1")

        canvas.restoreState()

    def generate(self, data):
        doc = SimpleDocTemplate(self.buffer, pagesize=letter,
                                rightMargin=30, leftMargin=30,
                                topMargin=150, bottomMargin=50)
        
        doc.statement_data = data.get('statement_info', {})

        elements = []
        normal_style = self.styles["Normal"]
        bold_style = ParagraphStyle('Bold', parent=normal_style, fontName='Helvetica-Bold', fontSize=10)
        
        # Recipient Info
        recipient = data.get('recipient', {})
        elements.append(Paragraph(f"<b>{recipient.get('name', 'FITRIGHT LOGISTICS LLC')}</b>", normal_style))
        elements.append(Paragraph(f"<b>{recipient.get('address_line_1', '3374 FLAMBOROUGH DR')}</b>", normal_style))
        elements.append(Paragraph(f"<b>{recipient.get('address_line_2', 'Orlando, FL 32835')}</b>", normal_style))
        elements.append(Spacer(1, 20))

        # Trips Section
        elements.append(Paragraph("<b>Trips :</b>", bold_style))
        elements.append(Spacer(1, 5))
        
        trip_headers = ["Date", "Trip #", "Route", "Description", "Quantity", "Rate", "Amount"]
        processed_trips = [trip_headers]
        total_trips_amount = 0.0
        
        for trip in data.get('trips', []):
            try:
                amount = float(trip.get('amount', 0))
                qty = float(trip.get('quantity', 0))
                rate = float(trip.get('rate', 0))
            except:
                amount = 0.0
                qty = 0.0
                rate = 0.0
                
            total_trips_amount += amount
            processed_trips.append([
                trip.get('date', ''),
                trip.get('trip_number', ''),
                trip.get('route', ''),
                trip.get('description', ''),
                f"{qty:.2f}",
                f"{rate:.4f}",
                self.format_currency(amount)
            ])

        col_widths = [50, 60, 150, 120, 50, 50, 60]
        t_trips = Table(processed_trips, colWidths=col_widths)
        t_trips.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (3, -1), 'LEFT'),
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
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (1, 0), (1, 0), colors.red),
            ('GRID', (1, 0), (1, 0), 0.5, colors.black),
        ]))
        elements.append(t_trip_total)
        elements.append(Spacer(1, 10))

        # Deductions Section
        elements.append(Paragraph("<b>Scheduled Deductions :</b>", bold_style))
        elements.append(Spacer(1, 5))
        
        deduction_headers = ["Description", "Date", "Amount"]
        processed_deductions = [deduction_headers]
        total_deductions_amount = 0.0
        
        for ded in data.get('deductions', []):
            try:
                amount = float(ded.get('amount', 0))
            except:
                amount = 0.0
            total_deductions_amount += amount
            processed_deductions.append([
                ded.get('description', ''),
                ded.get('date', ''),
                self.format_currency(amount)
            ])
        
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
        # YTD values passed from frontend or calculated?
        # Assuming passed or just placeholders. The user said they will provide amounts.
        # We will calculate "Check Amount" dynamically.
        ytd_net = data.get('ytd', {}).get('net', 0.0)
        ytd_gross = data.get('ytd', {}).get('gross', 0.0)
        check_amount = total_trips_amount + total_deductions_amount # Deductions are negative usually? 
        # Note: In the image/logic, deductions amount was ($37.50) which implies negative.
        # If user sends positive number for deduction, we might need to subtract.
        # However, usually in accounting data, if it's a deduction, it might be stored as negative.
        # Let's assume the frontend sends the signed value or we sum them up. 
        # In the previous script I summed them. If the input is negative, it subtracts.
        
        t_summary = Table([
            [f"Total Net Year-To-Date : ", self.format_currency(ytd_net), "", ""],
            [f"Total Gross Year-To-Date : ", self.format_currency(ytd_gross), "Check Amount:", self.format_currency(check_amount)]
        ], colWidths=[150, 100, sum(col_widths)-150-100-70, 70])
        
        t_summary.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (1, 0), (1, 1), colors.blue),
            ('TEXTCOLOR', (3, 1), (3, 1), colors.red),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, 1), 'RIGHT'),
            ('ALIGN', (3, 1), (3, 1), 'CENTER'),
            ('GRID', (3, 1), (3, 1), 0.5, colors.black),
        ]))
        elements.append(t_summary)
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"{datetime.now().strftime('%m.%d')}-{datetime.now().strftime('%m.%d')}", normal_style))

        doc.build(elements, onFirstPage=self._header_footer, onLaterPages=self._header_footer)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        try:
            data = json.loads(body)
        except:
            data = {}

        buffer = io.BytesIO()
        gen = PDFGenerator(buffer)
        gen.generate(data)
        
        pdf_value = buffer.getvalue()
        buffer.close()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/pdf')
        self.send_header('Content-Disposition', 'attachment; filename="statement.pdf"')
        self.end_headers()
        self.wfile.write(pdf_value)

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Send a POST request with JSON data to generate PDF.".encode('utf-8'))
