import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.urandom(24)

DATA_DIR = os.path.join(os.path.dirname(__file__), "lms_data")
os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================
# DATA MODELS & STORAGE
# ============================================================

class DataStore:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def _filepath(self, filename: str) -> str:
        return os.path.join(self.data_dir, filename)

    def save(self, filename: str, data: dict):
        with open(self._filepath(filename), 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load(self, filename: str) -> dict:
        path = self._filepath(filename)
        if os.path.exists(path):
            with open(path, 'r') as f:
                return json.load(f)
        return {}

store = DataStore()

# ============================================================
# ACHIEVEMENT SYSTEM
# ============================================================

class Achievement:
    def __init__(self, id: str, name: str, description: str, icon: str, criteria: dict):
        self.id = id
        self.name = name
        self.description = description
        self.icon = icon
        self.criteria = criteria

ACHIEVEMENTS = [
    Achievement("first_login", "Welcome Aboard!", "Log in for the first time", "🎉", {"type": "first_login"}),
    Achievement("first_chapter", "Chapter One Done!", "Complete your first chapter", "📖", {"type": "chapters_completed", "value": 1}),
    Achievement("half_way", "Halfway There!", "Complete 50% of all chapters", "🏃", {"type": "chapters_percent", "value": 50}),
    Achievement("all_chapters", "Scholar!", "Complete all chapters", "🎓", {"type": "chapters_percent", "value": 100}),
    Achievement("perfect_quiz", "Perfect Score!", "Score 100% on any quiz", "💯", {"type": "quiz_score", "value": 100}),
    Achievement("quiz_streak_3", "On Fire!", "Pass 3 quizzes in a row", "🔥", {"type": "quiz_streak", "value": 3}),
    Achievement("quiz_streak_5", "Unstoppable!", "Pass 5 quizzes in a row", "⚡", {"type": "quiz_streak", "value": 5}),
    Achievement("persistence", "Never Give Up!", "Retry and pass a failed quiz", "💪", {"type": "retry_pass"}),
    Achievement("speed_learner", "Speed Learner!", "Complete a chapter in under 2 minutes", "🚀", {"type": "speed_complete", "value": 120}),
    Achievement("bookworm", "Bookworm!", "Read all lesson content in a chapter", "🐛", {"type": "all_content_read"}),
    Achievement("five_quizzes", "Quiz Master!", "Pass 5 quizzes total", "🧠", {"type": "total_quizzes_passed", "value": 5}),
    Achievement("ten_quizzes", "Quiz Legend!", "Pass 10 quizzes total", "👑", {"type": "total_quizzes_passed", "value": 10}),
    Achievement("certified", "Certified!", "Earn your completion certificate", "🏆", {"type": "certificate_earned"}),
]

# ============================================================
# COURSE CONTENT
# ============================================================

class Question:
    def __init__(self, text: str, options: List[str], correct_index: int, explanation: str = ""):
        self.text = text
        self.options = options
        self.correct_index = correct_index
        self.explanation = explanation

    def to_dict(self):
        return {"text": self.text, "options": self.options, "correct_index": self.correct_index, "explanation": self.explanation}

class Quiz:
    def __init__(self, quiz_id: str, title: str, questions: List[Question], passing_score: int = 70):
        self.quiz_id = quiz_id
        self.title = title
        self.questions = questions
        self.passing_score = passing_score

class Lesson:
    def __init__(self, lesson_id: str, title: str, content: str):
        self.lesson_id = lesson_id
        self.title = title
        self.content = content

class Chapter:
    def __init__(self, chapter_id: str, title: str, description: str, lessons: List[Lesson], quizzes: List[Quiz]):
        self.chapter_id = chapter_id
        self.title = title
        self.description = description
        self.lessons = lessons
        self.quizzes = quizzes

class Course:
    def __init__(self, title: str, description: str, chapters: List[Chapter]):
        self.title = title
        self.description = description
        self.chapters = chapters

course = None

def create_python_course() -> Course:
    ch1_lessons = [
        Lesson("1-1", "What is Python?", """
WHAT IS PYTHON?

Python is a high-level, interpreted programming language created by Guido van Rossum and first released in 1991.

KEY FEATURES:
  - Easy to read and write (clean syntax)
  - Interpreted (no compilation needed)
  - Dynamically typed
  - Huge standard library
  - Cross-platform (Windows, Mac, Linux)

USED FOR:
  - Web Development (Django, Flask)
  - Data Science & AI (NumPy, TensorFlow)
  - Automation & Scripting
  - Game Development
  - Desktop Applications

Python uses indentation (whitespace) to define code blocks, making it visually clean and easy to understand.
        """),
        Lesson("1-2", "Installing Python & Your First Program", """
YOUR FIRST PYTHON PROGRAM

INSTALLATION:
  1. Visit python.org
  2. Download the latest version (3.x)
  3. Run the installer (check "Add to PATH")
  4. Open terminal/command prompt
  5. Type: python --version

YOUR FIRST PROGRAM:
    print("Hello, World!")
    # Output: Hello, World!

RUNNING PYTHON:
  - Interactive mode: Type 'python' in terminal
  - Script mode: Save as .py file, run with 'python filename.py'

COMMENTS:
  # This is a single-line comment
  '''This is a multi-line comment'''
        """),
    ]

    ch1_qa = Quiz("1-A", "Chapter 1 Quiz - Version A", [
        Question("Who created Python?", ["James Gosling", "Guido van Rossum", "Dennis Ritchie", "Bjarne Stroustrup"], 1, "Guido van Rossum created Python, first released in 1991."),
        Question("What type of language is Python?", ["Compiled", "Interpreted", "Assembly", "Machine"], 1, "Python is an interpreted language - code runs line by line."),
        Question("What does print('Hello') do?", ["Saves text to a file", "Displays 'Hello' on screen", "Creates a variable", "Nothing"], 1, "The print() function outputs text to the console."),
        Question("How does Python define code blocks?", ["Curly braces {}", "Indentation/whitespace", "Parentheses ()", "Square brackets []"], 1, "Python uniquely uses indentation to define code blocks."),
        Question("What file extension do Python scripts use?", [".java", ".py", ".cpp", ".js"], 1, "Python files use the .py extension."),
    ], passing_score=60)

    ch1_qb = Quiz("1-B", "Chapter 1 Quiz - Version B", [
        Question("When was Python first released?", ["1985", "1991", "2000", "1995"], 1, "Python was first released in 1991."),
        Question("Which is NOT a use case for Python?", ["Web Development", "Data Science", "Operating System Kernels", "Automation"], 2, "Python is rarely used for OS kernel development (that's typically C)."),
        Question("What symbol starts a single-line comment in Python?", ["//", "#", "/*", "--"], 1, "The # symbol is used for single-line comments in Python."),
        Question("Python is dynamically typed. What does this mean?", ["You must declare variable types", "Variable types are determined at runtime", "It only works with numbers", "It requires a compiler"], 1, "Dynamic typing means types are checked at runtime, not compile time."),
        Question("Which command checks your Python version?", ["python --version", "python -check", "python /v", "python info"], 0, "The command 'python --version' displays the installed version."),
    ], passing_score=60)

    ch1_qc = Quiz("1-C", "Chapter 1 Quiz - Version C", [
        Question("Python code is known for being:", ["Hard to read", "Readable and clean", "Only for experts", "Verbose"], 1, "Python's clean syntax makes it very readable."),
        Question("Which framework is used for web development in Python?", ["React", "Angular", "Django", "Spring"], 2, "Django is a popular Python web framework."),
        Question("What is the output of: print(2 + 3)?", ["23", "5", "2 + 3", "Error"], 1, "Python evaluates the expression 2+3=5, then prints it."),
        Question("Which is the correct way to run a Python script?", ["python myfile.py", "run myfile.py", "execute myfile.py", "start myfile.py"], 0, "Use 'python filename.py' to run a script."),
        Question("Python's standard library is:", ["Very small", "Non-existent", "Huge and comprehensive", "Only for math"], 2, "Python has a massive standard library covering many domains."),
    ], passing_score=60)

    chapter1 = Chapter("ch1", "Introduction to Python", "Learn what Python is, how to install it, and write your first program.", ch1_lessons, [ch1_qa, ch1_qb, ch1_qc])

    ch2_lessons = [
        Lesson("2-1", "Variables", """
VARIABLES

A variable is a named container that stores data.

CREATING VARIABLES:
    name = "Alice"          # string
    age = 25                # integer
    height = 5.6            # float
    is_student = True       # boolean

NAMING RULES:
  - Must start with a letter or underscore
  - Can contain letters, numbers, underscores
  - Cannot start with a number
  - Cannot use reserved words (if, for, while, etc.)
  - Case-sensitive (Name != name)
        """),
        Lesson("2-2", "Data Types", """
DATA TYPES

Python has several built-in data types:

NUMERIC TYPES:
    x = 10        # int (integer)
    y = 3.14      # float (decimal)
    z = 2 + 3j    # complex

TEXT TYPE:
    name = "Hello"    # str (string)
    char = 'A'        # also a string

BOOLEAN TYPE:
    is_active = True   # bool
    is_done = False    # bool

TYPE CHECKING:
    type(10)      -> <class 'int'>
    type("Hi")    -> <class 'str'>
    type(3.14)    -> <class 'float'>
    type(True)    -> <class 'bool'>

TYPE CONVERSION:
    int("5")    -> 5      (string to int)
    str(10)     -> "10"   (int to string)
    float(3)    -> 3.0    (int to float)
        """),
    ]

    ch2_qa = Quiz("2-A", "Chapter 2 Quiz - Version A", [
        Question("Which is a valid variable name?", ["2name", "my-var", "my_var", "class"], 2, "my_var follows Python naming rules. It uses letters and underscore."),
        Question("What data type is 3.14?", ["int", "str", "float", "bool"], 2, "3.14 is a decimal number, which is a float."),
        Question("What does type('Hello') return?", ["<class 'int'>", "<class 'str'>", "<class 'float'>", "<class 'list'>"], 1, "'Hello' is a string, so type() returns <class 'str'>."),
        Question("What is the result of int('5')?", ["'5'", "5", "Error", "5.0"], 1, "int('5') converts the string '5' to the integer 5."),
        Question("Which is a boolean value?", ["'True'", "1", "True", "yes"], 2, "True (without quotes) is a boolean. 'True' is a string."),
    ], passing_score=60)

    ch2_qb = Quiz("2-B", "Chapter 2 Quiz - Version B", [
        Question("What will x be after: x = 10?", ["A string", "An integer with value 10", "A float", "Undefined"], 1, "x = 10 assigns the integer value 10 to variable x."),
        Question("Which variable name is invalid?", ["_count", "myVar", "3rd_place", "student_name"], 2, "Variable names cannot start with a number."),
        Question("What does float(3) return?", ["3", "'3'", "3.0", "Error"], 2, "float(3) converts integer 3 to float 3.0."),
        Question("Are variable names case-sensitive in Python?", ["Yes", "No", "Only for strings", "Only for numbers"], 0, "Python is case-sensitive: 'Name' and 'name' are different."),
        Question("What type is the value True?", ["str", "int", "bool", "float"], 2, "True is a boolean (bool) value."),
    ], passing_score=60)

    ch2_qc = Quiz("2-C", "Chapter 2 Quiz - Version C", [
        Question("What is a variable?", ["A type of loop", "A named container for data", "A function", "A Python module"], 1, "Variables are named containers that store data values."),
        Question("Which stores a decimal number?", ["int", "str", "float", "bool"], 2, "Float (floating-point) stores decimal numbers."),
        Question("What happens with: str(42)?", ["Error", "Returns 42", "Returns '42'", "Returns 42.0"], 2, "str(42) converts the integer to the string '42'."),
        Question("Which can be a variable name?", ["for", "while", "student_age", "import"], 2, "student_age is valid; the others are reserved keywords."),
        Question("What is the result of type(True)?", ["<class 'str'>", "<class 'int'>", "<class 'bool'>", "<class 'true'>"], 2, "True is a boolean, so type returns <class 'bool'>."),
    ], passing_score=60)

    chapter2 = Chapter("ch2", "Variables & Data Types", "Learn how to store data using variables and understand Python's data types.", ch2_lessons, [ch2_qa, ch2_qb, ch2_qc])

    ch3_lessons = [
        Lesson("3-1", "If/Else Statements", """
IF / ELSE STATEMENTS

Control flow lets your program make decisions.

BASIC IF:
    age = 18
    if age >= 18:
        print("You are an adult")

IF/ELSE:
    score = 75
    if score >= 60:
        print("You passed!")
    else:
        print("Try again.")

IF/ELIF/ELSE:
    grade = 85
    if grade >= 90:
        print("A")
    elif grade >= 80:
        print("B")
    elif grade >= 70:
        print("C")
    else:
        print("F")

COMPARISON OPERATORS:
    ==  Equal to          !=  Not equal to
    >   Greater than      <   Less than
    >=  Greater or equal  <=  Less or equal
        """),
        Lesson("3-2", "Loops", """
LOOPS

Loops let you repeat code multiple times.

FOR LOOP:
    for i in range(5):
        print(i)    # prints 0,1,2,3,4

    fruits = ["apple", "banana", "cherry"]
    for fruit in fruits:
        print(fruit)

WHILE LOOP:
    count = 0
    while count < 5:
        print(count)
        count += 1

LOOP CONTROL:
    break     -> Exit the loop immediately
    continue  -> Skip to the next iteration
    pass      -> Do nothing (placeholder)
        """),
    ]

    ch3_qa = Quiz("3-A", "Chapter 3 Quiz - Version A", [
        Question("What keyword is used for conditional statements?", ["for", "while", "if", "def"], 2, "'if' is used to create conditional statements."),
        Question("What does 'elif' stand for?", ["else if", "eliminate if", "element if", "else ignore"], 0, "'elif' is short for 'else if'."),
        Question("What does range(5) generate?", ["1,2,3,4,5", "0,1,2,3,4", "0,1,2,3,4,5", "1,2,3,4"], 1, "range(5) generates numbers 0 through 4."),
        Question("What does 'break' do in a loop?", ["Pauses the loop", "Exits the loop immediately", "Skips one iteration", "Restarts the loop"], 1, "'break' immediately exits the loop."),
        Question("Which operator checks equality?", ["=", "==", "!=", ">="], 1, "== checks if two values are equal. = is assignment."),
    ], passing_score=60)

    ch3_qb = Quiz("3-B", "Chapter 3 Quiz - Version B", [
        Question("What will this print? if 5 > 3: print('Yes') else: print('No')", ["Yes", "No", "Error", "Nothing"], 0, "5 > 3 is True, so 'Yes' is printed."),
        Question("Which loop is best for iterating over a list?", ["while", "for", "do-while", "switch"], 1, "A 'for' loop is ideal for iterating over sequences like lists."),
        Question("What does 'continue' do?", ["Exits the loop", "Skips to the next iteration", "Pauses execution", "Repeats the current iteration"], 1, "'continue' skips the rest of the current iteration."),
        Question("How do you write 'not equal' in Python?", ["<>", "!=", "=/=", "not="], 1, "!= is the 'not equal' operator in Python."),
        Question("What does range(2, 8) generate?", ["2,3,4,5,6,7,8", "2,3,4,5,6,7", "3,4,5,6,7", "2,3,4,5,6,7,8,9"], 1, "range(2,8) generates 2 through 7 (end is exclusive)."),
    ], passing_score=60)

    ch3_qc = Quiz("3-C", "Chapter 3 Quiz - Version C", [
        Question("What is the output? count=0; while count<3: print(count); count+=1", ["0 1 2 3", "0 1 2", "1 2 3", "Infinite loop"], 1, "Prints 0, 1, 2. When count reaches 3, the condition is False."),
        Question("Which is NOT a comparison operator?", ["==", ">=", "!=", "="], 3, "= is the assignment operator, not a comparison operator."),
        Question("What does 'pass' do in Python?", ["Exits the program", "Nothing (placeholder)", "Passes a value", "Skips a line"], 1, "'pass' is a null operation — it does nothing. Used as a placeholder."),
        Question("How many times does this loop run? for i in range(1, 6): print(i)", ["4", "5", "6", "Infinite"], 1, "range(1,6) produces 1,2,3,4,5 — that's 5 iterations."),
        Question("Can you nest if statements inside loops?", ["Yes", "No", "Only in for loops", "Only in while loops"], 0, "You can nest any control structure inside any other."),
    ], passing_score=60)

    chapter3 = Chapter("ch3", "Control Flow", "Learn how to control program flow with conditions and loops.", ch3_lessons, [ch3_qa, ch3_qb, ch3_qc])

    ch4_lessons = [
        Lesson("4-1", "Defining Functions", """
FUNCTIONS

Functions are reusable blocks of code that perform specific tasks.

DEFINING A FUNCTION:
    def greet(name):
        print(f"Hello, {name}!")

    greet("Alice")  # Hello, Alice!

RETURN VALUES:
    def add(a, b):
        return a + b

    result = add(3, 5)  # result = 8

DEFAULT PARAMETERS:
    def greet(name, greeting="Hello"):
        print(f"{greeting}, {name}!")

    greet("Bob")           # Hello, Bob!
    greet("Bob", "Hi")     # Hi, Bob!

WHY USE FUNCTIONS?
  - Reusability - Write once, use many times
  - Organization - Break complex code into parts
  - Readability - Named blocks are easier to understand
  - Testing - Easier to test small pieces
        """),
        Lesson("4-2", "Scope & Advanced Functions", """
SCOPE & ADVANCED FUNCTIONS

VARIABLE SCOPE:
    x = "global"        # global scope

    def my_func():
        y = "local"     # local scope
        print(x)        # can see global
        print(y)        # can see local

    my_func()
    print(y)  # ERROR! y is local

MULTIPLE RETURN VALUES:
    def min_max(numbers):
        return min(numbers), max(numbers)

    lo, hi = min_max([3, 1, 7, 2])
    # lo = 1, hi = 7

*ARGS AND **KWARGS:
    def total(*args):
        return sum(args)

    total(1, 2, 3)      # returns 6
    total(10, 20)       # returns 30

LAMBDA FUNCTIONS (anonymous):
    square = lambda x: x ** 2
    square(5)           # returns 25
        """),
    ]

    ch4_qa = Quiz("4-A", "Chapter 4 Quiz - Version A", [
        Question("What keyword defines a function in Python?", ["function", "def", "func", "define"], 1, "The 'def' keyword is used to define functions."),
        Question("What does 'return' do in a function?", ["Prints a value", "Sends a value back to the caller", "Stops the program", "Creates a variable"], 1, "'return' sends a value back to where the function was called."),
        Question("What is the output? def add(a, b=5): return a+b; print(add(3))", ["3", "5", "8", "Error"], 2, "a=3, b defaults to 5, so 3+5=8."),
        Question("What is variable scope?", ["Variable speed", "Where a variable can be accessed", "Variable size", "Variable type"], 1, "Scope determines where a variable is accessible in code."),
        Question("What is a lambda function?", ["A named function", "An anonymous inline function", "A built-in function", "A class method"], 1, "Lambda creates small anonymous functions inline."),
    ], passing_score=60)

    ch4_qb = Quiz("4-B", "Chapter 4 Quiz - Version B", [
        Question("What happens if a function has no return statement?", ["Error", "Returns 0", "Returns None", "Returns empty string"], 2, "Functions without return statements return None."),
        Question("Can a function call another function?", ["Yes", "No", "Only built-in functions", "Only with import"], 0, "Functions can absolutely call other functions."),
        Question("What does *args allow?", ["Named arguments", "Variable number of arguments", "Default arguments", "No arguments"], 1, "*args allows passing a variable number of positional arguments."),
        Question("What is a default parameter?", ["A parameter that can't be changed", "A parameter with a pre-set value", "The first parameter", "A required parameter"], 1, "Default parameters have pre-set values used if no argument is given."),
        Question("Why are functions important?", ["They make code slower", "They enable code reuse and organization", "They are required by Python", "They replace variables"], 1, "Functions promote code reuse, organization, and readability."),
    ], passing_score=60)

    ch4_qc = Quiz("4-C", "Chapter 4 Quiz - Version C", [
        Question("What is wrong with this code? def greet: print('hi')", ["Nothing", "Missing parentheses after 'greet'", "print is wrong", "Indentation error"], 1, "Function definitions require parentheses: def greet():"),
        Question("How do you return multiple values?", ["return a; return b", "return a, b", "return [a][b]", "You can't"], 1, "Use commas to return multiple values: return a, b"),
        Question("A local variable is:", ["Available everywhere", "Only available inside its function", "Shared between functions", "Always a number"], 1, "Local variables exist only within the function they're defined in."),
        Question("What does this lambda do? square = lambda x: x**2", ["Returns x squared", "Prints x", "Returns x", "Creates a list"], 0, "This lambda takes x and returns x squared (x**2)."),
        Question("Which is a benefit of using functions?", ["More memory usage", "Harder to debug", "Code reusability", "Slower execution"], 2, "Functions allow you to reuse code without rewriting it."),
    ], passing_score=60)

    chapter4 = Chapter("ch4", "Functions", "Learn how to create reusable code blocks with functions.", ch4_lessons, [ch4_qa, ch4_qb, ch4_qc])

    ch5_lessons = [
        Lesson("5-1", "Lists and Tuples", """
LISTS AND TUPLES

LISTS (mutable, ordered):
    fruits = ["apple", "banana", "cherry"]

    # Accessing elements
    fruits[0]     -> "apple"
    fruits[-1]    -> "cherry"

    # Modifying
    fruits.append("date")    # add to end
    fruits.insert(1, "fig")  # insert at 1
    fruits.remove("banana")  # remove item
    fruits.pop()             # remove last

    # Useful operations
    len(fruits)              # length
    fruits.sort()            # sort in place
    "apple" in fruits        # True/False

TUPLES (immutable, ordered):
    point = (3, 5)
    x, y = point     # unpacking
    # point[0] = 10  <- ERROR! Immutable

LIST COMPREHENSION:
    squares = [x**2 for x in range(5)]
    # [0, 1, 4, 9, 16]
        """),
        Lesson("5-2", "Dictionaries and Sets", """
DICTIONARIES AND SETS

DICTIONARIES (key-value pairs):
    student = {
        "name": "Alice",
        "age": 20,
        "grade": "A"
    }

    # Access
    student["name"]       -> "Alice"
    student.get("age")    -> 20

    # Modify
    student["age"] = 21
    student["email"] = "a@b.com"  # add
    del student["grade"]           # delete

    # Iterate
    for key, value in student.items():
        print(f"{key}: {value}")

SETS (unique elements, unordered):
    colors = {"red", "green", "blue"}
    colors.add("yellow")
    colors.discard("red")

    # Set operations
    a = {1, 2, 3}
    b = {2, 3, 4}
    a | b    -> {1, 2, 3, 4}  # union
    a & b    -> {2, 3}        # intersection
    a - b    -> {1}           # difference
        """),
    ]

    ch5_qa = Quiz("5-A", "Chapter 5 Quiz - Version A", [
        Question("What is the correct way to create a list?", ["(1, 2, 3)", "[1, 2, 3]", "{1, 2, 3}", "list = 1, 2, 3"], 1, "Lists use square brackets []."),
        Question("What does .append() do?", ["Removes the last item", "Adds an item to the end", "Sorts the list", "Reverses the list"], 1, ".append() adds an element to the end of a list."),
        Question("What is a dictionary?", ["An ordered list", "A collection of key-value pairs", "An immutable sequence", "A set of unique numbers"], 1, "Dictionaries store data as key-value pairs."),
        Question("What makes tuples different from lists?", ["Tuples use brackets", "Tuples are immutable", "Tuples can't hold strings", "Tuples are unordered"], 1, "Tuples are immutable — they cannot be changed after creation."),
        Question("What does {1,2,3} & {2,3,4} return?", ["{1,2,3,4}", "{2,3}", "{1}", "{4}"], 1, "& is the intersection operator — elements in both sets."),
    ], passing_score=60)

    ch5_qb = Quiz("5-B", "Chapter 5 Quiz - Version B", [
        Question("How do you access the first element of list 'items'?", ["items[1]", "items[0]", "items.first()", "items[-0]"], 1, "Lists are zero-indexed, so the first element is at index 0."),
        Question("How do you add a key-value pair to a dictionary?", ["dict.add(key, value)", "dict[key] = value", "dict.append(key, value)", "dict.insert(key, value)"], 1, "Use dict[key] = value to add or update entries."),
        Question("What is list comprehension?", ["A way to understand lists", "A concise way to create lists", "A type of loop", "A sorting method"], 1, "List comprehension is a concise syntax for creating lists."),
        Question("Sets automatically remove:", ["All elements", "The first element", "Duplicates", "Numbers"], 2, "Sets only store unique elements — duplicates are removed."),
        Question("What does len() return for a list?", ["The last element", "The number of elements", "The maximum value", "The index of the last element"], 1, "len() returns the number of elements in a list."),
    ], passing_score=60)

    ch5_qc = Quiz("5-C", "Chapter 5 Quiz - Version C", [
        Question("What does fruits[-1] return if fruits = ['a','b','c']?", ["'a'", "'b'", "'c'", "Error"], 2, "Negative indexing: -1 is the last element."),
        Question("Which method safely gets a dictionary value?", [".get()", ".find()", ".search()", ".value()"], 0, ".get() returns None instead of raising an error if key not found."),
        Question("What is [x*2 for x in range(3)]?", ["[0, 1, 2]", "[2, 4, 6]", "[0, 2, 4]", "[1, 2, 3]"], 2, "range(3) = 0,1,2 → multiplied by 2 = [0, 2, 4]."),
        Question("Can a dictionary key be a list?", ["Yes", "No", "Only if it's empty", "Only with strings inside"], 1, "Dictionary keys must be immutable. Lists are mutable, so no."),
        Question("How do you remove an item from a set?", [".remove() or .discard()", ".delete()", ".pop_item()", ".clear_one()"], 0, ".remove() raises error if missing; .discard() does not."),
    ], passing_score=60)

    chapter5 = Chapter("ch5", "Data Structures", "Master Python's built-in data structures: lists, tuples, dictionaries, and sets.", ch5_lessons, [ch5_qa, ch5_qb, ch5_qc])

    return Course("Python Programming Fundamentals", "A comprehensive course covering Python basics from variables to data structures.", [chapter1, chapter2, chapter3, chapter4, chapter5])

# ============================================================
# STUDENT PROFILE & PROGRESS
# ============================================================

class StudentProfile:
    def __init__(self, username: str, store: DataStore):
        self.username = username
        self.store = store
        self.data = self._load_or_create()

    def _load_or_create(self) -> dict:
        data = self.store.load(f"student_{self.username}.json")
        if not data:
            data = {
                "username": self.username,
                "created_at": str(datetime.now()),
                "last_login": str(datetime.now()),
                "total_study_time_seconds": 0,
                "chapters_progress": {},
                "quiz_history": [],
                "achievements_unlocked": [],
                "quiz_streak": 0,
                "total_quizzes_passed": 0,
                "certificate_earned": False,
                "certificate_date": None,
                "chapter_start_times": {},
            }
            self.store.save(f"student_{self.username}.json", data)
        data["last_login"] = str(datetime.now())
        return data

    def save(self):
        self.store.save(f"student_{self.username}.json", self.data)

    def get_chapter_progress(self, chapter_id: str) -> dict:
        if chapter_id not in self.data["chapters_progress"]:
            self.data["chapters_progress"][chapter_id] = {
                "status": "not_started",
                "lessons_read": [],
                "quiz_attempts": {},
                "best_quiz_score": 0,
                "passed": False,
            }
        return self.data["chapters_progress"][chapter_id]

    def mark_lesson_read(self, chapter_id: str, lesson_id: str):
        progress = self.get_chapter_progress(chapter_id)
        if lesson_id not in progress["lessons_read"]:
            progress["lessons_read"].append(lesson_id)
        if progress["status"] == "not_started":
            progress["status"] = "in_progress"
        self.save()

    def record_quiz_attempt(self, chapter_id: str, quiz_id: str, score: float, passed: bool, total_questions: int, correct_count: int):
        progress = self.get_chapter_progress(chapter_id)
        attempt = {
            "quiz_id": quiz_id,
            "score": score,
            "passed": passed,
            "total_questions": total_questions,
            "correct": correct_count,
            "timestamp": str(datetime.now()),
        }
        if quiz_id not in progress["quiz_attempts"]:
            progress["quiz_attempts"][quiz_id] = []
        progress["quiz_attempts"][quiz_id].append(attempt)
        self.data["quiz_history"].append(attempt)
        if score > progress["best_quiz_score"]:
            progress["best_quiz_score"] = score
        if passed:
            self.data["quiz_streak"] = self.data.get("quiz_streak", 0) + 1
            self.data["total_quizzes_passed"] = self.data.get("total_quizzes_passed", 0) + 1
            progress["passed"] = True
            progress["status"] = "completed"
        else:
            self.data["quiz_streak"] = 0
        self.save()

    def start_chapter_timer(self, chapter_id: str):
        self.data["chapter_start_times"][chapter_id] = str(datetime.now())
        self.save()

    def get_chapter_time(self, chapter_id: str) -> Optional[float]:
        start = self.data["chapter_start_times"].get(chapter_id)
        if start:
            start_time = datetime.fromisoformat(start)
            return (datetime.now() - start_time).total_seconds()
        return None

    def get_completed_chapters(self, total_chapters: int) -> int:
        return sum(1 for ch_data in self.data["chapters_progress"].values() if ch_data.get("passed", False))

    def has_achievement(self, achievement_id: str) -> bool:
        return achievement_id in self.data.get("achievements_unlocked", [])

    def unlock_achievement(self, achievement_id: str):
        if achievement_id not in self.data["achievements_unlocked"]:
            self.data["achievements_unlocked"].append(achievement_id)
            self.save()
            return True
        return False

# ============================================================
# ACHIEVEMENT ENGINE
# ============================================================

class AchievementEngine:
    def __init__(self, student: StudentProfile, course: Course):
        self.student = student
        self.course = course
        self.newly_unlocked = []

    def check_all(self) -> List[Achievement]:
        self.newly_unlocked = []
        total_chapters = len(self.course.chapters)
        completed = self.student.get_completed_chapters(total_chapters)
        for achievement in ACHIEVEMENTS:
            if self.student.has_achievement(achievement.id):
                continue
            unlocked = False
            criteria = achievement.criteria
            if criteria["type"] == "first_login":
                unlocked = True
            elif criteria["type"] == "chapters_completed":
                unlocked = completed >= criteria["value"]
            elif criteria["type"] == "chapters_percent":
                pct = (completed / total_chapters * 100) if total_chapters > 0 else 0
                unlocked = pct >= criteria["value"]
            elif criteria["type"] == "quiz_score":
                for attempt in self.student.data.get("quiz_history", []):
                    if attempt["score"] >= criteria["value"]:
                        unlocked = True
                        break
            elif criteria["type"] == "quiz_streak":
                unlocked = self.student.data.get("quiz_streak", 0) >= criteria["value"]
            elif criteria["type"] == "retry_pass":
                for ch_data in self.student.data["chapters_progress"].values():
                    for qid, attempts in ch_data.get("quiz_attempts", {}).items():
                        has_fail = any(not a["passed"] for a in attempts)
                        has_pass = any(a["passed"] for a in attempts)
                        if has_fail and has_pass:
                            unlocked = True
                            break
            elif criteria["type"] == "speed_complete":
                for ch in self.course.chapters:
                    time_taken = self.student.get_chapter_time(ch.chapter_id)
                    ch_progress = self.student.get_chapter_progress(ch.chapter_id)
                    if time_taken and time_taken <= criteria["value"] and ch_progress.get("passed"):
                        unlocked = True
                        break
            elif criteria["type"] == "all_content_read":
                for ch in self.course.chapters:
                    ch_progress = self.student.get_chapter_progress(ch.chapter_id)
                    if len(ch_progress["lessons_read"]) == len(ch.lessons) and len(ch.lessons) > 0:
                        unlocked = True
                        break
            elif criteria["type"] == "total_quizzes_passed":
                unlocked = self.student.data.get("total_quizzes_passed", 0) >= criteria["value"]
            elif criteria["type"] == "certificate_earned":
                unlocked = self.student.data.get("certificate_earned", False)
            if unlocked:
                if self.student.unlock_achievement(achievement.id):
                    self.newly_unlocked.append(achievement)
        return self.newly_unlocked

# ============================================================
# CERTIFICATE GENERATOR
# ============================================================

class CertificateGenerator:
    @staticmethod
    def generate(student: StudentProfile, course: Course) -> str:
        completed_chapters = []
        total_score_sum = 0
        quiz_count = 0
        for ch in course.chapters:
            ch_progress = student.get_chapter_progress(ch.chapter_id)
            if ch_progress.get("passed"):
                completed_chapters.append(ch.title)
                total_score_sum += ch_progress.get("best_quiz_score", 0)
                quiz_count += 1
        avg_score = total_score_sum / quiz_count if quiz_count > 0 else 0
        date_str = datetime.now().strftime("%B %d, %Y")
        cert_data = f"{student.username}-{date_str}-{course.title}"
        cert_id = hashlib.md5(cert_data.encode()).hexdigest()[:12].upper()
        total_achievements = len(student.data.get("achievements_unlocked", []))
        cert = f"""
============================================================
                    CERTIFICATE OF COMPLETION
============================================================

This is to certify that

            {student.username.upper()}

has successfully completed the course:

         {course.title}

============================================================
TOPICS MASTERED:
"""
        for ch in completed_chapters:
            cert += f"    - {ch}\n"
        cert += f"""
============================================================
PERFORMANCE SUMMARY:
    - Chapters Completed: {len(completed_chapters)}/{len(course.chapters)}
    - Average Quiz Score: {avg_score:.1f}%
    - Achievements Earned: {total_achievements}/{len(ACHIEVEMENTS)}
    - Total Quizzes Passed: {student.data.get('total_quizzes_passed', 0)}

Date Issued: {date_str}
Certificate ID: {cert_id}

                    ________________________
                       Course Director
                    Python Learning Academy

============================================================
"""
        return cert

# ============================================================
# FLASK ROUTES
# ============================================================

@app.before_request
def load_course():
    global course
    if course is None:
        course = create_python_course()

def get_student() -> Optional[StudentProfile]:
    username = session.get("username")
    if username:
        return StudentProfile(username, store)
    return None

def check_achievements(student):
    engine = AchievementEngine(student, course)
    return engine.check_all()

@app.route("/")
def index():
    student = get_student()
    if student:
        return redirect(url_for("dashboard"))
    return render_template("index.html")

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username", "").strip().lower()
    if not username:
        flash("Username cannot be empty.", "error")
        return redirect(url_for("index"))
    filepath = os.path.join(store.data_dir, f"student_{username}.json")
    if os.path.exists(filepath):
        student = StudentProfile(username, store)
        session["username"] = username
        newly = check_achievements(student)
        flash(f"Welcome back, {username}!", "success")
        if newly:
            flash(f"Achievement unlocked: {newly[0].name}!", "success")
        return redirect(url_for("dashboard"))
    else:
        flash("Username not found. Please register first.", "error")
        return redirect(url_for("index"))

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip().lower()
    if not username:
        flash("Username cannot be empty.", "error")
        return redirect(url_for("index"))
    if not username.isalnum():
        flash("Username must be alphanumeric.", "error")
        return redirect(url_for("index"))
    filepath = os.path.join(store.data_dir, f"student_{username}.json")
    if os.path.exists(filepath):
        flash("Username already exists. Please login instead.", "error")
        return redirect(url_for("index"))
    student = StudentProfile(username, store)
    session["username"] = username
    newly = check_achievements(student)
    flash(f"Account created! Welcome, {username}!", "success")
    if newly:
        flash(f"Achievement unlocked: {newly[0].name}!", "success")
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("index"))

