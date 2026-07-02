import json
import os
from datetime import datetime

PROFILES_DIR = "profiles"
os.makedirs(PROFILES_DIR, exist_ok=True)

def get_profile_path(username: str) -> str:
    return os.path.join(PROFILES_DIR, f"{username.lower().strip()}.json")

def profile_exists(username: str) -> bool:
    return os.path.exists(get_profile_path(username))

def create_profile(username: str, target_language: str = "",
    current_level: str = "beginner", goal: str = "") -> dict:
    if profile_exists(username):
        raise ValueError(f"Profile '{username}' already exists.")
    profile = {"username": username, "target_language": target_language,
    "current_level": current_level, "goal": goal, "learned_words": {}, "weak_words": {},
    "weak_word_progress": {}, "quiz_history": [], "streak": 0,
    "last_active": datetime.now().isoformat() }
    save_profile(profile)
    return profile

def load_profile(username: str) -> dict:
    path = get_profile_path(username)
    if not os.path.exists(path):
        raise FileNotFoundError(f"No profile found for {username}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_profile(profile: dict):
    path = get_profile_path(profile["username"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=4, ensure_ascii=False)

def update_last_active(username: str):
    profile = load_profile(username)
    profile["last_active"] = (datetime.now().isoformat())
    save_profile(profile)

def add_learned_words(username: str, language: str, words: dict):
    """
       words should be:
       {
           "Haus": "House",
           "Hund": "Dog"
       }
       """
    profile = load_profile(username)
    learned_words = profile.get("learned_words", {})
    if language not in learned_words:
        learned_words[language] = {}
    learned_words[language].update(words)
    profile["learned_words"] = learned_words
    save_profile(profile)

def set_goal(username: str, goal: str):
    profile = load_profile(username)
    profile["goal"] = goal
    save_profile(profile)

def get_goal(username: str) -> str:
    profile = load_profile(username)
    return profile.get("goal", "")

def add_weak_words(username: str, language: str, words: dict):
    """
    words:
    {
        "Haus": "House",
        "Hund": "Dog"
    }
    """
    profile = load_profile(username)
    weak_words = profile.get("weak_words", {})
    if not isinstance(weak_words, dict):
        weak_words = {}
    if language not in weak_words:
        weak_words[language] = {}
    weak_words[language].update(words)
    profile["weak_words"] = weak_words
    save_profile(profile)

def update_level(username: str, level: str):
    profile = load_profile(username)
    profile["current_level"] = level
    save_profile(profile)

def remove_weak_words(username: str, language: str, words: list):
    profile = load_profile(username)
    weak_words = profile.get("weak_words", {})
    current = weak_words.get(language, {})
    for word in words:
        current.pop(word, None)
    weak_words[language] = current
    profile["weak_words"] = weak_words
    save_profile(profile)

def save_quiz_result(username: str, language: str, score: int, total: int):
    profile = load_profile(username)
    history = profile.get("quiz_history", [])
    history.append({"language": language,"score": score, "total": total,
            "timestamp": datetime.now().isoformat()})
    profile["quiz_history"] = history
    save_profile(profile)

def get_quiz_history(username: str):
    profile = load_profile(username)
    return profile.get("quiz_history", [])

def add_quiz_result(username, quiz_result):
    profile = load_profile(username)
    if "quiz_history" not in profile:
        profile["quiz_history"] = []
    profile["quiz_history"].append(quiz_result)
    save_profile(profile)

def update_weak_word_progress(username, language, word):
    profile = load_profile(username)
    if "weak_progress" not in profile:
        profile["weak_progress"] = {}
    if language not in profile["weak_progress"]:
        profile["weak_progress"][language] = {}
    weak = profile["weak_progress"][language]
    weak[word] = weak.get(word, 0) + 1
    if weak[word] >= 3:
        del weak[word]
        if language in profile["weak_words"]:
            profile["weak_words"][language].pop(word, None)
        # remove progress entries for words no longer weak
    current_weak = profile.get("weak_words", {}).get(language, {})
    for w in list(weak.keys()):
        if w not in current_weak:
            weak.pop(w)
        # cleanup empty dictionaries
    if not weak:
        profile["weak_progress"].pop(language, None)
    if language in profile.get("weak_words", {}):
        if not profile["weak_words"][language]:
            profile["weak_words"].pop(language)
    save_profile(profile)

def update_streak(username):
    profile = load_profile(username)
    today = datetime.now().date()
    last_active = profile.get("last_active")
    if last_active:
        last_date = datetime.fromisoformat(last_active).date()
        difference = (today - last_date).days
        if difference == 1:
            profile["streak"] += 1
        elif difference > 1:
            profile["streak"] = 1
    else:
        profile["streak"] = 1
    profile["last_active"] = (datetime.now().isoformat())
    save_profile(profile)
    return profile["streak"]
