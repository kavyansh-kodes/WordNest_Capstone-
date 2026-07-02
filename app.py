import streamlit as st
import re
import random
import json
import asyncio
from datetime import datetime
from langchain_core.messages import HumanMessage
from profile_tools import (save_learned_words,save_quiz_result,save_weak_words,update_weak_progress
,update_user_streak)
from agent import build_graph
from tools import generate_quiz, explain_grammar
from memory import (create_profile,profile_exists,load_profile,save_profile,)

# header and css
st.set_page_config(page_title="WordNest - AI Language Assistant",page_icon="🌍",layout="wide")
st.markdown("""
<style>
div[data-baseweb="select"] > div {
    cursor: pointer !important;
}
button {
    cursor: pointer !important;
}
div.stButton > button {
    width: 100%;
    border-radius: 12px;
    height: 3em;
    font-weight: 600;
}
div.stDownloadButton > button {
    width: 100%;
    border-radius: 12px;
}
div[data-testid="metric-container"] {
    background: #262730;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #444;
}
section[data-testid="stSidebar"] {
    border-right: 1px solid #333;
}
</style>
""", unsafe_allow_html=True)

if "username" not in st.session_state:
    st.session_state.username = None
if "profile_loaded" not in st.session_state:
    st.session_state.profile_loaded = False
if "quiz" not in st.session_state:
    st.session_state.quiz = []

r = random.randint(1001, 9999)
st.title("🌍 WordNest - An AI Language Assistant")
st.info(
    "Learn languages with AI-powered vocabulary generation, "
    "quizzes, grammar explanations and progress tracking.")

# profile login section
st.sidebar.header("👤 Profile")
profile_action = st.sidebar.radio("Profile Action",["Load Profile", "Create Profile"])
username = st.sidebar.text_input("Username")
st.sidebar.header("Learning Settings")

# language and difficulty selection
source_language = st.sidebar.selectbox("Language You Want To Learn",
["German","Spanish","French","Japanese","Croatian","Greek","Portuguese","Russian",
 "Italian","Korean","Swedish","English"])
target_language = st.sidebar.selectbox( "Base Language (You Already Know)",
["English","French","German","Spanish","Japanese","Croatian","Greek","Portuguese",
 "Russian","Italian","Korean","Swedish"])
difficulty = st.sidebar.selectbox("Difficulty Level",
["beginner","intermediate","advanced"])

# create profile
if profile_action == "Create Profile":
    if st.sidebar.button("Create Profile"):
        if not username.strip():
            st.sidebar.error("Please enter a username.")
        elif profile_exists(username):
            st.sidebar.error("Username already exists.")
        else:
            try:
                create_profile( username=username,target_language=source_language,
                               current_level=difficulty)
                st.session_state.username = username
                st.session_state.profile_loaded = True
                st.sidebar.success(f"Profile created: {username}")
            except Exception as e:
                st.sidebar.error(str(e))

# load profile
if profile_action == "Load Profile":
    if st.sidebar.button("Load Profile"):
        try:
            load_profile(username)
            st.session_state.username = username
            st.session_state.profile_loaded = True
            st.sidebar.success(f"Loaded profile: {username}")
        except Exception as e:
            st.sidebar.error(str(e))

# login
if st.session_state.profile_loaded:
    profile = load_profile(st.session_state.username)
    st.sidebar.markdown("---")
    st.sidebar.success(f"Logged in as:\n{profile['username']}")
    st.sidebar.write(f"Level: {profile['current_level']}")
    st.sidebar.write(f"Goal: {profile.get('goal','')}")
    learned = profile.get("learned_words",{})
    total_words = sum(len(v) for v in learned.values())
    st.sidebar.write(f"Learned words: {total_words}")
    st.sidebar.write(f"Streak: {profile.get('streak', 0)} days 🔥")
    st.sidebar.markdown("---")
    new_goal = st.sidebar.text_input("Learning Goal")
    if st.sidebar.button("Save Goal"):
        profile["goal"] = new_goal
        save_profile(profile)
        st.sidebar.success("Goal updated.")

st.sidebar.markdown("---")
st.sidebar.text("Made by - Kavyansh Gaur")

st.markdown("## Let's start learning...")
num_words = st.slider("Number Of Words",min_value=5,max_value=50,value=10)
download_option = st.checkbox("Download Content as Text File?")

# profile viewer
if st.session_state.profile_loaded:
    with st.expander("📂 View Profile"):
        st.json(load_profile(st.session_state.username ))

