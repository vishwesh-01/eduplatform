"""
seeds.py — Database seeding script.

Populates the database with the minimum data required for the platform to
function:
  - 2 roles: student, admin
  - 6 learning goals
  - 5+ quiz questions per goal at each difficulty level (1-5)

Usage (from the backend/ directory with virtualenv active):
    python -m backend.seeds
Or from the project root:
    python backend/seeds.py

Requires DATABASE_URL to be set in the environment (loaded from .env).
"""

import sys
import os

# Add project root to path when run as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.app import create_app
from backend.extensions import db
from backend.models import Goal, Role, QuizQuestion
from backend.models.quiz import QuestionSource


# ── Seed data definitions ────────────────────────────────────────────────────

ROLES = ["student", "admin"]

GOALS = [
    {"name": "Java Developer",       "description": "Build production-ready Java applications and backend services."},
    {"name": "Python Developer",     "description": "Master Python for scripting, web development, and automation."},
    {"name": "Web Developer",        "description": "Build modern full-stack web applications."},
    {"name": "Data Scientist",       "description": "Analyse data, build ML models, and derive insights."},
    {"name": "Mobile App Developer", "description": "Develop cross-platform mobile apps for iOS and Android."},
    {"name": "DevOps Engineer",      "description": "Automate infrastructure, CI/CD pipelines, and cloud deployments."},
]

