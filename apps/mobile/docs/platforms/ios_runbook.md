# Guía de ejecución y diagnóstico iOS

## Entorno de referencia
- **Fecha**: 17 de octubre de 2025.
- **Hardware**: iPhone 16 Pro Max (512 GB) enlazado por cable USB-C.
- **Sistema operativo**: iOS 26.1 beta 2 (verificar con `xcodebuild -showsdks`; Apple etiqueta esta beta como «iOS 18.1 beta 2» en Xcode 16.1 beta 2).
- **macOS anfitrión**: macOS 15 (Sequoia) con Xcode 16.1 beta 2 y CocoaPods ≥ 1.15.
- **SDK Flutter**: 3.24.x (Dart 3.9.2) según `pubspec.yaml`.

> ⚠️ Las betas de iOS y Xcode introducen overhead adicional en modo *debug*. Usa builds *profile* o *release* para evaluar rendimiento real.

## Flujo recomendado para correr en dispositivo físico
1. **Preparar variables de entorno**
   - Copia `env/local.env.example` a `env/local.env` y completa credenciales Supabase.
   - Los iPhone no alcanzan `127.0.0.1`; ejecuta el script con `--lan` para reescribir endpoints:  
     ```bash
     tool/run_dev.sh --lan -d <device-id>
     ```
   - Si necesitas un IP fijo, usa `tool/run_dev.sh --lan-ip 192.168.x.y -d <device-id>`.

2. **Sincronizar dependencias**
   ```bash
   flutter clean
   flutter pub get
   cd ios && pod install --repo-update && cd ..
   ```

3. **Ejecutar en modo perfil para medir rendimiento**
   ```bash
   flutter run --profile -d <device-id> \
     --dart-define-from-file=env/local.env
   ```
   Conecta DevTools (`flutter pub global run devtools`) y abre **Performance → Timeline** para detectar jank.

4. **Generar build release**
   ```bash
   flutter build ipa --release \
     --export-options-plist=ios/Runner/ExportOptions.plist \
     --dart-define-from-file=env/local.env
   ```
   Firma con tu provisioning profile antes de distribución.

## Diagnóstico de la lentitud observada
- **`Gesture: System gesture gate timed out`** indica que el *main thread* de iOS estuvo bloqueado > 0.35 s. Revisa tareas pesadas disparadas al hidratar la sesión (`AuthController.hydrate`) y operaciones de `FlutterSecureStorage`. Usa el timeline de DevTools para confirmar si hay bloques largos en `Platform Channel`.
- **`containerToPush is nil`** y los avisos de constraints provienen del teclado del modal. Asegúrate de cerrar el *bottom sheet* antes de mostrar otro. Añade `isScrollControlled: true` (ya presente) y evita operaciones síncronas dentro de `showModalBottomSheet`.
- **Supabase en dispositivo real**: si no usas `--lan`, las solicitudes a `http://127.0.0.1:54321` quedarán en *timeout*, lo que da la sensación de congelamiento. Verifica desde el dispositivo con Safari → `http://<LAN_IP>:54321`.
- **Modo debug JIT** (log: `Dart execution mode: JIT`): ralentiza la UI ~3-4× comparado con *profile*. Evita evaluar rendimiento en modo debug; usa `--profile` para comparar FPS reales.
- **`UIScene lifecycle will soon be required`**: agrega `UIApplicationSceneManifest` en `ios/Runner/Info.plist` para migrar al ciclo de vida de escenas y evitar *asserts* en futuras betas. Ejemplo:
  ```xml
  <key>UIApplicationSceneManifest</key>
  <dict>
    <key>UIApplicationSupportsMultipleScenes</key>
    <false/>
    <key>UISceneConfigurations</key>
    <dict>
      <key>UIWindowSceneSessionRoleApplication</key>
      <array>
        <dict>
          <key>UISceneConfigurationName</key>
          <string>Default Configuration</string>
          <key>UISceneDelegateClassName</key>
          <string>$(PRODUCT_MODULE_NAME).SceneDelegate</string>
        </dict>
      </array>
    </dict>
  </dict>
  ```
  Crea `ios/Runner/SceneDelegate.swift` si aún no existe.

## Limpieza de caches y herramientas útiles
- Restablecer caches corruptas:
  ```bash
  flutter clean
  rm -rf ~/Library/Developer/Xcode/DerivedData/Runner-*
  pod cache clean --all
  ```
- Ver latencia de suscripción a Supabase:
  ```bash
  flutter run -d <device-id> --profile --trace-startup --verbose
  ```
- Para medir CPU/GPU en el dispositivo usa **Xcode → Debug → View Debugging → Capture GPU Frame**.

## Checklist previo a QA/Release
- [ ] Ejecutaste `tool/run_dev.sh --lan` cuando el backend vive en tu máquina.
- [ ] Confirmaste que `AuthController.hydrate` termina < 150 ms (DevTools timeline).
- [ ] `Info.plist` actualizado con ciclo de escenas para iOS 18+/Xcode 16.
- [ ] `flutter analyze` y `flutter test` sin errores.
- [ ] Build *profile* y *release* validados en iPhone 16 Pro Max.
