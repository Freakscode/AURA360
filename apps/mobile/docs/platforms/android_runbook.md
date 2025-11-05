# Guía de ejecución y diagnóstico Android

## Entorno de referencia
- **Fecha**: 17 de octubre de 2025.
- **IDE**: Android Studio Ladybug | 2024.2.1 Patch 2 con Flutter plugin 84.
- **SDK**: Flutter 3.24.x (Dart 3.9.2), Android SDK Platform 35 (Android 15).
- **Emulador**: Pixel 8 Pro API 35 (x86_64 / ARM64) con 8 GB RAM y 2560 MB de RAM gráfica.
- **Backend local**: Supabase CLI 1.181 en `http://127.0.0.1:54321`.

## Preparativos iniciales
1. Instala paquetes Android necesarios:
   ```bash
   sdkmanager \
     "platforms;android-35" \
     "build-tools;35.0.0" \
     "platform-tools" \
     "emulator"
   ```
2. Crea el AVD (ejemplo Pixel 8 Pro):
   ```bash
   avdmanager create avd \
     -n Pixel8ProApi35 \
     -k "system-images;android-35;google_apis;x86_64"
   ```

## Ejecutar la app en emulador
1. **Sincronizar dependencias**
   ```bash
   flutter clean
   flutter pub get
   ```
2. **Lanzar el emulador**
   ```bash
   flutter emulators --launch Pixel8ProApi35
   ```
3. **Ajustar defines para apuntar al host**
   - Los emuladores Android acceden a la máquina anfitrión mediante `10.0.2.2`.  
   - Crea (o edita) `env/android.emu.env` con overrides específicos:
     ```bash
     cp env/local.env env/android.emu.env
     ```
     ```diff
     -SUPABASE_URL=http://127.0.0.1:54321
     +SUPABASE_URL=http://10.0.2.2:54321
     -POSTGRES_HOST=127.0.0.1
     +POSTGRES_HOST=10.0.2.2
     ```
4. **Ejecutar la app**
   ```bash
   tool/run_dev.sh -d emulator-5554 \
     --dart-define-from-file=env/android.emu.env
   ```
   Si usas varios emuladores, revisa el ID con `flutter devices`.

## Diagnóstico de rendimiento
- **Modo debug vs profile**  
  Usa `flutter run --profile -d emulator-5554` para medir FPS reales. En debug verás más jank por el JIT.
- **Registro de fotogramas**  
  ```bash
  adb shell dumpsys gfxinfo com.example.aura_mobile
  ```
  Observa columnas `Janky frames` y `50th percentile`.
- **Captura de eventos timeline**  
  Ejecuta `flutter attach`, luego abre DevTools → Performance y graba una sesión para inspeccionar layout/paint costosos.
- **Lentitud al hidratar sesión**  
  Si ves bloqueos en `GestureDetector` similares a iOS, revisa `AuthController.hydrate` y valida que Supabase responda (`adb logcat | rg Supabase`). Falla de red (e.g. URLs sin `10.0.2.2`) provoca reintentos y sensación de congelamiento.
- **GPU/CPU emulador**  
  Asigna `hw.gpu.mode=host` en AVD (`~/.android/avd/<name>.avd/config.ini`) para usar aceleración por hardware. Sin aceleración la app corre muy lenta.

## Buenas prácticas adicionales
- Ejecuta `flutter analyze` y `flutter test` antes de levantar el emulador para detectar problemas que bloqueen la build.
- Si necesitas probar sensores o cámara, habilita *Virtual scene camera* desde Android Studio.
- Elimina caches corruptas cuando notes `Errors found! Invalidating cache...`:
  ```bash
  flutter clean
  ./android/gradlew clean
  rm -rf ~/.gradle/caches
  ```

## Checklist previo a QA
- [ ] `env/android.emu.env` apunta a `10.0.2.2`.
- [ ] DevTools timeline sin picos > 16 ms tras la pantalla de *Home*.
- [ ] `adb shell dumpsys gfxinfo` reporta < 5 % frames janky en modo profile.
- [ ] Resultado de `flutter test` y `flutter analyze` exitoso.
- [ ] Build `flutter build apk --release` generado y probado en emulador y/o dispositivo físico Android 15.
