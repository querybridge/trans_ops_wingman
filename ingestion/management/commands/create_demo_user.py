import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create or reset the non-staff demo user for the walkthrough. Prompts for the password; never pass it on the command line."

    def add_arguments(self, parser):
        parser.add_argument("username", nargs="?", default="demo")

    def handle(self, username, **options):
        password = getpass.getpass(f"Password for demo user {username!r}: ")
        if password != getpass.getpass("Repeat password: "):
            raise CommandError("Passwords don't match.")
        User = get_user_model()
        user = User.objects.filter(username=username).first() or User(username=username)
        try:
            validate_password(password, user)
        except ValidationError as exc:
            raise CommandError(" ".join(exc.messages))
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f"Demo user {username!r} is ready (no admin access)."))