if st.session_state.profile_loaded:
    profile = load_profile(st.session_state.username)
    with st.expander("📊 Progress Dashboard"):
        learned = profile.get("learned_words",{})
        quiz_history = profile.get("quiz_history",[])
        weak_words = profile.get("weak_words",{})
        total_words = sum(len(v) for v in learned.values())
        st.metric("Total Words Learned", total_words)
        total_weak = sum(len(v) for v in weak_words.values())
        st.metric("Current Weak Words",total_weak)

        if quiz_history:
            total_quizzes = len(quiz_history)
            avg_score = (sum(q["score"]/q["total"] for q in quiz_history
                             if q["total"] > 0) / total_quizzes) * 100
            best_score = max((q["score"]/q["total"] for q in quiz_history
                             if q["total"] > 0), default=0) * 100
            st.markdown("### Quiz Statistics")
            st.write(f"Quizzes Taken: {total_quizzes}")
            st.write(f"Average Score: {avg_score:.1f}%")
            st.write(f"Best Score: {best_score:.1f}%")
        else:
            st.info("No quiz history yet.")
        st.markdown("### Recent Quiz History")
        if quiz_history:
            for q in reversed(quiz_history[-3:]):
                st.write(
                    f"{q['date']} | "
                    f"{q['language']} | "
                    f"{q['score']}/{q['total']}")
        st.markdown("### Language Statistics")
        for lang in learned:
            learned_count = len(learned[lang])
            weak_count = len(
                weak_words.get(lang, {}))
            st.write(
                f"{lang}: "
                f"{learned_count} learned, "
                f"{weak_count} weak")

# download progress report
if st.session_state.profile_loaded:
    with st.expander("📥 Export Progress Report"):
        profile = load_profile(st.session_state.username)
        report = f"""
    WORDNEST PROGRESS REPORT
    ========================
    Username: {profile["username"]}
    Current Level: {profile["current_level"]}
    Learning Goal: {profile.get("goal","")}
    Current Streak: {profile.get("streak",0)} days
    ========================================
    LEARNED WORDS
    ========================================
    """
        learned = profile.get("learned_words",{})
        total_words = 0
        for lang, words in learned.items():
            count = len(words)
            total_words += count
            report += (f"\n{lang}: " f"{count} words")
        report += (f"\n\nTotal Words Learned: " f"{total_words}")

        report += (
            "\n\n========================================"
            "\nWEAK WORDS"
            "\n========================================\n"
        )
        weak = profile.get("weak_words",{})
        total_weak = 0
        for lang, words in weak.items():
            count = len(words)
            total_weak += count
            report += (f"\n{lang}: " f"{count} words")
        report += (f"\n\nTotal Weak Words: " f"{total_weak}")

        report += (
            "\n\n========================================"
            "\nQUIZ STATISTICS"
            "\n========================================\n"
        )
        quiz_history = profile.get("quiz_history",[])
        report += (f"\nQuizzes Taken: "f"{len(quiz_history)}")
        if quiz_history:
            avg = (sum(q["score"] / q["total"] for q in quiz_history
                if q["total"] > 0)/ len(quiz_history)) * 100
            best = max((q["score"] / q["total"] for q in quiz_history
                   if q["total"] > 0),default=0) * 100
            report += (f"\nAverage Score: " f"{avg:.1f}%")
            report += (f"\nBest Score: " f"{best:.1f}%")

        report += (
            "\n\n========================================"
            "\nRECENT QUIZZES"
            "\n========================================\n")
        for q in quiz_history[-5:]:
            report += (f"\n{q['date']} | " f"{q['language']} | " f"{q['score']}/{q['total']}")
        st.download_button( label="📄 Download Progress Report",
        data=report,file_name=(f"{st.session_state.username} _progress_report.txt"),mime="text/plain")

