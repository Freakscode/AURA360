"""Command para auditar el estado de Row Level Security en las tablas críticas."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import connection


DEFAULT_TABLES = (
    "body_activities",
    "body_nutrition_logs",
    "body_sleep_logs",
    "user_context_snapshots",
    "mood_entries",
    "user_profile_extended",
)


class Command(BaseCommand):
    help = "Muestra si RLS está habilitado y las políticas registradas por tabla."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tables",
            nargs="*",
            default=DEFAULT_TABLES,
            help="Lista de tablas (schema public) a revisar",
        )

    def handle(self, *args, **options):
        tables = options["tables"] or DEFAULT_TABLES
        table_tuple = tuple(tables)

        self.stdout.write(self.style.NOTICE("Revisando estado de RLS..."))
        rls_query = """
            SELECT nspname AS schema,
                   relname AS table,
                   relrowsecurity AS rls_enabled,
                   relforcerowsecurity AS rls_forced
            FROM pg_class
            JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace
            WHERE relkind = 'r'
              AND nspname IN ('public', 'auth')
              AND relname = ANY(%s)
            ORDER BY nspname, relname;
        """

        policy_query = """
            SELECT schemaname,
                   tablename,
                   policyname,
                   permissive,
                   roles,
                   cmd
            FROM pg_policies
            WHERE schemaname IN ('public', 'auth')
              AND tablename = ANY(%s)
            ORDER BY schemaname, tablename, policyname;
        """

        with connection.cursor() as cursor:
            cursor.execute(rls_query, (table_tuple,))
            rows = cursor.fetchall()

        if not rows:
            self.stdout.write("No se encontraron tablas para las que consultar RLS.")
        else:
            for schema, table, enabled, forced in rows:
                status = "ON" if enabled else "OFF"
                forced_text = " (forced)" if forced else ""
                self.stdout.write(f"- {schema}.{table}: RLS {status}{forced_text}")

        self.stdout.write("\nPolíticas registradas:")
        with connection.cursor() as cursor:
            cursor.execute(policy_query, (table_tuple,))
            policies = cursor.fetchall()

        if not policies:
            self.stdout.write("(sin políticas registradas)")
            return

        for schema, table, policy, permissive, roles, cmd in policies:
            roles_str = roles or "PUBLIC"
            mode = "PERMISSIVE" if permissive else "RESTRICTIVE"
            self.stdout.write(
                f"- {schema}.{table} → {policy} [{cmd}] {mode} roles={roles_str}"
            )
