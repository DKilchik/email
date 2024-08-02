import smtplib
import os
import argparse

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tools.html_render import HTML

parser = argparse.ArgumentParser(description="cmd parameters",
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# parser.add_argument("-s", "--sender", action="store", default="noreply.jenkins@orange.sk", help="email sender")
# parser.add_argument("-r", "--receiver", action="store", default="dmitri.cilcic@orange.com, egor.iacovlev@orange.com, daniel1.vasek@orange.com",help="email receivers, comma separated list")
parser.add_argument("-sb", "--subject", action="store", default="Test execution report", help="email subject")
parser.add_argument("-t", "--title", action="store", default="E-Care2", help="email title")
parser.add_argument("-p", "--pack", action="store", default="Smoke pack", help="testing pack")
# parser.add_argument("-e", "--env", action="store", help="Environment")

args = parser.parse_args()
config = vars(args)

sender_email = config["sender"]
recipients = config["receiver"].split(",")

message = MIMEMultipart("alternative")
message["Subject"] = config["subject"]
message["From"] = sender_email
message["To"] = ", ".join(recipients)

root = os.path.dirname(os.path.abspath(__file__))
template = os.path.join(root, 'static', 'template.html')
output = os.path.join(root, 'static', 'index.html')


html = HTML(template=template,
            output=output,
            title=config["title"],
            pack_name=config["pack"],
            features=features,
            total=total,
            failed=failed,
            tags=tags,
            features_stat=features_stat,
            started_at=started_at,
            finished_at=finished_at,
            env=env
            ).render()

content = MIMEText(html, 'html')

message.attach(content)

with smtplib.SMTP("virtsmtpgateway.ux.mobistar.be", 25) as server:
    server.sendmail(sender_email, recipients, message.as_string())
