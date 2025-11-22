import UIKit

class SceneDelegate: UIResponder, UIWindowSceneDelegate {
  var window: UIWindow?

  func scene(
    _ scene: UIScene,
    willConnectTo session: UISceneSession,
    options connectionOptions: UIScene.ConnectionOptions
  ) {
    guard let windowScene = scene as? UIWindowScene else {
      return
    }

    // When using storyboards the system wires up the initial Flutter view
    // controller automatically. We just need to ensure the window references
    // the active UIWindowScene so that UIKit can manage gestures correctly.
    if window == nil {
      window = UIWindow(windowScene: windowScene)
      window?.rootViewController = UIStoryboard(name: "Main", bundle: nil)
        .instantiateInitialViewController()
    } else {
      window?.windowScene = windowScene
    }

    window?.makeKeyAndVisible()
  }
}
