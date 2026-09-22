import os
import string
import time
import webbrowser
import queue
import threading
import pyttsx3

# --- Speech engine -----------------------------------------------------
# Using ONE persistent pyttsx3 engine, fed by a queue and drained by a
# single worker thread. Spinning up a brand-new engine on every call (in
# its own thread) is a common source of crashes/garbled or overlapping
# audio on Windows (SAPI5), since pyttsx3 isn't designed to have several
# engines running concurrently.

_speech_queue = queue.Queue()

def _speech_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 170)
    engine.setProperty('volume', 1)
    while True:
        text = _speech_queue.get()
        if text is None:
            break
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            print("Speech error:", e)
        _speech_queue.task_done()

threading.Thread(target=_speech_worker, daemon=True).start()

def speak(text):
    _speech_queue.put(text)

def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return text.strip()

STOPWORDS = {"who", "is", "what", "tell", "me", "about", "the", "a", "an"}

print("ADWOA: Online")
speak("Online")

memory = {}

if os.path.exists("brain.txt"):
    with open("brain.txt", "r") as file:
        for line in file:
            if "|" in line:
                question, answer = line.strip().split("|", 1)
                question = question.strip()
                answer = answer.strip()
                memory[question] = answer

while True:
    user = clean_text(input("You: "))

    if user == "bye" or user == "exit":
        print("ADWOA: Goodbye Eli")
        speak("Goodbye Eli")
        break

    found = False

    user_words = [word for word in user.split() if word not in STOPWORDS]

    if user == "time":
        current_time = time.strftime("%H:%M:%S")
        print("ADWOA: The time is " + current_time)
        speak("The time is " + current_time)
        continue

    if user == "date":
        current_date = time.strftime("%Y-%m-%d")
        print("ADWOA: Today's date is " + current_date)
        speak("Today's date is " + current_date)
        continue

    if user.startswith("open "):
        site = user.replace("open ", "").strip()
        if not site:
            print("ADWOA: Open what site?")
            speak("Open what site?")
            continue
        url = "https://www." + site + ".com"
        print("ADWOA: Opening " + site)
        speak("Opening " + site)
        webbrowser.open(url)
        continue

    if user.startswith("search "):
        query = user.replace("search ", "").strip()
        if not query:
            print("ADWOA: Search for what?")
            speak("Search for what?")
            continue
        print("ADWOA: Searching Google for " + query)
        speak("Searching Google for " + query)
        link = "https://www.google.com/search?q=" + query
        webbrowser.open(link)
        continue

    if user in memory:
        print("ADWOA: " + memory[user])
        speak(memory[user])
        continue

    if user == "brain size":
        print("ADWOA: I currently know " + str(len(memory)) + " things.")
        speak("I currently know " + str(len(memory)) + " things.")
        continue

    if user.startswith("look into "):
        keyword = user.replace("look into ", "").strip()
        matches = [q for q in memory if keyword in q]
        print("ADWOA: I found these:")
        speak("I found these:")
        for question in matches:
            print("- " + question)
            speak(question)
        continue

    # --- Fuzzy fallback match -------------------------------------
    best_match = ""
    best_score = 0

    for question in memory:
        if question == user:
            continue

        question_words = [word for word in question.split() if word not in STOPWORDS]
        if not question_words:
            continue

        match_count = sum(1 for word in question_words if word in user_words)
        score = match_count / len(question_words)

        if score > best_score:
            best_score = score
            best_match = question

    if best_score >= 0.6:
        print("ADWOA: " + memory[best_match])
        speak(memory[best_match])
        found = True

    if not found:
        speak("I don't know that. Teach me")
        reply = input("ADWOA: I don't know that. Teach me: ").lower().strip()

        speak("Should I remember this?")
        confirm = input("ADWOA: Should I remember this? (yes/no): ").lower().strip()

        if confirm == "yes":
            memory[user] = reply

            with open("brain.txt", "a") as file:
                file.write(user + "|" + reply + "\n")

            print("ADWOA: Got it! I will remember that.")
            speak("Got it! I will remember that.")
        else:
            print("ADWOA: Okay, I won't save it.")
            speak("Okay, I won't save it.")
            