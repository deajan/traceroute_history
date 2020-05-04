#! /usr/bin/env python
#  -*- coding: utf-8 -*-
#
# This file is part of ofunctions module

"""
ofunctions is a general library for basic repetitive tasks that should be no brainers :)

Versionning semantics:
    Major version: backward compatibility breaking changes
    Minor version: New functionnality
    Patch version: Backwards compatible bug fixes

"""

__intname__ = 'ofunctions.mailer'
__author__ = 'Orsiris de Jong'
__copyright__ = 'Copyright (C) 2014-2020 Orsiris de Jong'
__licence__ = 'BSD 3 Clause'
__version__ = '0.3.2'
__build__ = '2020041302'


import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
import ssl
import socket
import re


def send_email(source_mail=None, destination_mails=None, split_mails=False, smtp_server='localhost', smtp_port=25,
               smtp_user=None, smtp_password=None, security=None, subject=None, body=None, attachment=None,
               filename=None, html_enabled=False, bcc_mails=None, priority=False, debug=False):
    """

    :param source_mail:
    :param destination_mails: Accepts space, comma or semi-colon separated email addresses or list of email addresses
    :param split_mails: When multiple mails exist, shall we create an email per addresss or an unique one
    :param smtp_server:
    :param smtp_port:
    :param smtp_user:
    :param smtp_password:
    :param security:
    :param subject:
    :param body:
    :param attachment: (str/bytes): Path to file, or inline binary data
    :param filename: (str):  filename in case we use inline binary data
    :param html_enabled:
    :param bcc_mails:
    :param priority: (bool) set to true to add a high priority flag
    :param debug:
    :return:
    """

    if subject is None:
        raise ValueError('No subject set')

    # Fix for empty passed auth strings
    if len(smtp_user) == 0:
        smtp_user = None
    if len(smtp_password) == 0:
        smtp_password = None

    if destination_mails is None:
        raise ValueError('No destination mails set')

    def _send_email(address):
        nonlocal filename

        # Create a multipart message and set headers
        message = MIMEMultipart()
        message["From"] = source_mail
        message["To"] = destination_mail
        message["Subject"] = subject

        if bcc_mails is not None:
            message["Bcc"] = bcc_mails  # Recommended for mass emails

        if priority:
            message["X-Priority"] = '2'
            message['X-MSMail-Priority'] = 'High'

        # Add body to email
        if body is not None:
            if html_enabled:
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))

        if attachment is not None:
            if isinstance(attachment, bytes):
                # Let's suppose we directly attach binary data
                payload = attachment
            else:
                with open(attachment, 'rb') as f_attachment:
                    payload = f_attachment.read()
                    filename = os.path.basename(attachment)

            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(payload)

            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)

            # Add header as key/value pair to attachment part
            part.add_header(
                "Content-Disposition",
                "attachment; filename=%s" % filename,
            )

            # Add attachment to message and convert message to string
            message.attach(part)

        text = message.as_string()

        try:
            if security == 'ssl':
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as remote_server:
                    if debug:
                        remote_server.set_debuglevel(True)
                    remote_server.ehlo()
                    if smtp_user is not None and smtp_password is not None:
                        remote_server.login(smtp_user, smtp_password)
                    remote_server.sendmail(source_mail, destination_mails, text)

            elif security == 'tls':
                # TLS
                context = ssl.create_default_context()
                with smtplib.SMTP(smtp_server, smtp_port) as remote_server:
                    if debug:
                        remote_server.set_debuglevel(True)
                    remote_server.ehlo()
                    remote_server.starttls(context=context)
                    remote_server.ehlo()
                    if smtp_user is not None and smtp_password is not None:
                        remote_server.login(smtp_user, smtp_password)
                    remote_server.sendmail(source_mail, destination_mails, text)

            else:
                with smtplib.SMTP(smtp_server, smtp_port) as remote_server:
                    if debug:
                        remote_server.set_debuglevel(True)
                    remote_server.ehlo()
                    if smtp_user is not None and smtp_password is not None:
                        remote_server.login(smtp_user, smtp_password)
                    remote_server.sendmail(source_mail, destination_mails, text)
        # SMTPNotSupportedError = Server does not support STARTTLS
        except (smtplib.SMTPAuthenticationError, smtplib.SMTPSenderRefused, smtplib.SMTPRecipientsRefused,
                smtplib.SMTPDataError, ConnectionRefusedError, ConnectionAbortedError, ConnectionResetError,
                ConnectionError, socket.gaierror, smtplib.SMTPNotSupportedError, ssl.SSLError) as exc:
            return exc

    if not isinstance(destination_mails, list):
        # Make sure destination mails is a list
        destination_mails = re.split(r',|;| ', destination_mails)

    rfc822_addresses = [mail for mail in destination_mails if is_mail_address(mail)]
    non_rfc822_addresses = [mail for mail in destination_mails if mail not in rfc822_addresses]

    if not split_mails:
        for destination_mail in rfc822_addresses:
            _send_email(destination_mail)
    else:
        _send_email(','.join(rfc822_addresses))

    if non_rfc822_addresses == []:
        return True

    return 'Refused non RFC 822 mails: {0}'.format(non_rfc822_addresses)


def is_mail_address(string):
    if re.match(r'[^@\s]+@[^@\s]+\.[a-zA-Z0-9]+$', string):
        return True
    else:
        return False