@app.route("/dashboard")
def dashboard():
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    total_chapters = len(course.chapters)
    completed = student.get_completed_chapters(total_chapters)
    pct = int(completed / total_chapters * 100) if total_chapters > 0 else 0
    achievements_count = len(student.data.get("achievements_unlocked", []))
    total_quizzes_taken = len(student.data.get("quiz_history", []))
    total_passed = student.data.get("total_quizzes_passed", 0)
    streak = student.data.get("quiz_streak", 0)
    avg_score = 0
    if total_quizzes_taken > 0:
        avg_score = sum(a["score"] for a in student.data["quiz_history"]) / total_quizzes_taken
    chapters_data = []
    for ch in course.chapters:
        progress = student.get_chapter_progress(ch.chapter_id)
        chapters_data.append({"chapter": ch, "progress": progress})
    return render_template("dashboard.html", student=student, course=course, completed=completed, total_chapters=total_chapters, pct=pct, achievements_count=achievements_count, total_achievements=len(ACHIEVEMENTS), total_quizzes_taken=total_quizzes_taken, total_passed=total_passed, streak=streak, avg_score=avg_score, chapters_data=chapters_data)

@app.route("/chapter/<chapter_id>")
def chapter_detail(chapter_id):
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    chapter = next((c for c in course.chapters if c.chapter_id == chapter_id), None)
    if not chapter:
        flash("Chapter not found.", "error")
        return redirect(url_for("dashboard"))
    student.start_chapter_timer(chapter_id)
    progress = student.get_chapter_progress(chapter_id)
    return render_template("chapter.html", chapter=chapter, progress=progress, student=student)