# quiz section
if st.session_state.profile_loaded:
    st.markdown("---")
    st.markdown("## 📝 Vocabulary Quiz")
    profile = load_profile(st.session_state.username)
    learned_words = profile.get("learned_words",{}).get(source_language, {})

    col1, col2 = st.columns(2)
    with col1:
        generate_quiz_btn = st.button("📝 Generate Quiz")
    with col2:
        weak_quiz_btn = st.button("🔥 Practice Weak Words")

    if len(learned_words) >= 4:

        if generate_quiz_btn:
            st.session_state.weak_practice = False
            quiz = generate_quiz.invoke({"words": learned_words,
                "source_language": source_language,"target_language": target_language})
            st.session_state.quiz = quiz["quiz"]

        if weak_quiz_btn:
            st.session_state.weak_practice = True
            profile = load_profile(st.session_state.username)
            weak = profile.get("weak_words", {}).get(source_language, {})
            if not weak:
                st.warning("No weak words found.")
            else:
                quiz = generate_quiz.invoke({"words": weak,"source_language": source_language,
                                            "target_language": target_language})
                st.session_state.quiz = quiz["quiz"]
    else:
        st.info("Learn at least 4 words first.")

    if "quiz" in st.session_state:
        score = 0
        weak_words = {}
        for i, q in enumerate(st.session_state.quiz):
            answer = st.radio(q["question"], q["options"], key=f"quiz_{i}")
            if answer == q["correct"]:
                score += 1
                if st.session_state.get("weak_practice", False):
                    (update_weak_progress.invoke({"username":st.session_state.username,
                    "language":source_language, "word": q["word"]}))
                else:
                    weak_words[q["word"]] = q["correct"]

            else:
                word = q["question"].split("'")[1]
                weak_words[word] = q["correct"]

        if st.session_state.get("quiz"):
            if st.button("Submit Quiz"):
                st.markdown("---")
                st.success(f"Score: {score}/{len(st.session_state.quiz)}")
                save_quiz_result.invoke({
                    "username": st.session_state.username,
                    "language": source_language,
                    "score": score,
                    "total": len(st.session_state.quiz),
                    "date": str(datetime.now())
                })
                if weak_words:
                    save_weak_words.invoke({
                        "username": st.session_state.username,
                        "language": source_language,
                        "words": weak_words
                    })
                st.markdown("## Quiz Review")
                for i, q in enumerate(st.session_state.quiz):
                    user_answer = st.session_state[f"quiz_{i}"]
                    st.write(f"**Q{i + 1}. {q['question']}**")
                    st.write(f"Your answer: {user_answer}")
                    st.write(f"Correct answer: {q['correct']}")
                    if user_answer == q["correct"]:
                        st.success("✅ Correct")
                    else:
                         st.error("❌ Incorrect")
                    st.markdown("---")

# ai tutor
if st.session_state.profile_loaded:
    st.markdown("---")
    st.markdown("## 🤖 AI Grammar Tutor")
    grammar_query = st.text_input("Ask about grammar, words, or sentences")
    if st.button("Explain", key="grammar_explain"):
        if grammar_query:
            with st.spinner("Generating explanation..."):
                explanation = explain_grammar.invoke({"topic": grammar_query,
                              "language": source_language,"level": difficulty})
                response = re.sub(r"<think>.*?</think>","", explanation["explanation"]
                           ,flags=re.DOTALL).strip()
            st.markdown("### Explanation")
            st.write(response)

# running the agent and generating content
async def run_agent(prompt):
    graph = await build_graph()
    result = await graph.ainvoke({"messages": [HumanMessage(content=prompt)],
    "username":st.session_state.username, "source_language":source_language,
    "target_language":target_language, "number_of_words":num_words, "word_difficulty":difficulty,})
    return result

st.markdown("---")
if st.button("Generate Learning Content"):
    final_prompt = f""" Current user: {st.session_state.username}
                   Generate {num_words} {difficulty} words in {source_language}. 
                   Base language: {target_language}.
                   Provide:
                   1. Vocabulary
                   2. Meanings
                   3. Example sentences
                   4. Short practice paragraph
                   """
    with st.spinner("Generating learning content..."):
        result = asyncio.run(run_agent(final_prompt))
        username = st.session_state.get("username")
        messages = result["messages"]
        translations = None
        for msg in messages:
            if getattr(msg, "name", None) == "translate_words":
                try:
                    translations = json.loads(msg.content)
                    break
                except:
                    pass

        if translations and username:
            learned = {item["source"]: item["target"]
                      for item in translations.get("translations", [])}
            if learned:
                save_learned_words.invoke({"username": username,"language": source_language,
                                          "words": learned})
                update_user_streak.invoke({"username": username})
    response = result["messages"][-1].content
    st.markdown("---")
    st.markdown("## 📘 Learning Content")
    st.write(response)

    if download_option:
        st.download_button(
            label="Download Learning Content",
            data=response,
            file_name=(
                f"{source_language}_"
                f"{difficulty}_"
                f"{r}.txt"), mime="text/plain")

st.markdown("---")
st.caption(
    "WordNest v1.0 • Built with Streamlit "
    "and LangGraph,  "
    "Created by Kavyansh Gaur")
