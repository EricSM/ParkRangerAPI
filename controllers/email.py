import smtplib, ssl
from controllers.report import Report, ReportHandler
from controllers.user import UserHandler

class EmailHandler:
    def __init__(self):
        self.context = None
        self.report_handler = ReportHandler()
        self.user_handler = UserHandler()

    def send_all_emails(self):
        print("Sending all emails...")
        users = self.user_handler.get_all_users()

        for user in users:
            reports = self.report_handler.get_reports_filter(user.park_id, approvedStatus = 0)
            if len(reports) > 0:
                message = self.construct_message_body(reports)
                self.establish_and_send(user.email, message)

        print("Done!")

    def construct_message_body(self, reports):
        message = """\
Subject: ParkRanger.info Daily Report

The following reports are currently awaiting approval.

{}
            """.format(self.reports_list_to_string(reports))

        return message

    def reports_list_to_string(self, reports):
        report_str = ""

        for report in reports:
            report_str += report.loc_name + "\n"
            report_str += report.description + "\n"
            report_str += "Location: " +  str(report.loc_lat) + " (lat), " + str(report.loc_long) + " (lon)\n\n"
        
        return report_str


    def establish_and_send(self, recipient, email_body):
        print("Establishing smtp connection...")
        smtp_server = "smtp.gmail.com"
        port = 587  # For starttls
        sender_email = "parkranger.inf@gmail.com"
        password = "ParkWatch123!"

        # Create a secure SSL context
        self.context = ssl.create_default_context()

        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(smtp_server,port)
            server.ehlo() # Can be omitted
            server.starttls(context=self.context) # Secure the connection
            server.ehlo() # Can be omitted
            server.login(sender_email, password)
            self.send_email(server, recipient, email_body)

        except Exception as e:
            # Print any error messages to stdout
            print(e)
        finally:
            server.quit()

    def send_email(self, server, recipient, email_body):
        print("Sending email...")
        sender_email = "parkranger.inf@gmail.com"  # Enter your address
        receiver_email = recipient  # Enter receiver address
        
        server.sendmail(sender_email, receiver_email, email_body)
