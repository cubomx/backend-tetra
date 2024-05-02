# management/commands/createadmin.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a master administrator'

    def handle(self, *args, **kwargs):
        User = get_user_model()
        if not User.objects.filter(is_superuser=True).exists():
            email = input('Enter email for master administrator: ')
            password = input('Enter password for master administrator: ')

            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(self.style.SUCCESS('Master administrator created successfully'))
        else:
            self.stdout.write(self.style.WARNING('A superuser already exists. Skipping master administrator creation'))