# 5 questions per goal per difficulty level (1-5) = 25 questions per goal
QUIZ_QUESTIONS = {
    "Java Developer": [
        # Difficulty 1 — Beginner
        {"text": "What is the correct way to declare a variable in Java?", "options": ["int x = 5;", "variable x = 5;", "x := 5;", "var x: int = 5;"], "correct": 0, "difficulty": 1},
        {"text": "Which keyword is used to define a class in Java?", "options": ["define", "struct", "class", "object"], "correct": 2, "difficulty": 1},
        {"text": "What does JVM stand for?", "options": ["Java Virtual Machine", "Java Variable Manager", "Java Version Manager", "Java Visual Module"], "correct": 0, "difficulty": 1},
        {"text": "Which data type stores whole numbers in Java?", "options": ["float", "String", "int", "char"], "correct": 2, "difficulty": 1},
        {"text": "How do you print text in Java?", "options": ["print('Hello');", "console.log('Hello');", "System.out.println('Hello');", "echo 'Hello';"], "correct": 2, "difficulty": 1},
        # Difficulty 2
        {"text": "What is the main method signature in Java?", "options": ["public static void main(String[] args)", "public void main(String[] args)", "static void main()", "main(String args)"], "correct": 0, "difficulty": 2},
        {"text": "Which keyword is used for inheritance in Java?", "options": ["implements", "extends", "inherits", "super"], "correct": 1, "difficulty": 2},
        {"text": "What is encapsulation in Java?", "options": ["Hiding implementation details", "Creating objects", "Method overloading", "Exception handling"], "correct": 0, "difficulty": 2},
        {"text": "What is the default value of an int in Java?", "options": ["null", "1", "0", "-1"], "correct": 2, "difficulty": 2},
        {"text": "Which collection class allows duplicate elements in Java?", "options": ["HashSet", "TreeSet", "ArrayList", "HashMap"], "correct": 2, "difficulty": 2},
        # Difficulty 3
        {"text": "What is the difference between == and .equals() in Java?", "options": ["No difference", "== compares references; .equals() compares values", "== compares values; .equals() compares references", ".equals() only works on primitives"], "correct": 1, "difficulty": 3},
        {"text": "What does the 'final' keyword do in Java?", "options": ["Makes a variable static", "Prevents modification/inheritance/override", "Marks a method as abstract", "Defines a constructor"], "correct": 1, "difficulty": 3},
        {"text": "Which design pattern uses a single instance throughout an application?", "options": ["Factory", "Observer", "Singleton", "Decorator"], "correct": 2, "difficulty": 3},
        {"text": "What is an interface in Java?", "options": ["A class with only private methods", "A blueprint specifying method signatures without implementations", "A type of constructor", "A way to create anonymous classes"], "correct": 1, "difficulty": 3},
        {"text": "What is the purpose of the 'synchronized' keyword?", "options": ["Makes a method run faster", "Prevents concurrent access to a block by multiple threads", "Makes a variable immutable", "Enables method chaining"], "correct": 1, "difficulty": 3},
        # Difficulty 4
        {"text": "What is the time complexity of HashMap.get() in Java?", "options": ["O(n)", "O(log n)", "O(1) average", "O(n²)"], "correct": 2, "difficulty": 4},
        {"text": "What is a functional interface in Java 8+?", "options": ["An interface with multiple abstract methods", "An interface with exactly one abstract method", "An interface that extends Runnable", "An abstract class with no fields"], "correct": 1, "difficulty": 4},
        {"text": "What does the Stream.flatMap() method do?", "options": ["Filters elements from the stream", "Transforms each element into a single value", "Flattens nested streams into one stream", "Counts the elements"], "correct": 2, "difficulty": 4},
        {"text": "What is the purpose of the volatile keyword in Java?", "options": ["Prevents garbage collection", "Ensures visibility of a variable across threads", "Locks an object for one thread", "Makes a field serialisable"], "correct": 1, "difficulty": 4},
        {"text": "What is method reference syntax in Java 8?", "options": ["ClassName->methodName", "ClassName::methodName", "ClassName.methodName()", "@methodName"], "correct": 1, "difficulty": 4},
        # Difficulty 5 — Expert
        {"text": "What is the difference between ReentrantLock and synchronized in Java?", "options": ["No difference", "ReentrantLock provides more control (try-lock, timed lock, fairness)", "synchronized is faster than ReentrantLock in all cases", "ReentrantLock only works on static methods"], "correct": 1, "difficulty": 5},
        {"text": "What is the Java Memory Model's happens-before relationship?", "options": ["A compile-time optimisation", "A guarantee about ordering and visibility of memory operations across threads", "A GC strategy", "A way to avoid stack overflow"], "correct": 1, "difficulty": 5},
        {"text": "What does CompletableFuture.thenCompose() do?", "options": ["Combines two futures by running them in parallel", "Chains a dependent async computation returning a new CompletableFuture", "Converts a Future to a CompletableFuture", "Cancels the future if it takes too long"], "correct": 1, "difficulty": 5},
        {"text": "What is the main purpose of the Fork/Join framework?", "options": ["Managing database connections", "Breaking large tasks into smaller subtasks processed in parallel", "Handling I/O operations asynchronously", "Managing thread local storage"], "correct": 1, "difficulty": 5},
        {"text": "What is the difference between Comparable and Comparator in Java?", "options": ["No difference", "Comparable defines natural ordering on the class itself; Comparator defines external ordering", "Comparator is used only for primitives", "Comparable requires two objects; Comparator requires one"], "correct": 1, "difficulty": 5},
    ],
    "Python Developer": [
        {"text": "Which keyword defines a function in Python?", "options": ["function", "def", "func", "define"], "correct": 1, "difficulty": 1},
        {"text": "What is the correct way to create a list?", "options": ["x = []", "x = ()", "x = {}", "x = <>"], "correct": 0, "difficulty": 1},
        {"text": "How do you write a comment in Python?", "options": ["// comment", "/* comment */", "# comment", "<!-- comment -->"], "correct": 2, "difficulty": 1},
        {"text": "Which method adds an element to a list?", "options": ["add()", "append()", "insert()", "push()"], "correct": 1, "difficulty": 1},
        {"text": "What does len() return for 'hello'?", "options": ["4", "5", "6", "None"], "correct": 1, "difficulty": 1},
        {"text": "What is a tuple in Python?", "options": ["A mutable list", "An immutable sequence", "A key-value store", "A set of unique items"], "correct": 1, "difficulty": 2},
        {"text": "How do you open a file for reading in Python?", "options": ["open('file', 'w')", "open('file', 'r')", "file.open('r')", "read('file')"], "correct": 1, "difficulty": 2},
        {"text": "What is a lambda function?", "options": ["A named function", "A class method", "An anonymous inline function", "A generator function"], "correct": 2, "difficulty": 2},
        {"text": "What does *args do in a function?", "options": ["Passes keyword arguments", "Passes a fixed number of args", "Passes variable positional arguments", "Makes all args optional"], "correct": 2, "difficulty": 2},
        {"text": "What is list comprehension?", "options": ["Sorting a list", "A concise way to build lists with inline logic", "Filtering None values", "Joining two lists"], "correct": 1, "difficulty": 2},
        {"text": "What is the difference between a list and a generator?", "options": ["No difference", "Generators evaluate lazily; lists are eager", "Lists are immutable; generators are mutable", "Generators can only yield strings"], "correct": 1, "difficulty": 3},
        {"text": "What does @property do in Python?", "options": ["Marks a method as a class method", "Allows a method to be accessed as an attribute", "Makes a method private", "Decorates a method as static"], "correct": 1, "difficulty": 3},
        {"text": "What is a context manager?", "options": ["A thread synchronisation tool", "An object that manages resource setup/teardown via with statement", "A class that manages global state", "A tool for profiling code"], "correct": 1, "difficulty": 3},
        {"text": "What is GIL in Python?", "options": ["Global Import Library", "Global Interpreter Lock preventing multiple threads from executing Python bytecode simultaneously", "A garbage collection mechanism", "An async I/O event loop"], "correct": 1, "difficulty": 3},
        {"text": "What is the purpose of __slots__?", "options": ["Prevents subclassing", "Restricts instance attributes to save memory", "Enables multiple inheritance", "Locks class attributes"], "correct": 1, "difficulty": 3},
        {"text": "What is asyncio.gather() used for?", "options": ["Collects exceptions from coroutines", "Runs multiple coroutines concurrently and waits for all", "Cancels running coroutines", "Schedules a callback"], "correct": 1, "difficulty": 4},
        {"text": "What does functools.lru_cache do?", "options": ["Clears the function cache", "Memoizes function results to speed up repeated calls", "Limits recursion depth", "Logs function calls"], "correct": 1, "difficulty": 4},
        {"text": "What is a metaclass in Python?", "options": ["A subclass of object", "A class whose instances are classes", "A decorator for class methods", "A singleton pattern implementation"], "correct": 1, "difficulty": 4},
        {"text": "What is the difference between deepcopy and copy?", "options": ["No difference", "copy makes a shallow copy; deepcopy recursively copies nested objects", "deepcopy only works on dicts", "copy creates a new reference"], "correct": 1, "difficulty": 4},
        {"text": "What is a descriptor in Python?", "options": ["A docstring format", "An object implementing __get__, __set__, or __delete__ for attribute access control", "A type annotation tool", "A way to mark private fields"], "correct": 1, "difficulty": 4},
        {"text": "What is the MRO (Method Resolution Order) in Python?", "options": ["The order methods are deleted", "The order Python searches base classes for method lookups in multiple inheritance", "A decorator resolution algorithm", "The order in which imports are resolved"], "correct": 1, "difficulty": 5},
        {"text": "What does __init_subclass__ do?", "options": ["Prevents subclassing", "Called automatically when a class is subclassed, allowing the parent to customise it", "Replaces __init__ for all subclasses", "Registers the subclass globally"], "correct": 1, "difficulty": 5},
        {"text": "What is the difference between threading.Event and threading.Condition?", "options": ["No difference", "Event is a simple flag; Condition supports waiting for a specific state with notify/wait", "Condition is only for async code", "Event requires a lock"], "correct": 1, "difficulty": 5},
        {"text": "What does sys.intern() do?", "options": ["Imports a module internally", "Caches a string object so identical strings share memory", "Converts bytes to a string", "Locks a module namespace"], "correct": 1, "difficulty": 5},
        {"text": "What is a C extension in Python?", "options": ["A file ending in .cx", "A Python module written in C to improve performance or access OS APIs", "A type of class decorator", "A compiled bytecode file"], "correct": 1, "difficulty": 5},
    ],
    "Web Developer": [
        {"text": "What does HTML stand for?", "options": ["Hyper Text Markup Language", "Home Tool Markup Language", "Hyperlinks and Text Markup Language", "Hyper Text Making Language"], "correct": 0, "difficulty": 1},
        {"text": "Which CSS property changes text colour?", "options": ["font-color", "text-color", "color", "foreground-color"], "correct": 2, "difficulty": 1},
        {"text": "What is the correct HTML element for the largest heading?", "options": ["<h6>", "<h1>", "<heading>", "<header>"], "correct": 1, "difficulty": 1},
        {"text": "What does CSS stand for?", "options": ["Cascading Style Sheets", "Creative Style Syntax", "Coloured Style Sheets", "Computer Style System"], "correct": 0, "difficulty": 1},
        {"text": "Which tag creates a hyperlink in HTML?", "options": ["<link>", "<href>", "<a>", "<url>"], "correct": 2, "difficulty": 1},
        {"text": "What is the box model in CSS?", "options": ["A layout for 3D elements", "Content, padding, border, margin model for sizing elements", "A flexbox layout pattern", "A grid template", ], "correct": 1, "difficulty": 2},
        {"text": "What does 'position: absolute' do?", "options": ["Fixes the element relative to the viewport", "Positions relative to the nearest positioned ancestor", "Removes the element from the document flow entirely", "Floats the element left"], "correct": 1, "difficulty": 2},
        {"text": "What is a Promise in JavaScript?", "options": ["A strict equality check", "An object representing the eventual result of an async operation", "A type of loop", "A way to declare constants"], "correct": 1, "difficulty": 2},
        {"text": "What does the DOM stand for?", "options": ["Document Object Model", "Data Output Module", "Dynamic Object Method", "Design Object Map"], "correct": 0, "difficulty": 2},
        {"text": "Which HTTP method is used to submit form data?", "options": ["GET", "POST", "PUT", "DELETE"], "correct": 1, "difficulty": 2},
        {"text": "What is event bubbling in JavaScript?", "options": ["Creating multiple events simultaneously", "An event propagating from target element up through the DOM tree", "A memory leak pattern", "An animation technique"], "correct": 1, "difficulty": 3},
        {"text": "What is the purpose of async/await in JavaScript?", "options": ["Makes code run in parallel automatically", "Provides cleaner syntax for handling Promises", "Converts callbacks to generators", "Prevents blocking the UI thread always"], "correct": 1, "difficulty": 3},
        {"text": "What is CORS?", "options": ["A CSS preprocessor", "A security mechanism controlling cross-origin HTTP requests", "A JavaScript testing framework", "A web server protocol"], "correct": 1, "difficulty": 3},
        {"text": "What is React's virtual DOM?", "options": ["A server-side rendering technique", "A lightweight in-memory representation of the real DOM for efficient updates", "A browser extension for React debugging", "A CSS-in-JS solution"], "correct": 1, "difficulty": 3},
        {"text": "What does localStorage.setItem() do?", "options": ["Stores data in a cookie", "Stores a key-value pair persistently in the browser", "Sends data to the server", "Creates a session variable"], "correct": 1, "difficulty": 3},
        {"text": "What is the difference between REST and GraphQL?", "options": ["No difference", "REST uses fixed endpoints per resource; GraphQL uses a single endpoint with flexible queries", "GraphQL only works with SQL databases", "REST is faster in all cases"], "correct": 1, "difficulty": 4},
        {"text": "What is code splitting in React?", "options": ["Breaking CSS into modules", "Splitting a React bundle into smaller chunks loaded on demand", "Separating business logic from UI", "A way to share state between components"], "correct": 1, "difficulty": 4},
        {"text": "What is a service worker?", "options": ["A background Node.js process", "A script running in the browser background to enable offline capabilities and caching", "A REST API middleware", "A CSS animation worker"], "correct": 1, "difficulty": 4},
        {"text": "What is server-side rendering (SSR)?", "options": ["Rendering HTML on the client", "Generating HTML on the server and sending it to the browser", "A webpack optimisation", "A way to cache API responses"], "correct": 1, "difficulty": 4},
        {"text": "What is the Content Security Policy header?", "options": ["Limits request body size", "Defines allowed sources for scripts, styles, and other resources to prevent XSS", "Sets CORS policies", "Controls browser caching"], "correct": 1, "difficulty": 4},
        {"text": "What is the critical rendering path?", "options": ["The sequence of steps a browser takes to convert HTML/CSS/JS into pixels", "The route to the most important API endpoint", "A React rendering optimisation", "The path to the root DOM node"], "correct": 0, "difficulty": 5},
        {"text": "What is a web socket?", "options": ["An HTTP keep-alive header", "A protocol enabling full-duplex communication between client and server over a single connection", "A DOM API for animations", "A REST API pattern"], "correct": 1, "difficulty": 5},
        {"text": "What does tree shaking do in a JavaScript bundler?", "options": ["Removes duplicate styles", "Eliminates dead code that is imported but never used", "Minifies CSS files", "Splits the bundle by route"], "correct": 1, "difficulty": 5},
        {"text": "What is hydration in SSR frameworks?", "options": ["Adding CSS variables at runtime", "Attaching JavaScript event listeners to server-rendered HTML on the client", "Pre-loading fonts", "A form validation technique"], "correct": 1, "difficulty": 5},
        {"text": "What is the purpose of HTTP/2 multiplexing?", "options": ["Compressing HTTP headers", "Allowing multiple requests/responses over a single TCP connection simultaneously", "Encrypting payloads", "Caching static assets"], "correct": 1, "difficulty": 5},
    ],
    "Data Scientist": [
        {"text": "Which Python library is primarily used for data manipulation?", "options": ["NumPy", "pandas", "Matplotlib", "Scikit-learn"], "correct": 1, "difficulty": 1},
        {"text": "What does CSV stand for?", "options": ["Comma Separated Values", "Computer Standard Values", "Coded Set Variables", "Column Stored Values"], "correct": 0, "difficulty": 1},
        {"text": "What is a DataFrame?", "options": ["A chart type", "A 2D labelled data structure in pandas", "A SQL table type", "A neural network layer"], "correct": 1, "difficulty": 1},
        {"text": "Which library is used for numerical computation in Python?", "options": ["pandas", "NumPy", "Flask", "SQLAlchemy"], "correct": 1, "difficulty": 1},
        {"text": "What does EDA stand for?", "options": ["Exploratory Data Analysis", "Enhanced Data Algorithm", "External Data API", "Event Driven Architecture"], "correct": 0, "difficulty": 1},
        {"text": "What is the purpose of train/test split?", "options": ["To speed up training", "To evaluate model performance on unseen data", "To normalise features", "To balance class labels"], "correct": 1, "difficulty": 2},
        {"text": "What is feature scaling?", "options": ["Reducing feature count", "Normalising features to a common range to improve model convergence", "Adding new features", "Removing correlated features"], "correct": 1, "difficulty": 2},
        {"text": "What is a confusion matrix?", "options": ["A matrix of feature correlations", "A table showing actual vs predicted class outcomes", "A loss function visualisation", "A PCA output"], "correct": 1, "difficulty": 2},
        {"text": "What does overfitting mean?", "options": ["Model is too simple", "Model performs well on training data but poorly on new data", "Model has too few parameters", "Model fails to converge"], "correct": 1, "difficulty": 2},
        {"text": "What is the mean squared error (MSE)?", "options": ["Average of absolute errors", "Average of squared differences between predicted and actual values", "Total prediction error", "Variance of predictions"], "correct": 1, "difficulty": 2},
        {"text": "What is cross-validation?", "options": ["A data augmentation technique", "A resampling method to evaluate model performance on multiple train/test splits", "A hyperparameter tuning algorithm", "A feature selection method"], "correct": 1, "difficulty": 3},
        {"text": "What is the bias-variance tradeoff?", "options": ["A cost function formula", "The balance between underfitting (high bias) and overfitting (high variance)", "A regularisation penalty", "A neural network architecture choice"], "correct": 1, "difficulty": 3},
        {"text": "What is regularisation in machine learning?", "options": ["Normalising input data", "Adding a penalty term to the loss function to reduce overfitting", "Standardising model outputs", "Removing outliers"], "correct": 1, "difficulty": 3},
        {"text": "What is Principal Component Analysis (PCA)?", "options": ["A classification algorithm", "A dimensionality reduction technique that transforms features to maximise variance", "A clustering algorithm", "A missing value imputation method"], "correct": 1, "difficulty": 3},
        {"text": "What does a ROC curve measure?", "options": ["Regression accuracy", "The tradeoff between true positive rate and false positive rate at various thresholds", "Feature importance", "Model training speed"], "correct": 1, "difficulty": 3},
        {"text": "What is gradient descent?", "options": ["A data preprocessing step", "An optimisation algorithm that iteratively adjusts parameters to minimise a loss function", "A feature selection method", "A regularisation technique"], "correct": 1, "difficulty": 4},
        {"text": "What is the vanishing gradient problem?", "options": ["Gradients growing too large during backpropagation", "Gradients becoming extremely small, stalling training in deep networks", "Loss function not converging", "A dataset imbalance issue"], "correct": 1, "difficulty": 4},
        {"text": "What is an ensemble method?", "options": ["A single strong model", "Combining predictions from multiple models to improve performance", "A data augmentation strategy", "A type of regularisation"], "correct": 1, "difficulty": 4},
        {"text": "What is transfer learning?", "options": ["Moving a model to a new server", "Reusing a pre-trained model's weights as a starting point for a new task", "Copying training data between tasks", "A hyperparameter transfer technique"], "correct": 1, "difficulty": 4},
        {"text": "What is the purpose of batch normalisation?", "options": ["Shuffles training batches", "Normalises layer inputs during training to stabilise and speed up learning", "Reduces batch size", "Applies dropout regularisation"], "correct": 1, "difficulty": 4},
        {"text": "What is the kernel trick in SVM?", "options": ["A hyperparameter selection method", "Implicitly mapping data to a higher-dimensional space to find a linear separator", "A dimensionality reduction technique", "A gradient approximation"], "correct": 1, "difficulty": 5},
        {"text": "What is the EM algorithm?", "options": ["Error Minimisation algorithm", "Expectation-Maximisation: iteratively estimates parameters of models with latent variables", "Entropy Maximisation algorithm", "An ensemble method"], "correct": 1, "difficulty": 5},
        {"text": "What is a variational autoencoder (VAE)?", "options": ["A deterministic encoder-decoder", "A generative model that learns a probabilistic latent space", "A supervised classification model", "A type of RNN"], "correct": 1, "difficulty": 5},
        {"text": "What is SHAP in machine learning explainability?", "options": ["A regularisation method", "SHapley Additive exPlanations: a game-theoretic approach to explain individual predictions", "A feature engineering technique", "A gradient-based optimiser"], "correct": 1, "difficulty": 5},
        {"text": "What is the difference between bagging and boosting?", "options": ["No difference", "Bagging trains models independently in parallel; boosting trains sequentially, correcting previous errors", "Boosting uses fewer models", "Bagging only works with decision trees"], "correct": 1, "difficulty": 5},
    ],
    "Mobile App Developer": [
        {"text": "What language is used for native Android development?", "options": ["Swift", "Kotlin", "TypeScript", "Dart"], "correct": 1, "difficulty": 1},
        {"text": "What is Flutter?", "options": ["A JavaScript framework", "A Google UI toolkit for building natively compiled apps from one codebase", "An iOS-only framework", "A backend framework"], "correct": 1, "difficulty": 1},
        {"text": "What file format does Android use for UI layouts?", "options": ["HTML", "XML", "JSON", "YAML"], "correct": 1, "difficulty": 1},
        {"text": "What is an APK?", "options": ["A programming language", "An Android application package file", "An Apple product key", "An API protocol"], "correct": 1, "difficulty": 1},
        {"text": "What is Swift?", "options": ["A cross-platform framework", "Apple's programming language for iOS and macOS development", "A Kotlin competitor for Android", "A UI testing tool"], "correct": 1, "difficulty": 1},
        {"text": "What is the difference between a native and hybrid app?", "options": ["No difference", "Native apps use platform-specific languages; hybrid apps use web technologies wrapped in a native shell", "Hybrid apps are faster", "Native apps cannot access device hardware"], "correct": 1, "difficulty": 2},
        {"text": "What is React Native?", "options": ["A native iOS framework", "A JavaScript framework for building cross-platform mobile apps using React", "A UI component library", "A state management tool"], "correct": 1, "difficulty": 2},
        {"text": "What is an Activity in Android?", "options": ["A database transaction", "A single screen with a user interface", "A background service", "A content provider"], "correct": 1, "difficulty": 2},
        {"text": "What is a ViewModel in Android?", "options": ["A UI layout file", "A component that holds UI-related data and survives configuration changes", "A database model", "A content resolver"], "correct": 1, "difficulty": 2},
        {"text": "What is the purpose of the App Delegate in iOS?", "options": ["Manages memory allocation", "Responds to app lifecycle events and acts as the entry point", "Handles HTTP requests", "Defines the storyboard layout"], "correct": 1, "difficulty": 2},
        {"text": "What is the Flutter widget tree?", "options": ["A list of installed packages", "A hierarchical structure of widgets that defines the UI", "A navigation stack", "A state management pattern"], "correct": 1, "difficulty": 3},
        {"text": "What is dependency injection in mobile development?", "options": ["Importing third-party libraries", "Providing a class's dependencies from outside rather than creating them internally", "Adding platform plugins", "A navigation pattern"], "correct": 1, "difficulty": 3},
        {"text": "What is Jetpack Compose?", "options": ["An Android testing tool", "Android's modern declarative UI toolkit", "A navigation component", "A dependency injection framework"], "correct": 1, "difficulty": 3},
        {"text": "What is the purpose of coroutines in Kotlin?", "options": ["Handling UI events", "Simplifying asynchronous programming with sequential-looking code", "Managing app state", "Database migrations"], "correct": 1, "difficulty": 3},
        {"text": "What is a push notification?", "options": ["An in-app alert", "A message delivered to a device from a server even when the app is not running", "A local notification", "A system sound"], "correct": 1, "difficulty": 3},
        {"text": "What is the Model-View-ViewModel (MVVM) pattern?", "options": ["A database pattern", "An architecture that separates UI (View), data (Model), and presentation logic (ViewModel)", "A navigation pattern", "A testing strategy"], "correct": 1, "difficulty": 4},
        {"text": "What is deep linking in mobile apps?", "options": ["Navigating to a website", "A URI scheme that opens a specific screen inside an app", "A background sync mechanism", "An in-app purchase flow"], "correct": 1, "difficulty": 4},
        {"text": "What is the purpose of App Transport Security (ATS) in iOS?", "options": ["Encrypts local storage", "Requires apps to use HTTPS for all network connections", "Manages app permissions", "Prevents jailbreak detection bypasses"], "correct": 1, "difficulty": 4},
        {"text": "What is the WorkManager API in Android?", "options": ["Manages UI threads", "Schedules deferrable background work that runs even if the app exits", "A database ORM", "A lifecycle-aware component"], "correct": 1, "difficulty": 4},
        {"text": "What is a Content Provider in Android?", "options": ["A network data source", "A component that manages access to a structured set of data and enables data sharing between apps", "A background service", "An intent resolver"], "correct": 1, "difficulty": 4},
        {"text": "What is ProGuard in Android development?", "options": ["A security audit tool", "A tool that shrinks, optimises, and obfuscates code to reduce APK size and improve security", "A static code analyser", "A dependency manager"], "correct": 1, "difficulty": 5},
        {"text": "What is Keychain in iOS?", "options": ["A cryptography library", "A secure storage service for sensitive data like passwords and tokens", "A certificate management tool", "An authentication API"], "correct": 1, "difficulty": 5},
        {"text": "What is the purpose of the @Composable annotation in Jetpack Compose?", "options": ["Marks a class as injectable", "Declares a function as a composable UI element that can be called within the composition", "Marks a function as async", "Defines a ViewModel factory"], "correct": 1, "difficulty": 5},
        {"text": "What is isolate in Flutter/Dart?", "options": ["A UI isolation technique", "A separate thread of execution with its own memory, used for CPU-intensive work", "A state isolation pattern", "A widget subtree boundary"], "correct": 1, "difficulty": 5},
        {"text": "What is bitcode in iOS builds?", "options": ["Binary code for App Store submission", "An intermediate representation of an app that Apple can re-optimise for new hardware", "A debug symbol format", "A code signing mechanism"], "correct": 1, "difficulty": 5},
    ],
    "DevOps Engineer": [
        {"text": "What does CI/CD stand for?", "options": ["Continuous Integration / Continuous Delivery", "Code Integration / Code Deployment", "Cloud Infrastructure / Cloud Delivery", "Container Integration / Container Deployment"], "correct": 0, "difficulty": 1},
        {"text": "What is Docker?", "options": ["A virtual machine", "A platform for building, shipping, and running applications in containers", "A cloud provider", "A CI/CD tool"], "correct": 1, "difficulty": 1},
        {"text": "What is a container?", "options": ["A virtual machine", "A lightweight isolated process with its own filesystem and dependencies", "A cloud storage bucket", "A network namespace only"], "correct": 1, "difficulty": 1},
        {"text": "What is Git?", "options": ["A deployment tool", "A distributed version control system", "A container orchestration tool", "An infrastructure as code tool"], "correct": 1, "difficulty": 1},
        {"text": "What does IaC stand for?", "options": ["Internet as Code", "Infrastructure as Code", "Integrated Application Configuration", "Internal API Contract"], "correct": 1, "difficulty": 1},
        {"text": "What is Kubernetes?", "options": ["A Docker alternative", "An open-source system for automating deployment, scaling, and management of containerised applications", "A cloud provider", "A monitoring tool"], "correct": 1, "difficulty": 2},
        {"text": "What is a Dockerfile?", "options": ["A Docker configuration UI", "A text file containing instructions to build a Docker image", "A Docker networking config", "A Docker Compose override file"], "correct": 1, "difficulty": 2},
        {"text": "What is a load balancer?", "options": ["A database replication tool", "A device or service that distributes traffic across multiple servers", "A network firewall", "A container registry"], "correct": 1, "difficulty": 2},
        {"text": "What is Terraform?", "options": ["A monitoring tool", "An open-source IaC tool for provisioning infrastructure across cloud providers", "A container runtime", "A secrets manager"], "correct": 1, "difficulty": 2},
        {"text": "What is a reverse proxy?", "options": ["A client-side proxy", "A server that forwards requests from clients to backend servers", "A DNS server type", "A load balancing algorithm"], "correct": 1, "difficulty": 2},
        {"text": "What is the difference between blue-green and canary deployments?", "options": ["No difference", "Blue-green switches all traffic between two identical environments; canary gradually shifts traffic to the new version", "Canary is only for databases", "Blue-green requires Kubernetes"], "correct": 1, "difficulty": 3},
        {"text": "What is a Kubernetes Pod?", "options": ["A virtual machine", "The smallest deployable unit in Kubernetes, containing one or more containers", "A namespace boundary", "A Kubernetes node"], "correct": 1, "difficulty": 3},
        {"text": "What is Prometheus used for?", "options": ["Log aggregation", "Open-source monitoring and alerting with time-series metrics", "Container image storage", "Service mesh management"], "correct": 1, "difficulty": 3},
        {"text": "What is the purpose of an Nginx reverse proxy?", "options": ["Compiling applications", "Handling SSL termination, load balancing, and routing to backend services", "Running container workloads", "Managing DNS records"], "correct": 1, "difficulty": 3},
        {"text": "What is a Helm chart?", "options": ["A Kubernetes monitoring dashboard", "A package of Kubernetes YAML manifests that can be versioned and deployed as a unit", "A CI/CD pipeline template", "A Docker image format"], "correct": 1, "difficulty": 3},
        {"text": "What is GitOps?", "options": ["A Git branching strategy", "An operational framework using Git as the source of truth for infrastructure and app config", "A CI/CD tool", "A Kubernetes plugin"], "correct": 1, "difficulty": 4},
        {"text": "What is service mesh?", "options": ["A Docker network driver", "An infrastructure layer handling service-to-service communication (traffic, security, observability)", "A cloud networking product", "A Kubernetes storage class"], "correct": 1, "difficulty": 4},
        {"text": "What is eBPF?", "options": ["An HTTP protocol extension", "A kernel technology for running sandboxed programs to observe and modify OS behaviour", "A container networking standard", "An encryption protocol"], "correct": 1, "difficulty": 4},
        {"text": "What is the purpose of OPA (Open Policy Agent)?", "options": ["Container image scanning", "A general-purpose policy engine for enforcing authorisation policies across the stack", "A secret rotation tool", "A log aggregation tool"], "correct": 1, "difficulty": 4},
        {"text": "What is a sidecar container pattern?", "options": ["A backup container", "An auxiliary container in a Pod that extends/enhances the main container's functionality", "A load balancer container", "A database connection pool"], "correct": 1, "difficulty": 4},
        {"text": "What is chaos engineering?", "options": ["Deploying broken code intentionally", "Deliberately injecting failures into a system to uncover weaknesses before they cause outages", "A random deployment strategy", "A security testing approach"], "correct": 1, "difficulty": 5},
        {"text": "What is the CAP theorem?", "options": ["A Kubernetes scheduling algorithm", "The impossibility of guaranteeing consistency, availability, and partition tolerance simultaneously", "A cloud cost model", "A container isolation framework"], "correct": 1, "difficulty": 5},
        {"text": "What is distributed tracing?", "options": ["Logging every network packet", "Tracking a request as it propagates through multiple services in a distributed system", "A Kubernetes audit log feature", "A load balancing algorithm"], "correct": 1, "difficulty": 5},
        {"text": "What is SPIFFE/SPIRE?", "options": ["A secret management tool", "A framework for establishing and verifying workload identity in distributed systems", "A network policy enforcer", "A container runtime security tool"], "correct": 1, "difficulty": 5},
        {"text": "What is the purpose of a circuit breaker pattern?", "options": ["Rotating TLS certificates", "Preventing cascading failures by stopping calls to a failing service and allowing it to recover", "Balancing microservice load", "Managing database connection pools"], "correct": 1, "difficulty": 5},
    ],
}


