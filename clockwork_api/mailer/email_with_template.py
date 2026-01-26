from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.conf import settings


class EmailWithTemplate:
    """
    Utility class for sending system emails using HTML templates.

    This class centralizes all outgoing research-related email
    communication, including:

        - Researcher registration notifications
        - Account approval messages
        - Request confirmations
        - Restricted material decisions
        - Item delivery notifications
        - Account recovery messages

    Email templates are stored under:
        research/emails/<template_name>.html

    Recipients are resolved dynamically based on message type:
        - User (researcher)
        - Staff
        - Restricted decision makers

    Configuration is controlled via Django settings:
        - RESEARCH_ROOM_STAFF_EMAIL
        - RESTRICTED_DECISION_MAKER_EMAIL
    """

    def __init__(self, researcher, context):
        """
        Initialize the email sender.

        Args:
            researcher (Researcher):
                The researcher associated with this email.

            context (dict):
                Template context variables used when rendering
                the email body.
        """
        self.staff_emails = getattr(settings, 'RESEARCH_ROOM_STAFF_EMAIL')
        self.restricted_decision_maker_emails = getattr(
            settings,
            'RESTRICTED_DECISION_MAKER_EMAIL'
        )

        self.researcher = researcher
        self.template = ""
        self.context = context

    # ------------------------------------------------------------------
    # Public API: High-level notification methods
    # ------------------------------------------------------------------

    def send_new_user_registration_admin(self):
        """
        Notify staff about a new researcher registration.
        """
        self.template = "researcher_registration_admin"
        self._send_mail('admin')

    def send_new_user_registration_user(self):
        """
        Send confirmation email to a newly registered researcher.
        """
        self.template = "researcher_registration_user"
        self._send_mail('user')

    def send_new_user_approved_user(self):
        """
        Notify the researcher that their registration was approved.
        """
        self.template = "researcher_approved_user"
        self._send_mail('user')

    def send_new_request_admin(self):
        """
        Notify staff about a new material request.
        """
        self.template = "new_request_admin"
        self._send_mail('admin')

    def send_new_request_user(self):
        """
        Send request confirmation to the researcher.
        """
        self.template = "new_request_user"
        self._send_mail('user')

    def send_new_request_restricted_decision_maker(self):
        """
        Notify decision makers about a request containing
        restricted material.
        """
        self.template = "new_request_restricted_decision_maker"
        self._send_mail('restricted_decision_maker')

    def send_new_request_restricted_decision_user(self):
        """
        Notify the researcher about a decision on restricted material.
        """
        self.template = "new_request_restricted_decision_user"
        self._send_mail('user')

    def send_new_request_restricted_decision_admin(self):
        """
        Notify staff about a restricted material decision.
        """
        self.template = "new_request_restricted_decision_admin"
        self._send_mail('admin')

    def send_request_delivered_user(self):
        """
        Notify the researcher that requested items are prepared.
        """
        self.template = "request_delivered_user"
        self._send_mail('user')

    def send_researcher_forgot_card_number(self):
        """
        Send researcher their forgotten card number.
        """
        self.template = "researcher_forgot_card_number"
        self._send_mail('user')

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _send_mail(self, to='user'):
        """
        Render and send the configured email.

        Args:
            to (str):
                Recipient group. One of:
                    - 'user'
                    - 'admin'
                    - 'restricted_decision_maker'

        Returns:
            int: Number of successfully delivered messages.
        """
        message = get_template(
            f"research/emails/{self.template}.html"
        ).render(self.context)

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
        """
        Resolve the email subject based on the selected template.

        Returns:
            str: Email subject line.
        """

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

        if self.template == 'new_request_restricted_decision_admin':
            return "Decision about requesting restricted content!"

        # Request Item status change
        if self.template == 'request_delivered_user':
            return "Requested items are prepared"