@app.route("/lesson/<chapter_id>/<lesson_id>")
def lesson(chapter_id, lesson_id):
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    chapter = next((c for c in course.chapters if c.chapter_id == chapter_id), None)
    if not chapter:
        flash("Chapter not found.", "error")
        return redirect(url_for("dashboard"))
    lesson_obj = next((l for l in chapter.lessons if l.lesson_id == lesson_id), None)
    if not lesson_obj:
        flash("Lesson not found.", "error")
        return redirect(url_for("chapter_detail", chapter_id=chapter_id))
    student.mark_lesson_read(chapter_id, lesson_id)
    newly = check_achievements(student)
    return render_template("lesson.html", chapter=chapter, lesson=lesson_obj, newly_unlocked=newly)

@app.route("/quiz/<chapter_id>/<quiz_id>", methods=["GET", "POST"])
def quiz(chapter_id, quiz_id):
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    chapter = next((c for c in course.chapters if c.chapter_id == chapter_id), None)
    if not chapter:
        flash("Chapter not found.", "error")
        return redirect(url_for("dashboard"))
    quiz_obj = next((q for q in chapter.quizzes if q.quiz_id == quiz_id), None)
    if not quiz_obj:
        flash("Quiz not found.", "error")
        return redirect(url_for("chapter_detail", chapter_id=chapter_id))
    if request.method == "GET":
        return render_template("quiz.html", chapter=chapter, quiz=quiz_obj)
    else:
        correct = 0
        total = len(quiz_obj.questions)
        results = []
        for i, question in enumerate(quiz_obj.questions):
            ans = request.form.get(f"q_{i}")
            try:
                ans_idx = int(ans) - 1 if ans else -1
            except:
                ans_idx = -1
            is_correct = ans_idx == question.correct_index
            if is_correct:
                correct += 1
            results.append({
                "question": question.text,
                "your_answer": question.options[ans_idx] if 0 <= ans_idx < len(question.options) else "No answer",
                "correct_answer": question.options[question.correct_index],
                "is_correct": is_correct,
                "explanation": question.explanation,
            })
        score = (correct / total * 100) if total > 0 else 0
        passed = score >= quiz_obj.passing_score
        student.record_quiz_attempt(chapter_id, quiz_id, score, passed, total, correct)
        newly = check_achievements(student)
        return render_template("quiz_result.html", chapter=chapter, quiz=quiz_obj, score=score, correct=correct, total=total, passed=passed, results=results, newly_unlocked=newly)

