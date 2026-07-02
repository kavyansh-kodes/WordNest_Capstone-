import json
import os
import random
from langchain_core.tools import tool
from memory import (load_profile,add_learned_words,set_goal,get_goal,add_weak_words,
update_level,add_quiz_result,get_quiz_history,update_weak_word_progress,update_streak)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@tool
def get_user_profile(username: str) -> dict:
    """
    Retrieve complete user profile.
    """
    return load_profile(username)

@tool
def set_learning_goal(username: str, goal: str) -> str:
    """
    Set or update user's learning goal.
    """
    set_goal(username, goal)
    return f"Goal updated to: {goal}"

@tool
def get_learning_goal(username: str) -> str:
    """
    Retrieve user's current goal.
    """
    return get_goal(username)

@tool
def save_learned_words(username: str,language: str,words: dict) -> str:
    """
    Save newly learned vocabulary.
    Example:
    {
        "Haus":"House",
        "Hund":"Dog"
    }
    """
    add_learned_words(username, language, words)
    return ( f"Saved {len(words)}"
             f"{language} words."
             f"for {username}")

@tool
def get_learned_words(username: str,language: str) -> dict:
    """
    Retrieve learned vocabulary as a dictionary.
     Returns:
    {
        "Haus":"House",
        "Hund":"Dog"
    }
    """
    profile = load_profile(username)
    return profile.get("learned_words", {}).get(language, {})

@tool
def save_weak_words(username: str, language: str, words: dict) -> str:
    """
    Store words the user struggles with.
     Example:
    {
        "Haus":"House",
        "Hund":"Dog"
    }
    """
    add_weak_words(username, language, words)
    return (f"Added {len(words)} weak words in {language} for {username}")

@tool
def update_learning_level(username: str, level: str) -> str:
    """
    Update learner proficiency level.
    """
    update_level(username, level)
    return f"Level updated to {level}"

@tool
def get_personalized_words(username: str, language: str, n: int) -> list:
    """
    Generate words the user has not previously learned.
    """
    profile = load_profile(username)
    learned_words = set(profile.get("learned_words", {}).get(language, {}).keys())
    path = os.path.join(BASE_DIR, "data", language, "word-list-cleaned.json")
    with open(path, encoding="utf-8") as f:
        word_list = json.load(f)
    available_words = [item["word"] for item in word_list.values()
                      if item["word"] not in learned_words]
    if len(available_words) < n:
        n = len(available_words)
    selected_words = random.sample(available_words, n)
    return selected_words

@tool
def get_personalized_words_by_difficulty(username: str, language: str,
    difficulty_level: str, n: int) -> list:
    """
    Generate unseen words, filtered by difficulty.
    """
    profile = load_profile(username)
    learned_words = set(profile.get("learned_words", {}).get(language, {}).keys())
    path = os.path.join(BASE_DIR, "data", language, "word-list-cleaned.json")
    with open(path, encoding="utf-8") as f:
        word_list = json.load(f)
    filtered_words = [item["word"] for item in word_list.values()
    if (item.get("word_difficulty") == difficulty_level and item["word"] not in learned_words )]
    if len(filtered_words) < n:
        n = len(filtered_words)
    selected_words = random.sample(filtered_words, n)
    return selected_words

@tool
def save_quiz_result(username: str,language: str,score: int,total: int,date: str) -> str:
    """
    Save a user's quiz attempt to their profile.
    Example:
    username="Kavyansh",
    language="German",
    score=7,
    total=10,
    date="2026-06-27"
    """
    add_quiz_result(username,
         {"date": date,"language": language,"score": score,"total": total})
    return "Quiz result saved"

@tool
def retrieve_quiz_history(username: str) -> list:
    """
    Retrieve previous quiz attempts.
    """
    return get_quiz_history(username)

@tool
def update_weak_progress(username: str, language: str, word: str) -> str:
    """
    Update mastery progress
    for a weak word.
    """
    update_weak_word_progress(username, language, word)
    return "updated"

@tool
def update_user_streak(username: str) -> int:
    """
    Update the user's daily streak.
    """
    return update_streak(username)