def seed_roles(session):
    """Insert student and admin roles if they don't already exist."""
    for name in ROLES:
        if not session.query(Role).filter_by(name=name).first():
            session.add(Role(name=name))
            print(f"  + Role: {name}")
        else:
            print(f"  ~ Role already exists: {name}")
    session.commit()


def seed_goals(session):
    """Insert learning goals if they don't already exist. Returns goal name → object map."""
    goal_map = {}
    for g in GOALS:
        existing = session.query(Goal).filter_by(name=g["name"]).first()
        if not existing:
            goal_obj = Goal(name=g["name"], description=g["description"])
            session.add(goal_obj)
            session.flush()  # get the generated UUID
            goal_map[g["name"]] = goal_obj
            print(f"  + Goal: {g['name']}")
        else:
            goal_map[g["name"]] = existing
            print(f"  ~ Goal already exists: {g['name']}")
    session.commit()
    return goal_map


def seed_questions(session, goal_map):
    """Insert quiz questions for every goal at each difficulty level."""
    total_added = 0
    for goal_name, questions in QUIZ_QUESTIONS.items():
        goal = goal_map.get(goal_name)
        if goal is None:
            print(f"  ! Goal not found: {goal_name} — skipping questions")
            continue
        for q in questions:
            exists = (
                session.query(QuizQuestion)
                .filter_by(goal_id=goal.id, question_text=q["text"])
                .first()
            )
            if not exists:
                session.add(
                    QuizQuestion(
                        goal_id=goal.id,
                        question_text=q["text"],
                        options=q["options"],
                        correct_option_index=q["correct"],
                        difficulty=q["difficulty"],
                        source=QuestionSource.seeded,
                    )
                )
                total_added += 1
    session.commit()
    print(f"  + {total_added} quiz questions added")


def run():
    """Entry point — creates app context and seeds the database."""
    print("Starting database seeding...")
    app = create_app("development")
    with app.app_context():
        print("\n[1/3] Seeding roles...")
        seed_roles(db.session)

        print("\n[2/3] Seeding goals...")
        goal_map = seed_goals(db.session)

        print("\n[3/3] Seeding quiz questions...")
        seed_questions(db.session, goal_map)

    print("\nSeeding complete.")


if __name__ == "__main__":
    run()
