import boto3
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from fastapi import HTTPException
from scrape.core.configs import (
    SENDGRID_API_KEY, FROM_EMAIL, SUPPORT_EMAIL,
    AWS_REGION, SES_SENDER, AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY
)
from scrape.core.logger import logger


async def send_contact_email(name: str, email: str, subject: str, message: str):
    logger.info("Sending contact email via sendgrid")
    if not SENDGRID_API_KEY:
        logger.warning("SendGrid not configured")
        raise HTTPException(status_code=400, detail="SendGrid not configured")

    content = f"""
    Name: {name}
    Email: {email}

    Message:
    {message}
    """

    mail = Mail(
        from_email=FROM_EMAIL,
        to_emails=SUPPORT_EMAIL,
        subject=subject,
        plain_text_content=content,
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(mail)
        return {"status": "success", "code": response.status_code}
    except Exception as e:
        logger.exception("Error: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


ses_client = boto3.client(
    "ses",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


async def send_email_via_ses(name: str, email: str, subject: str, message: str):
    logger.info("Sending email via SES")
    try:
        response = ses_client.send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses": [SUPPORT_EMAIL]},
            Message={
                "Subject": {"Data": subject},
                "Body": {
                    "Text": {
                        "Data": f"Name: {name}\n"
                                f"Email: {email}\n\n"
                                f"Message:\n{message}"
                    }
                },
            },
            ReplyToAddresses=[email],
        )
        return {"status": "Success", "message_id": response["MessageId"]}
    except Exception as e:
        logger.exception("Error sending email via SES: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send email") from e


async def reset_password_send_email(to: str, subject: str, body: str):
    try:
        response = ses_client.send_email(
            Source=SES_SENDER,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": body, "Charset": "UTF-8"},
                    "Html": {"Data": f"<html><body>{body}</body></html>", "Charset": "UTF-8"},
                },
            },
        )
        return response
    except Exception as e:
        logger.exception("Error sending email via SES: %s", e)
        raise HTTPException(status_code=500, detail="Failed to send email") from e
