# Supabase JWT Signing Keys Migration (2024–2025)

## 1. Contexto
- El 22 de noviembre de 2024 Supabase dejó de exponer `app.settings.jwt_secret` en Postgres; desde entonces los proyectos deben administrar el secret o las claves desde el dashboard o el CLI.citeturn1search2
- En 2025 Supabase lanzó claves de firma asimétricas (ES256, RS256, EdDSA) y anunció la migración automática de todos los proyectos para el 1 de octubre de 2025, con nuevos API keys “publishable/secret” entrando en vigor a partir del 1 de noviembre.citeturn1search3
- El CLI moderno (≥ 2.34) genera claves mediante `supabase gen signing-key` y permite fijarlas en `supabase/config.toml` usando `signing_keys_path`, aunque aún existen bugs puntuales (ej. `PGRST301`) cuando la configuración es incompleta.citeturn2search0turn3search0

## 2. Objetivos de la migración
1. Operar Supabase local con el nuevo esquema asimétrico.
2. Validar tokens en el backend Django mediante JWKS (y mantener compatibilidad con HS256 como fallback).
3. Actualizar la app Flutter para que dependa únicamente de tokens emitidos por Supabase Auth, sin secretos compartidos.

## 3. Flujo recomendado para entornos locales
1. **Actualizar el CLI**  
   ```bash
   supabase --version  # verificar ≥ 2.38.0
   brew upgrade supabase/tap/supabase
   ```
2. **Generar la clave de firma**  
   ```bash
   mkdir -p supabase/signing
   supabase gen signing-key --algorithm ES256 > supabase/signing/key.json
   ```
3. **Configurar `supabase/config.toml`**  
   ```toml
   [auth]
   jwt_type = "es256"
   signing_keys_path = "./signing/key.json"
   ```
   Reinicia los contenedores con `supabase stop && supabase start`.  
   El JWKS público quedará disponible en `http://127.0.0.1:54321/auth/v1/.well-known/jwks.json`.
4. **Compartir claves**  
   - Nunca añadir `signing/key.json` al repositorio; sincronizarlo mediante el gestor de secretos del equipo.
   - Para ejecutar pipelines CI, considerar un paso que genere la clave en caliente antes de `supabase start`.

## 4. Backend (Django)
1. **Dependencias**  
   - Añadir `cryptography` y `pyjwt[crypto]` para poder validar ES256/RS256.
2. **Configuración**  
   - `.env`:  
     ```env
     SUPABASE_JWKS_URL=https://<project>.supabase.co/auth/v1/.well-known/jwks.json
     SUPABASE_JWT_ALGORITHMS=RS256,ES256,EdDSA,HS256
     SUPABASE_JWKS_CACHE_TTL=1200
     ```
   - Para entornos locales offline usar `SUPABASE_JWKS_FILE` apuntando a un JWKS en disco.
3. **Verificación**  
   - Se consulta el JWKS (cacheado 20 min) y se extrae la clave por `kid`.  
   - Si falla la verificación asimétrica pero existe `SUPABASE_JWT_SECRET`, se usa como fallback HS256 para compatibilidad con instalaciones legadas.
4. **Pruebas**  
   - Unit tests generan una clave RSA efímera y escriben un JWKS temporal para validar el flujo completo.

## 5. Flutter
1. **Variables**  
   - `env/local.env`: seguir usando el `anon` key que entrega el CLI; la app obtiene el access token usando Supabase Auth.
   - `env/prod.env`: usar la `publishable` key cuando esté disponible; no almacenar secretos en el binario.
2. **HTTP**  
   - Mantener el interceptor que añade `Authorization: Bearer <access_token>`; el backend no depende ya del secret compartido.
3. **Rotación**  
   - Gestionar expiración/refresh con `supabase_flutter`.  
   - Capturar errores 401/403 y forzar re-autenticación tras rotaciones de clave.

## 6. Checklist de DevOps
| Fase | Acciones |
| --- | --- |
| Pre-migración | Inventariar versiones de CLI y roles del proyecto. |
| Semana 0 | Generar nuevas claves, actualizar config y desplegar backend con soporte JWKS. |
| Semana 1 | Validar login desde apps iOS/Android/web; monitorear `auth` y `postgrest` logs. |
| Semana 2 | Rotar claves antiguas (`supabase auth signing-keys rotate` cuando esté disponible en cloud). |
| Trimestral | Ensayo de rotación, verificación de backups y actualización de documentación. |

## 7. Riesgos conocidos
- **Soporte parcial en CLI**: Hasta octubre 2025 el CLI no reproduce el flujo de publishable/secret API keys; los tests locales deben seguir usando JWT + `anon`.citeturn1search3turn3search0
- **Errores PGRST301**: Se presentan cuando `signing_keys_path` no coincide con la configuración de `jwt_type` o cuando falta reiniciar el stack.citeturn2search0
- **Caché de JWKS**: GoTrue puede tardar hasta 20 min en propagar claves nuevas; los clientes deberían refrescar tokens y el backend invalidar cachés tras la rotación.citeturn1search3

## 8. Referencias
1. Supabase discussion “Important announcement regarding JWT secrets”, nov 2024.citeturn1search2  
2. Supabase blog “Introducing JWT signing keys”, feb 2025.citeturn1search3  
3. Supabase docs: JWT signing keys guide (actualizada jun 2025).citeturn1search3turn1search5  
4. Supabase CLI release 2.45.0 y reportes de errores `signing_keys_path`.citeturn2search0turn3search0  
