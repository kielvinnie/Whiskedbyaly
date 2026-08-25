import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):

    help = "Create the production Django superuser."

    def handle(self, *args, **options):

        User = get_user_model()

        username = os.environ.get(
            "ADMIN_USERNAME"
        )

        password = os.environ.get(
            "ADMIN_PASSWORD"
        )

        if not username or not password:

            self.stdout.write(
                self.style.ERROR(
                    "ADMIN_USERNAME and ADMIN_PASSWORD "
                    "environment variables are required."
                )
            )

            return

        user, created = User.objects.get_or_create(
            username=username
        )

        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        if created:

            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser '{username}' created."
                )
            )

        else:

            self.stdout.write(
                self.style.SUCCESS(
                    f"Superuser '{username}' already exists. "
                    "Password updated."
                )
            )
        