import csv
import os
import smtplib
from email.message import EmailMessage


def load_participants(csv_file):
    """Load participant email addresses from a CSV file."""
    participants = []
    with open(csv_file, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get("email")
            if email:
                participants.append(email)
    return participants


def load_summary(summary_file):
    """Read summary text from a file."""
    with open(summary_file, "r", encoding="utf-8") as f:
        return f.read()


def send_email(to_address, subject, body, smtp_server, smtp_port, username, password, from_address=None):
    """Send an email using SMTP_SSL."""
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_address or username
    msg["To"] = to_address
    msg.set_content(body)

    with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
        server.login(username, password)
        server.send_message(msg)


def send_summary_to_all(participants_csv, summary_file):
    summary_text = load_summary(summary_file)
    participants = load_participants(participants_csv)

    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    from_address = os.getenv("FROM_EMAIL", username)

    subject = "Course Summary"

    for email in participants:
        send_email(email, subject, summary_text, smtp_server, smtp_port, username, password, from_address)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Send course summary emails to all participants.")
    parser.add_argument("participants_csv", help="CSV file containing participant data with an 'email' column")
    parser.add_argument("summary_file", help="Text file containing the course summary")
    args = parser.parse_args()

    send_summary_to_all(args.participants_csv, args.summary_file)