@app.route("/achievements")
def achievements():
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    unlocked = student.data.get("achievements_unlocked", [])
    unlocked_achievements = [a for a in ACHIEVEMENTS if a.id in unlocked]
    locked_achievements = [a for a in ACHIEVEMENTS if a.id not in unlocked]
    pct = int(len(unlocked) / len(ACHIEVEMENTS) * 100) if ACHIEVEMENTS else 0
    return render_template("achievements.html", unlocked=unlocked_achievements, locked=locked_achievements, pct=pct, total=len(ACHIEVEMENTS), earned=len(unlocked))

@app.route("/history")
def history():
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    quiz_history = list(reversed(student.data.get("quiz_history", [])))
    return render_template("history.html", history=quiz_history)

@app.route("/certificate")
def certificate():
    student = get_student()
    if not student:
        return redirect(url_for("index"))
    total_chapters = len(course.chapters)
    completed = student.get_completed_chapters(total_chapters)
    if completed < total_chapters:
        chapters_status = []
        for ch in course.chapters:
            progress = student.get_chapter_progress(ch.chapter_id)
            chapters_status.append({"chapter": ch, "passed": progress.get("passed", False)})
        return render_template("certificate_locked.html", completed=completed, total=total_chapters, chapters_status=chapters_status)
    if not student.data.get("certificate_earned"):
        student.data["certificate_earned"] = True
        student.data["certificate_date"] = str(datetime.now())
        student.save()
        check_achievements(student)
    cert_text = CertificateGenerator.generate(student, course)
    return render_template("certificate.html", cert_text=cert_text, student=student)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
