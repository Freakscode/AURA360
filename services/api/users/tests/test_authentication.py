"""Pruebas para la autenticación Supabase JWT."""

import json
import os
import tempfile
import uuid

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.contrib.auth import get_user_model
from django.db import connection
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import AppUser


class SupabaseJWTAuthenticationTests(APITestCase):
    """Valida que el backend acepte tokens generados por Supabase."""

    @classmethod
    def setUpTestData(cls):
        cls._ensure_app_users_table()

    @staticmethod
    def _ensure_app_users_table():
        """Crea la tabla app_users si no existe (necesaria para tests).
        
        Esta tabla existe en Supabase pero pytest crea una DB temporal,
        por lo que debemos recrearla manualmente para los tests.
        """
        vendor = connection.vendor
        with connection.cursor() as cursor:
            if vendor == 'sqlite':
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        auth_user_id TEXT UNIQUE,
                        full_name TEXT NOT NULL,
                        age INTEGER NOT NULL DEFAULT 0,
                        email TEXT UNIQUE,
                        phone_number TEXT,
                        gender TEXT,
                        tier TEXT NOT NULL,
                        role_global TEXT NOT NULL DEFAULT 'General',
                        is_independent BOOLEAN NOT NULL DEFAULT 0,
                        billing_plan TEXT NOT NULL DEFAULT 'individual',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    """,
                )
            else:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS app_users (
                        id BIGSERIAL PRIMARY KEY,
                        auth_user_id UUID UNIQUE,
                        full_name TEXT NOT NULL,
                        age INTEGER NOT NULL DEFAULT 0,
                        email TEXT UNIQUE,
                        phone_number TEXT,
                        gender TEXT,
                        tier TEXT NOT NULL,
                        role_global TEXT NOT NULL DEFAULT 'General',
                        is_independent BOOLEAN NOT NULL DEFAULT FALSE,
                        billing_plan TEXT NOT NULL DEFAULT 'individual',
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    )
                    """,
                )

    def setUp(self):
        self.auth_user = get_user_model().objects.create_user(
            username=f"auth-user-{uuid.uuid4()}",
            email='auth-tester@example.com',
            password='holistic-pass',
        )
        self.client.force_authenticate(self.auth_user)

        self.app_user = AppUser.objects.create(
            auth_user_id=uuid.uuid4(),
            full_name='Auth Tester',
            age=30,
            email=self.auth_user.email,
            tier='free',
        )

    def test_authenticated_request_with_valid_token(self):
        jwt_secret = 'test-secret'
        os.environ['SUPABASE_JWT_SECRET'] = jwt_secret
        self.addCleanup(lambda: os.environ.pop('SUPABASE_JWT_SECRET', None))

        token = jwt.encode(
            {
                'sub': str(self.app_user.auth_user_id),
                'email': self.app_user.email,
                'role': 'authenticated',
            },
            jwt_secret,
            algorithm='HS256',
        )

        url = reverse('users:appuser-quota-status', args=[self.app_user.id])
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rejects_invalid_signature(self):
        jwt_secret = 'test-secret'
        os.environ['SUPABASE_JWT_SECRET'] = jwt_secret
        self.addCleanup(lambda: os.environ.pop('SUPABASE_JWT_SECRET', None))

        token = jwt.encode(
            {'sub': str(self.app_user.auth_user_id)},
            'wrong-secret',
            algorithm='HS256',
        )

        url = reverse('users:appuser-quota-status', args=[self.app_user.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_request_with_jwks(self):
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()
        public_jwk = jwt.algorithms.RSAAlgorithm.to_jwk(public_key)

        jwk_dict = json.loads(public_jwk)
        jwk_dict.update(
            {
                'kid': 'test-key',
                'alg': 'RS256',
                'use': 'sig',
            }
        )
        jwks_payload = {'keys': [jwk_dict]}

        with tempfile.NamedTemporaryFile('w+', delete=False, suffix='.json') as jwks_file:
            json.dump(jwks_payload, jwks_file)
            jwks_file.flush()
            os.environ['SUPABASE_JWKS_FILE'] = jwks_file.name
            self.addCleanup(lambda: os.environ.pop('SUPABASE_JWKS_FILE', None))
            self.addCleanup(lambda: os.remove(jwks_file.name))

        os.environ['SUPABASE_JWT_ALGORITHMS'] = 'RS256,HS256'
        self.addCleanup(lambda: os.environ.pop('SUPABASE_JWT_ALGORITHMS', None))

        token = jwt.encode(
            {
                'sub': str(self.app_user.auth_user_id),
                'email': self.app_user.email,
                'role': 'authenticated',
            },
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            ),
            algorithm='RS256',
            headers={'kid': 'test-key'},
        )

        url = reverse('users:appuser-quota-status', args=[self.app_user.id])
        response = self.client.get(
            url,
            HTTP_AUTHORIZATION=f'Bearer {token}',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
