#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)


class BugReportHandler:
    def __init__(self):
        # Email configuration - You can set these as environment variables for security
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "pythonwebide@gmail.com")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")  # App-specific password for Gmail
        self.recipient_email = "sa9082@nyu.edu"

    def send_bug_report(self, report_data):
        """
        Send bug report email to the administrator

        Args:
            report_data (dict): Bug report data from frontend

        Returns:
            dict: Response with success status and ticket ID
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = (
                f"[Bug Report] {report_data.get('ticketId', 'Unknown')} - {report_data.get('title', 'No Title')}"
            )
            msg["From"] = self.sender_email
            msg["To"] = self.recipient_email
            msg["Reply-To"] = report_data.get("email", "noreply@example.com")

            # Create the HTML content
            html_body = self._create_html_body(report_data)

            # Create the plain text version
            text_body = self._create_text_body(report_data)

            # Add parts to message
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            if self.sender_password:  # Only send if password is configured
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls()
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(msg)

                logger.info(f"Bug report sent successfully: {report_data.get('ticketId')}")
            else:
                # For development/testing, just log the report
                logger.warning("SMTP password not configured. Bug report logged but not emailed.")
                logger.info(f"Bug Report: {json.dumps(report_data, indent=2)}")

                # Save to local file as backup
                self._save_to_file(report_data)

            return {
                "success": True,
                "ticketId": report_data.get("ticketId"),
                "message": "Bug report submitted successfully",
            }

        except Exception as e:
            logger.error(f"Failed to send bug report: {str(e)}")
            # Still save to file as backup
            self._save_to_file(report_data)
            return {
                "success": True,  # Return success even if email fails (saved to file)
                "ticketId": report_data.get("ticketId"),
                "message": "Bug report saved (email pending)",
                "error": str(e),
            }

    def _create_html_body(self, report_data):
        """Create HTML formatted email body"""
        timestamp = report_data.get("timestamp", datetime.now().isoformat())

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2 style="color: #333;">Bug Report - Python Web IDE</h2>
                
                <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #555; margin-top: 0;">Ticket Information</h3>
                    <p><strong>Ticket ID:</strong> {report_data.get('ticketId', 'N/A')}</p>
                    <p><strong>Submitted:</strong> {timestamp}</p>
                    <p><strong>Priority:</strong> <span style="color: {'red' if report_data.get('priority') == 'critical' else 'orange' if report_data.get('priority') == 'high' else 'blue'}; font-weight: bold;">{report_data.get('priority', 'medium').upper()}</span></p>
                </div>
                
                <div style="background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #555;">Bug Details</h3>
                    <p><strong>Title:</strong> {report_data.get('title', 'No title provided')}</p>
                    <p><strong>Description:</strong></p>
                    <div style="background: #f9f9f9; padding: 10px; border-left: 3px solid #409eff;">
                        {report_data.get('description', 'No description provided').replace(chr(10), '<br>')}
                    </div>
                </div>
                
                <div style="background: #fff; padding: 15px; border: 1px solid #ddd; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #555;">User Information</h3>
                    <p><strong>Email:</strong> <a href="mailto:{report_data.get('email', 'N/A')}">{report_data.get('email', 'N/A')}</a></p>
                    <p><strong>Browser:</strong> {report_data.get('browser', 'Not specified')}</p>
                    <p><strong>User Agent:</strong> <code style="font-size: 12px;">{report_data.get('userAgent', 'N/A')}</code></p>
                    <p><strong>URL:</strong> <a href="{report_data.get('url', '#')}">{report_data.get('url', 'N/A')}</a></p>
                    <p><strong>IDE Version:</strong> {report_data.get('ideVersion', 'N/A')}</p>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                
                <p style="color: #666; font-size: 12px;">
                    This bug report was automatically generated by the Python Web IDE bug reporting system.
                    Please respond to the user at {report_data.get('email', 'the provided email')} with the ticket ID when resolved.
                </p>
            </body>
        </html>
        """
        return html

    def _create_text_body(self, report_data):
        """Create plain text email body"""
        timestamp = report_data.get("timestamp", datetime.now().isoformat())

        text = f"""
Bug Report - Python Web IDE
===========================

TICKET INFORMATION
------------------
Ticket ID: {report_data.get('ticketId', 'N/A')}
Submitted: {timestamp}
Priority: {report_data.get('priority', 'medium').upper()}

BUG DETAILS
-----------
Title: {report_data.get('title', 'No title provided')}

Description:
{report_data.get('description', 'No description provided')}

USER INFORMATION
----------------
Email: {report_data.get('email', 'N/A')}
Browser: {report_data.get('browser', 'Not specified')}
User Agent: {report_data.get('userAgent', 'N/A')}
URL: {report_data.get('url', 'N/A')}
IDE Version: {report_data.get('ideVersion', 'N/A')}

---
This bug report was automatically generated by the Python Web IDE bug reporting system.
Please respond to the user at {report_data.get('email', 'the provided email')} with the ticket ID when resolved.
        """
        return text

    def _save_to_file(self, report_data):
        """Save bug report to a local file as backup"""
        try:
            # Create bug_reports directory if it doesn't exist
            reports_dir = os.path.join(os.path.dirname(__file__), "..", "bug_reports")
            os.makedirs(reports_dir, exist_ok=True)

            # Create filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bug_report_{report_data.get('ticketId', 'unknown')}_{timestamp}.json"
            filepath = os.path.join(reports_dir, filename)

            # Save report data
            with open(filepath, "w") as f:
                json.dump(report_data, f, indent=2)

            logger.info(f"Bug report saved to file: {filepath}")

        except Exception as e:
            logger.error(f"Failed to save bug report to file: {str(e)}")


# Create a global instance
bug_report_handler = BugReportHandler()


def handle_bug_report(report_data):
    """
    Main function to handle bug reports

    Args:
        report_data (dict): Bug report data from frontend

    Returns:
        dict: Response with success status
    """
    return bug_report_handler.send_bug_report(report_data)
