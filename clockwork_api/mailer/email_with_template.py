from django.core.mail import EmailMessage
from django.template import Context
from django.template.loader import get_template
from django.conf import settings


class EmailWithTemplate:
    def __init__(self, researcher, context):
        self.staff_emails = getattr(settings, 'RESEARCH_ROOM_STAFF_EMAIL')
        self.restricted_decision_maker_emails = getattr(settings, 'RESTRICTED_DECISION_MAKER_EMAIL')
        self.researcher = researcher
        self.template = ""
        self.context = context

    def send_new_user_registration_admin(self):
        self.template = "researcher_registration_admin"
        self._send_mail('admin')

    def send_new_user_registration_user(self):
        self.template = "researcher_registration_user"
        self._send_mail('user')

    def send_new_user_approved_user(self):
        self.template = "researcher_approved_user"
        self._send_mail('user')

    def send_new_request_admin(self):
        self.template = "new_request_admin"
        self._send_mail('admin')

    def send_new_request_user(self):
        self.template = "new_request_user"
        self._send_mail('user')

    def send_new_request_restricted_decision_maker(self):
        self.template = "new_request_restricted_decision_maker"
        self._send_mail('restricted_decision_maker')

    def send_new_request_restricted_decision_user(self):
        self.template = "new_request_restricted_decision_user"
        self._send_mail('user')

    def send_new_request_restricted_decision_admin(self):
        self.template = "new_request_restricted_decision_admin"
        self._send_mail('admin')

    def send_request_delivered_user(self):
        self.template = "request_delivered_user"
        self._send_mail('user')

    def send_researcher_forgot_card_number(self):
        self.template = "researcher_forgot_card_number"
        self._send_mail('user')

    def _send_mail(self, to='user'):
        message = get_template("research/emails/%s.html" % self.template).render(self.context)
        if to == 'user':
            to_address = [self.researcher.email]
        elif to == 'restricted_decision_maker':
            to_address = self.restricted_decision_maker_emails
        else:
            to_address = self.staff_emails
        mail = EmailMessage(
            subject=self._get_subject(),
            body=message,
            from_email="no-reply <blinken-osa-ams@ceu.edu>",
            to=to_address
        )
        mail.content_subtype = "html"
        return mail.send()

    def _get_subject(self):
        # New researcher registration
        if self.template == 'researcher_registration_admin':
            return "New researcher registration"

        if self.template == 'researcher_registration_user':
            return "Registration completed!"

        # New researcher approved
        if self.template == 'researcher_approved_user':
            return "Registration approved!"

        # Researcher forgot card number
        if self.template == 'researcher_forgot_card_number':
            return "Your Research Card number"

        # New Request
        if self.template == 'new_request_admin':
            return "New request arrived!"

        if self.template == 'new_request_user':
            return "Request confirmation"

        # New Request with restricted content
        if self.template == 'new_request_restricted_decision_maker':
            return "New request with restricted content arrived!"

        if self.template == 'new_request_restricted_decision_user':
            return "Decision about requesting restricted content!"

        # Request Item status change
        if self.template == 'request_delivered_user':
            return "Requested items are prepared"

