# WordNest 🌍 -- AI-Powered Language Learning Assistant

## Overview

WordNest is an agentic AI language learning assistant designed to
provide personalized vocabulary learning, adaptive practice, grammar
tutoring, and long-term progress tracking.

Built as a capstone project for Google's Agent Development Kit (ADK)
course, WordNest demonstrates how AI agents can create personalized
educational experiences through memory, tool usage, and adaptive
learning strategies.

## Features

### Personalized User Profiles

-   Create and load learner profiles
-   Store learning goals and proficiency levels
-   Persistent learning memory

### AI Vocabulary Generation

-   Generate vocabulary in multiple languages
-   Difficulty-based content generation
-   Example sentences and practice paragraphs

### Adaptive Quiz System

-   Automatic quiz generation
-   Multiple-choice vocabulary testing
-   Detailed quiz review and scoring

### Weak Word Detection & Practice

-   Detect incorrectly answered words
-   Maintain weak-word memory
-   Generate targeted revision quizzes
-   Automatically remove mastered weak words

### Progress Tracking

-   Quiz history
-   Learning streaks
-   Weak word analytics
-   Progress dashboard

### AI Grammar Tutor

-   AI-powered explanations
-   Beginner-friendly grammar support

### Export Progress Reports

-   Download comprehensive learning reports

## Agent Architecture

-   Main Learning Agent
-   Translation Tool
-   Quiz Generator Tool
-   Grammar Explanation Tool
-   Persistent Memory System

## Technologies Used

-   Python
-   Streamlit
-   LangGraph
-   LangChain
-   Google Gemini
-   JSON Storage

## Installation

``` bash
git clone <repository-url>
cd WordNest
pip install -r requirements.txt
streamlit run app.py
```

## Capstone Requirements Covered

-   Agent / Multi-Agent System
-   Agent Skills and Tools
-   Security Features
-   Deployability
-   Persistent Memory

## Author

**Kavyansh Gaur**
