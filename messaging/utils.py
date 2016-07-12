import smtplib
from email.mime.text import MIMEText
import drlutils.config

def send_email(recipients, subject, msg):
    msg = MIMEText(msg)
    msg['From'] = drlutils.config.MESSAGE_FROM 
    msg['To'] = ', '.join(recipients) 
    msg['Subject'] = subject 
    s = smtplib.SMTP(drlutils.config.SMTP)
    s.sendmail(drlutils.config.MESSAGE_FROM, recipients, msg.as_string())
    s.quit()


def get_recipients(action, has_error=False):
    r = []
    try:
        if has_error and action.name in ['ingest']:
            r.extend(drlutils.config.INGEST_RECIPIENTS)
        elif has_error and action.name in ['prep for bodybuilder']:
            r.extend(drlutils.config.BODYBUILDER_RECIPIENTS)
        elif action.name in ['prepare macrob files']:
            r.extend(drlutils.config.MACROB_RECIPIENTS)
        else:
            pass
    except:
        has_error = True

    if has_error:
        r.extend(drlutils.config.ERROR_RECIPIENTS)

    return list(set(r))

