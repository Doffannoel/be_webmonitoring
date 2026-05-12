from django.core.management.base import BaseCommand, CommandError

from monitoring.services import send_alert_email


class Command(BaseCommand):
    help = "Send a test alert email using the current Django email settings."

    def add_arguments(self, parser):
        parser.add_argument(
            "--to",
            required=True,
            help="Recipient email address.",
        )
        parser.add_argument(
            "--device",
            default="Test Device",
            help="Device name to show in the email.",
        )
        parser.add_argument(
            "--alert-type",
            default="threshold",
            help="Alert type label to show in the email.",
        )
        parser.add_argument(
            "--severity",
            default="warning",
            choices=["info", "warning", "critical"],
            help="Alert severity to show in the email.",
        )
        parser.add_argument(
            "--message",
            default="Ini adalah email tes alert dari Django.",
            help="Alert message body.",
        )

    def handle(self, *args, **options):
        recipient = options["to"].strip()
        if not recipient:
            raise CommandError("Parameter --to wajib diisi.")

        send_alert_email(
            recipients=[recipient],
            device_name=options["device"],
            alert_type=options["alert_type"],
            severity=options["severity"],
            message=options["message"],
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Permintaan kirim email test alert sudah dijalankan ke {recipient}."
            )
        )
