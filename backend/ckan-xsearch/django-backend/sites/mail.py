from email.mime.text import MIMEText
from logging import getLogger
import os
import smtplib
from typing import List, NoReturn, Optional, Union

logger = getLogger(__name__)


class Mail(object):
    """
    Email class

    Attributes
    ----------
    system_name: str ["カタログ横断検索システム"]
        System name, which will be replaced with '%%SYSTEM_NAME%%'
        in the message.
    from_address: str ["noreply@xckan.nii.ac.jp"]
        Sender email address.
    smtp_host: str
        Hostname / ip-address of the SMTP server.
    smtp_port: int [465]
        Port of the smtp server.
    smtp_user: str
        User name to authenticate with the smtp server.
    smtp_pass: str
        Password to authenticate with the smtp server.
    """

    system_name = os.getenv("XCKAN_SYSTEM_NAME", "カタログ横断検索システム")
    from_address = os.getenv("XCKAN_SYSTEM_FROM", "noreply@xckan.nii.ac.jp")
    smtp_host = os.getenv("SMTP_HOST")
    if smtp_host is None:
        logger.warning("環境変数 SMTP_HOST が未指定です。")

    smtp_port = int(os.getenv("SMTP_PORT", 465))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    @classmethod
    def send(
            cls,
            message: str,
            subject: str,
            to_addresses: Union[str, List[str]],
            from_address: Optional[str] = None) -> NoReturn:
        """
        Send an email.

        Parameters
        ----------
        message: str
            The message.
        subject: str
            Subject.
        from_address: str, optional
            Sender address.
            If omitted, use the class value.
        to_addresses: List[str]
            List of recipient addresses.
        """
        if cls.smtp_host is None:
            return

        msg = MIMEText(
            message.replace('%%SYSTEM_NAME%%', cls.system_name),
            "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = from_address or cls.from_address
        msg["To"] = ', '.join(to_addresses)

        with smtplib.SMTP_SSL(host=cls.smtp_host, port=cls.smtp_port) as smtp:
            if cls.smtp_user:
                logger.debug("Try to login to the smtp {}:{}".format(
                    cls.smtp_host, cls.smtp_port))
                smtp.login(cls.smtp_user, cls.smtp_pass)

            logger.debug("Sending mail: {}".format(msg))
            smtp.send_message(msg)
