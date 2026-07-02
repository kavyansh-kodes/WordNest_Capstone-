import os
import re
import json
import random
import streamlit as st
from json_repair import repair_json
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq

key = st.secrets["GROQ_API_KEY"]
translation_model = ChatGroq(model="qwen/qwen3-32b",groq_api_key=key)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@tool
def get_n_random_words(language:str,n:int) -> list:
    """
    Selects a specified number of random words from the language-specific word list.
    The function reads a JSON file containing words for the specific language from a predefined
    directory. It then selects 'n' random words from the file and returns a list of them.
    :param language: A string representing the language for which to fetch the word list.
    :param n: An integer representing the number of random words to retrieve.
    :return: A list of 'n' random words.
    """
    path = os.path.join(BASE_DIR,"data",f"{language}","word-list-cleaned.json")
    with open(path) as f:
        words = json.load(f)
        random_words_dict = {k:words[k] for k in random.sample(list(words.keys()),n)}
        random_words = [item["word"] for item in random_words_dict.values()]
        return random_words

@tool
def get_n_random_words_by_difficulty_level(language: str,
difficulty_level: str, n: int ) -> list:
    """
    Retrieves a specified number of random words filtered by a given difficulty level
    from a word list corresponding to a specific language. The function reads the
    word list from a JSON file located in the directory `data/{language}/word-list-cleaned.json`.
    :param language: The language of the word list to be used.
    :type language: str
    :param difficulty_level: The difficulty level to filter words by. Possible values
        depend on the data structure in the JSON file. The only valid values are "beginner",
        "intermediate" and "advanced".
    :type difficulty_level: str
    :param n: The number of random words to retrieve.
    :type n: int
    :return: A list containing `n` random words filtered by the specified difficulty level.
    :rtype: list
    """
    path = os.path.join(BASE_DIR,"data", f"{language}", "word-list-cleaned.json")
    with open(path) as f:
        word_list = json.load(f)
    words_filtered_by_difficulty = {k: v for k, v in word_list.items()
    if v.get("word_difficulty") == difficulty_level}
    random_word_dict = {k: words_filtered_by_difficulty[k] for k in
                        random.sample(list(words_filtered_by_difficulty.keys()), n)}
    random_words = [item["word"] for item in random_word_dict.values()]
    return random_words

@tool
def translate_words(random_words: list,
source_language: str, target_language: str) -> dict:
    """
    Translates a list of words from a source language to a target language using
    a language model. The method ensures output is in the expected JSON format,
    containing translations corresponding to the provided input words.
    :param random_words: A list of words to be translated.
    :param source_language: The language of the input words.
    :param target_language: The language to translate the words into.
    :return: A dictionary containing the translations with the structure:
             {"translations": [{"source": "<original>", "target": "<translated>"}, ...]}.
    """
    prompt = (
        f"You are a precise translation engine.\n"
        f"Translate each of the following {len(random_words)} words from {source_language} to {target_language}.\n"
        f"Return ONLY valid JSON with this exact structure:\n"
        f'{{"translations": [{{"source": "<original>", "target": "<translated>"}}, ...]}}\n'
        f"No explanations, no extra fields, no markdown.\n"
        f"Words: {json.dumps(random_words, ensure_ascii=False)}" )

    response = translation_model.invoke([HumanMessage(content=prompt)])
    text = getattr(response, "content", str(response))
    parsed = {}

    try:
        parsed = json.loads(text)

    except json.JSONDecodeError:

        matches = re.findall(
            r'\{(?:[^{}]|(?:\{[^{}]*\}))*\}',
            text,
            re.DOTALL
        )

        for candidate in matches:
            try:
                obj = json.loads(candidate)

                if isinstance(obj, dict) and "translations" in obj:
                    parsed = obj
                    break

            except:
                continue
    translations_list = parsed.get("translations", [])
    model_map = {item.get("source", ""): item.get("target", "")
    for item in translations_list if isinstance(item, dict)}
    ordered_translations = [ {"source": w, "target": model_map.get(
    w, model_map.get(w.capitalize(), w))} for w in random_words]
    return { "translations": ordered_translations,}

@tool
def generate_examples_and_text(words: list,
source_language: str,target_language: str) -> dict:
    """
     Generates example sentences and a short text. Takes a list of words, a source language and
     a target language string, and generates a short text and sentences using words in the list.
     The words of the list are in source language and the sentences formed using them are
     to be translated to the target language. Returns a JSON file with content and translations.
    """
    prompt = f"""
You are a language-learning assistant.
Source language: {source_language}
Target language: {target_language}
Vocabulary words: {json.dumps(words, ensure_ascii=False)}
Tasks:
1. Generate exactly ONE simple sentence for each word.
2. Translate every sentence into {target_language}.
3. Generate a short paragraph (3-5 sentences) using as many of the words as possible.
4. Translate the paragraph. Return ONLY valid JSON.
Format:
{{  "examples":[{{"word":"...", "sentence":"...", "translation":"..."}}],
    "text": {{ "content":"...","translation":"..." }}
      }}
    """
    response = translation_model.invoke([HumanMessage(content=prompt)])
    content = getattr(response, "content", str(response))
    try:
        parsed = json.loads(repair_json(content))
    except Exception:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise ValueError("Model returned invalid JSON.")
        parsed = json.loads( match.group(0))
    return parsed

def translations_to_dict(translations: dict) -> dict:
    """
    Converts:
    {
        "translations": [
            {"source":"Haus","target":"House"},
            {"source":"Hund","target":"Dog"}
        ]
    }
    to:
    {
        "Haus":"House",
        "Hund":"Dog"
    }
    """
    return {item["source"]: item["target"] for item in translations.get("translations", [])}

@tool
def generate_quiz(words: dict, source_language: str, target_language: str) -> dict:
    """
    Generate MCQ quiz from learned vocabulary.
    Example input:
    {
        "Haus":"House",
        "Hund":"Dog"
    }
    """
    german_words = list(words.keys())
    english_words = list(words.values())
    quiz = []
    for german, english in words.items():
        wrong = [x for x in english_words if x != english]
        options = random.sample(wrong, min(3, len(wrong)))
        options.append(english)
        random.shuffle(options)
        quiz.append({"word": german, "question": f"What is '{german}'?",
                    "correct":english,"options":options})
    return {"quiz": quiz}

@tool
def explain_grammar(topic: str, language: str, level: str) -> dict:
    """
    Explain a grammar concept, word usage,
    or sentence structure.
    """
    prompt = f"""
    You are an expert {language} language teacher.
    Explain the following grammar concept or expression: {topic}
    The learner's level is: {level}
    Requirements:
    - Explain in simple English.
    - Give a short explanation.
    - Provide 3 examples.
    - Explain any grammar rules involved.
    - Keep the explanation suitable for a {level} learner.
    
    Return plain text only.
    """
    response = translation_model.invoke([HumanMessage(content=prompt)])
    return {"explanation":response.content}
