# User Flow Diagram - AURA360

Este diagrama representa el flujo de navegación de la aplicación móvil.

```mermaid
graph TD
    Start((Tap on App Icon)) --> Splash[Splash Screen]
    Splash --> Onboarding[Onboarding Screens]
    Onboarding --> AuthDecision{Create Account / Login Account}

    %% Authentication Flow
    AuthDecision -->|Sign Up| SignUp[Sign Up]
    AuthDecision -->|Login| Login[Login]

    SignUp --> Facebook[Facebook]
    SignUp --> Google[Google]
    SignUp --> CreateAccount[Create Account]

    Login --> ForgotPass[Forgot Password]
    ForgotPass --> ResetPass[Reset Password]

    %% Main Navigation
    Facebook --> HomeScreen[Home Screen]
    Google --> HomeScreen
    CreateAccount --> HomeScreen
    Login --> HomeScreen
    ResetPass --> HomeScreen

    %% Home Screen Branches
    HomeScreen --> Search[Search]
    HomeScreen --> Courses[Courses]
    HomeScreen --> MyProfile[My Profile]
    HomeScreen --> Messages[Messages]
    HomeScreen --> Notifications[Notifications]

    %% Search Branch
    Search --> SearchCourses[Search Courses]
    SearchCourses --> SearchTutors[Search Tutors]

    %% Courses Branch
    Courses --> InProgress[In Progress]
    InProgress --> Bookmark[Bookmark]
    Bookmark --> Test[Test]
    Test --> Feedback[Feedback]
    Feedback --> Completed[Completed]

    %% Profile Branch
    MyProfile --> Edit[Edit]
    Edit --> Settings[Settings]
    Settings --> MyCourses[My Courses]
    MyCourses --> Payments[Payments]
    Payments --> Contacts[Contacts]
    Contacts --> Logout[Logout]

    %% Messages Branch
    Messages --> Chat[Chat]
    Chat --> GroupChat[Group Chat]

    %% Notifications Branch
    Notifications --> Updates[Updates]

    %% Styling
    classDef startNode fill:#2d3436,stroke:#fff,stroke-width:2px,color:#fff;
    classDef decisionNode fill:#0984e3,stroke:#fff,stroke-width:2px,color:#fff;
    classDef screenNode fill:#dfe6e9,stroke:#2d3436,stroke-width:1px,color:#2d3436;

    class Start startNode;
    class AuthDecision decisionNode;
    class Splash,Onboarding,SignUp,Login,ForgotPass,ResetPass,HomeScreen,Search,Courses,MyProfile,Messages,Notifications,SearchCourses,SearchTutors,InProgress,Bookmark,Test,Feedback,Completed,Edit,Settings,MyCourses,Payments,Contacts,Logout,Chat,GroupChat,Updates screenNode;
```