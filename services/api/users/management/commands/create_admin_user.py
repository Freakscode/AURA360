"""
Management command to create or update Django admin/staff users quickly.
"""

from __future__ import annotations

from getpass import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Creates or updates a Django admin/staff user using CLI arguments."

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            required=True,
            help='Email address for the admin user (used as username).',
        )
        parser.add_argument(
            '--password',
            help='Password for the user. If omitted, you will be prompted.',
        )
        parser.add_argument(
            '--first-name',
            default='',
            help='Optional first name.',
        )
        parser.add_argument(
            '--last-name',
            default='',
            help='Optional last name.',
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='If provided, the user will be created/updated as superuser.',
        )
        parser.add_argument(
            '--no-input',
            action='store_true',
            help='Do not prompt for missing values. Fails if password is missing.',
        )

    def handle(self, *args, **options):
        email = options['email'].strip().lower()
        if not email:
            raise CommandError('Email is required.')

        password = options.get('password')
        no_input = options['no_input']

        if not password:
            if no_input:
                raise CommandError('Password is required when using --no-input.')
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            if password != password_confirm:
                raise CommandError('Passwords did not match.')

        first_name = options['first_name'].strip()
        last_name = options['last_name'].strip()
        make_superuser = options['superuser']

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=email,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            },
        )

        if not created:
            # Update basic info if provided
            updated_fields = []
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated_fields.append('first_name')
            if last_name and user.last_name != last_name:
                user.last_name = last_name
                updated_fields.append('last_name')
            if user.email != email:
                user.email = email
                updated_fields.append('email')
            if updated_fields:
                user.save(update_fields=updated_fields)
            self.stdout.write(self.style.NOTICE(f'Updated existing user: {email}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Created new user: {email}'))

        # Configure permissions
        user.is_active = True
        user.is_staff = True
        user.is_superuser = make_superuser
        user.set_password(password)
        user.save()

        if make_superuser:
            self.stdout.write(self.style.SUCCESS('User granted superuser privileges.'))
        else:
            self.stdout.write(self.style.SUCCESS('User marked as staff (non-superuser).'))

        self.stdout.write(self.style.SUCCESS('Done. You can now log in with the provided credentials.'))
