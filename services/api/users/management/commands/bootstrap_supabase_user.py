"""Management command para provisionar usuarios reales en Supabase."""
from __future__ import annotations

import secrets
from typing import Any

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from users.models import AppUser, BillingPlan, GlobalRole, UserTier


class Command(BaseCommand):
    help = "Crea un usuario real en Supabase Auth + app_users para habilitar FKs locales."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email del usuario a crear")
        parser.add_argument(
            "--password",
            help="Password inicial. Si no se provee se genera una aleatoria segura.",
        )
        parser.add_argument("--full-name", default="Usuario AURA360", help="Nombre completo a guardar")
        parser.add_argument("--phone", default=None, help="Número telefónico opcional")
        parser.add_argument(
            "--tier",
            choices=[choice for choice, _ in UserTier.choices],
            default=UserTier.FREE,
            help="Membresía asignada en app_users",
        )
        parser.add_argument(
            "--role",
            choices=[choice for choice, _ in GlobalRole.choices],
            default=GlobalRole.GENERAL,
            help="Rol global del usuario",
        )
        parser.add_argument(
            "--billing-plan",
            choices=[choice for choice, _ in BillingPlan.choices],
            default=BillingPlan.INDIVIDUAL,
            help="Plan comercial asociado",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No ejecuta llamadas HTTP ni inserciones, solo imprime el payload",
        )

    def handle(self, *args, **options):
        service_role = settings.SUPABASE_SERVICE_ROLE_KEY
        if not service_role:
            raise CommandError("Configura SUPABASE_SERVICE_ROLE_KEY para usar este comando.")

        base_url = settings.SUPABASE_API_URL.rstrip("/")
        admin_url = f"{base_url}/auth/v1/admin/users"

        email = options["email"].lower().strip()
        password = options.get("password") or secrets.token_urlsafe(16)
        full_name = options["full_name"].strip() or "Usuario AURA360"
        phone = options.get("phone")
        tier = options["tier"]
        role = options["role"]
        billing_plan = options["billing_plan"]
        dry_run = options["dry_run"]

        payload: dict[str, Any] = {
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name,
                "role": role,
            },
        }

        if phone:
            payload["phone"] = phone

        headers = {
            "apikey": service_role,
            "Authorization": f"Bearer {service_role}",
            "Content-Type": "application/json",
        }

        if dry_run:
            self.stdout.write(self.style.NOTICE("Dry-run habilitado. Payload generado:"))
            self.stdout.write(str(payload))
            return

        response = requests.post(admin_url, headers=headers, json=payload, timeout=20)
        if response.status_code >= 400:
            raise CommandError(
                f"Supabase Admin API respondió {response.status_code}: {response.text}"
            )

        user_data = response.json()
        user_id = user_data.get("id") or user_data.get("user", {}).get("id")
        if not user_id:
            raise CommandError("No se pudo obtener el UUID del usuario creado en Supabase.")

        app_user, created = AppUser.objects.update_or_create(
            auth_user_id=user_id,
            defaults={
                "full_name": full_name,
                "email": email,
                "phone_number": phone,
                "tier": tier,
                "role_global": role,
                "billing_plan": billing_plan,
            },
        )

        action = "creado" if created else "actualizado"
        self.stdout.write(
            self.style.SUCCESS(
                f"Usuario {action} correctamente. auth_user_id={user_id} app_user_id={app_user.id}"
            )
        )
        self.stdout.write(f"Password inicial: {password}")
