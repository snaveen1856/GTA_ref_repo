Mailexceptions = {'MailConnectionException': {'enum': 300, 'emsg': 'Mail connection is not established check smtp ip or port'},
                  'MailRecipientsException': {'enum': 301, 'emsg': 'Not sending mails due to incorrect recipients list'},
				  'MailSocketAccessDeniedException': {'enum': 302, 'emsg': 'Not sending mails since mail socket access denied'}
				  }


class MailExceptions(Exception):
    """
    Custom Exception for handling mail related errors.
    """
    pass


class MailConnectionException(MailExceptions):
    """
    Custom Exception for handling mail connection error.
    """
    message = Mailexceptions["MailConnectionException"]["emsg"]
    eNumber = Mailexceptions["MailConnectionException"]["enum"]
    pass


class MailRecipientsException(MailExceptions):
    """
    Custom Exception for handling recipients list error.
    """
    message = Mailexceptions["MailRecipientsException"]["emsg"]
    eNumber = Mailexceptions["MailRecipientsException"]["enum"]
    pass

class MailSocketAccessDeniedException(MailExceptions):
    """
    Custom Exception for handling mail socket access denied.
    """
    message = Mailexceptions["MailSocketAccessDeniedException"]["emsg"]
    eNumber = Mailexceptions["MailSocketAccessDeniedException"]["enum"]
    pass 