import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import streamlit.components.v1 as components
import hashlib
import io
import os
import re
import sqlite3
from fpdf import FPDF
import json as _json   # only used internally for DB serialisation
from datetime import date, datetime

# ─── Admin Credentials ───
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256(b"admin123").hexdigest()

# ─── Trial Task Generator ───
def get_trial_tasks_for_career(career_name):
    if not career_name:
        return {i: f"Explore Day {i} of your career trial" for i in range(1, 8)}

    if "Government" in career_name or "Civil" in career_name or "IAS" in career_name or "UPSC" in career_name:
        return {
            1: "Solve UPSC-level reasoning questions",
            2: "Read about IAS officer responsibilities",
            3: "Watch a topper interview video",
            4: "Analyze a governance case study",
            5: "Study polity or current affairs basics",
            6: "Attempt mock questions",
            7: "Reflect on lifestyle & long-term commitment",
        }
    elif "Data" in career_name or "Analyst" in career_name:
        return {
            1: "Solve logical & analytical problems",
            2: "Learn Excel basics",
            3: "Watch a data analyst roadmap video",
            4: "Practice SQL or Python basics",
            5: "Analyze a small dataset",
            6: "Mini data project",
            7: "Career reflection",
        }
    elif "Software" in career_name or "Developer" in career_name or "Engineer" in career_name:
        return {
            1: "Set up a coding environment",
            2: "Write a 'Hello World' in a relevant language",
            3: "Watch a software engineering day-in-the-life video",
            4: "Solve 3 beginner coding problems",
            5: "Build a tiny project (calculator, to-do list, etc.)",
            6: "Explore open-source contributions",
            7: "Reflect on what you enjoyed most",
        }
    elif "Design" in career_name or "Creative" in career_name or "Art" in career_name:
        return {
            1: "Identify your creative strengths",
            2: "Learn Canva or a basic design tool",
            3: "Create one sample design",
            4: "Study a designer's portfolio",
            5: "Redesign something you see daily",
            6: "Get feedback on your work",
            7: "Skill gap analysis & next steps",
        }
    elif "Doctor" in career_name or "Medical" in career_name or "Health" in career_name:
        return {
            1: "Read about a typical doctor's day",
            2: "Understand NEET/medical entrance requirements",
            3: "Watch a medical student vlog",
            4: "Learn basic anatomy concepts",
            5: "Explore a medical specialty that interests you",
            6: "Shadow or read patient case studies",
            7: "Reflect on empathy, patience & commitment",
        }
    else:
        return {
            1: f"Understand what a {career_name} does daily",
            2: "Learn the core required skills",
            3: "Watch expert talks or day-in-the-life videos",
            4: "Practice a basic task from this career",
            5: "Skill improvement exercise",
            6: "Mini simulation or project",
            7: "Final reflection — is this right for you?",
        }

# ─── Trial Day Quizzes (one question per day, career-aware) ───
def get_trial_quizzes(career_name):
    """Return a dict of 7 days (1-indexed), each with a list of 3 quiz questions."""
    cn = career_name or ""

    if any(k in cn for k in ["Government", "Civil", "IAS", "UPSC"]):
        return {
            1: [
                {"q": "Which exam selects IAS officers in India?", "opts": ["GATE", "UPSC CSE", "CAT", "JEE"], "ans": 1},
                {"q": "What does IAS stand for?", "opts": ["Indian Administrative Service", "Indian Army Service", "Internal Affairs System", "Indian Accounts Service"], "ans": 0},
                {"q": "UPSC stands for:", "opts": ["Union Public Service Commission", "United Personnel Selection Committee", "Universal Public Sector Council", "Union Police Service Corps"], "ans": 0},
            ],
            2: [
                {"q": "An IAS officer is under which ministry at the centre?", "opts": ["Finance", "Home Affairs", "Dept. of Personnel & Training", "External Affairs"], "ans": 2},
                {"q": "Which Article of the Constitution establishes the UPSC?", "opts": ["Article 315", "Article 21", "Article 370", "Article 32"], "ans": 0},
                {"q": "The DM (District Magistrate) belongs to which service?", "opts": ["IPS", "IFS", "IAS", "IRS"], "ans": 2},
            ],
            3: [
                {"q": "How many stages are there in UPSC CSE?", "opts": ["1", "2", "3", "4"], "ans": 2},
                {"q": "Which stage of UPSC tests writing skills?", "opts": ["Prelims", "Mains", "Interview", "Physical Test"], "ans": 1},
                {"q": "CSAT is part of which stage?", "opts": ["Mains", "Interview", "Prelims", "Training"], "ans": 2},
            ],
            4: [
                {"q": "Which subject is NOT in the UPSC Prelims GS paper?", "opts": ["Polity", "History", "Mathematics", "Environment"], "ans": 2},
                {"q": "Current affairs for UPSC is best sourced from:", "opts": ["Textbooks", "The Hindu / PIB", "Novels", "Social media"], "ans": 1},
                {"q": "Which NCERT subject is most important for UPSC History?", "opts": ["Class 6–12 History", "Class 11 Physics", "Class 9 Maths", "Class 8 Science"], "ans": 0},
            ],
            5: [
                {"q": "What is the minimum age to appear for UPSC CSE?", "opts": ["18", "21", "25", "27"], "ans": 1},
                {"q": "Maximum age limit for General category in UPSC CSE?", "opts": ["30", "32", "35", "40"], "ans": 1},
                {"q": "How many attempts for OBC candidates in UPSC CSE?", "opts": ["6", "7", "9", "Unlimited"], "ans": 2},
            ],
            6: [
                {"q": "How many attempts does a General category candidate get?", "opts": ["3", "6", "9", "Unlimited"], "ans": 1},
                {"q": "Which mock test platform is popular for UPSC?", "opts": ["Testbook", "LeetCode", "Coursera", "Udemy"], "ans": 0},
                {"q": "What is the full form of GS in UPSC Mains?", "opts": ["General Science", "General Studies", "Government Service", "Graduate Studies"], "ans": 1},
            ],
            7: [
                {"q": "The Mains interview in UPSC is called:", "opts": ["GD", "Personality Test", "Group Discussion", "Viva Voce"], "ans": 1},
                {"q": "Who conducts the Personality Test (Interview) for UPSC?", "opts": ["State PSC", "UPSC Board", "IIM Panel", "Ministry of Education"], "ans": 1},
                {"q": "After selection, IAS probationers train at:", "opts": ["NDA Pune", "LBSNAA Mussoorie", "IIM Ahmedabad", "DRDO Delhi"], "ans": 1},
            ],
        }

    elif any(k in cn for k in ["Data", "Analyst", "Analytics"]):
        return {
            1: [
                {"q": "Which Python library is used for data manipulation?", "opts": ["NumPy", "pandas", "Flask", "Django"], "ans": 1},
                {"q": "What does CSV stand for?", "opts": ["Comma Separated Values", "Computer Storage Variable", "Code Storage View", "Column Separated Values"], "ans": 0},
                {"q": "Which of these is a spreadsheet tool?", "opts": ["Python", "Excel", "Java", "Linux"], "ans": 1},
            ],
            2: [
                {"q": "What does SQL stand for?", "opts": ["Simple Query Language", "Structured Query Language", "System Query Logic", "Standard Query Layer"], "ans": 1},
                {"q": "Which SQL clause filters rows?", "opts": ["ORDER BY", "GROUP BY", "WHERE", "SELECT"], "ans": 2},
                {"q": "Which SQL function counts rows?", "opts": ["SUM()", "AVG()", "COUNT()", "MAX()"], "ans": 2},
            ],
            3: [
                {"q": "Which chart is best for showing trends over time?", "opts": ["Pie", "Bar", "Line", "Scatter"], "ans": 2},
                {"q": "Which chart compares parts of a whole?", "opts": ["Line", "Scatter", "Pie", "Histogram"], "ans": 2},
                {"q": "What does a scatter plot show?", "opts": ["Trends over time", "Relationship between two variables", "Part of a whole", "Distribution"], "ans": 1},
            ],
            4: [
                {"q": "What is a DataFrame?", "opts": ["A database", "A 2D labelled data structure", "A list", "A chart"], "ans": 1},
                {"q": "Which pandas method shows the first 5 rows?", "opts": [".tail()", ".head()", ".info()", ".describe()"], "ans": 1},
                {"q": "Which pandas method shows column data types?", "opts": [".head()", ".tail()", ".dtypes", ".shape"], "ans": 2},
            ],
            5: [
                {"q": "Which of these is NOT a data visualisation library?", "opts": ["Matplotlib", "Seaborn", "Plotly", "NumPy"], "ans": 3},
                {"q": "Which library is best for statistical visualisations?", "opts": ["Flask", "Seaborn", "Django", "Requests"], "ans": 1},
                {"q": "What does Plotly specialise in?", "opts": ["Machine learning", "Interactive charts", "Web scraping", "Database queries"], "ans": 1},
            ],
            6: [
                {"q": "What does EDA stand for?", "opts": ["Exploratory Data Analysis", "External Data Application", "Extended Data Algorithms", "None"], "ans": 0},
                {"q": "Which step comes FIRST in a data project?", "opts": ["Model building", "Data cleaning", "Deployment", "Reporting"], "ans": 1},
                {"q": "What is a null value in a dataset?", "opts": ["Zero", "Missing data", "Negative number", "Text value"], "ans": 1},
            ],
            7: [
                {"q": "Which platform offers free datasets and competitions?", "opts": ["GitHub", "Kaggle", "LinkedIn", "Stack Overflow"], "ans": 1},
                {"q": "Which certification is offered by Google for data analytics?", "opts": ["AWS Certified", "Google Data Analytics Certificate", "Oracle DBA", "Azure Fundamentals"], "ans": 1},
                {"q": "Which tool is used to query big data at scale?", "opts": ["Excel", "BigQuery", "Notepad", "PowerPoint"], "ans": 1},
            ],
        }

    elif any(k in cn for k in ["Software", "Developer", "Engineer", "Programmer"]):
        return {
            1: [
                {"q": "What does HTML stand for?", "opts": ["Hyper Text Markup Language", "High Transfer Markup Logic", "Hyper Transfer Machine Language", "None"], "ans": 0},
                {"q": "What does CSS stand for?", "opts": ["Computer Style Sheets", "Cascading Style Sheets", "Creative Style System", "Coded Style Sheets"], "ans": 1},
                {"q": "Which language adds interactivity to websites?", "opts": ["HTML", "CSS", "JavaScript", "SQL"], "ans": 2},
            ],
            2: [
                {"q": "Which data structure uses LIFO order?", "opts": ["Queue", "Stack", "Array", "Tree"], "ans": 1},
                {"q": "Which data structure uses FIFO order?", "opts": ["Stack", "Tree", "Queue", "Graph"], "ans": 2},
                {"q": "Which is the fastest data structure for key lookups?", "opts": ["Array", "Linked List", "Hash Map", "Stack"], "ans": 2},
            ],
            3: [
                {"q": "What is Git used for?", "opts": ["Design", "Version control", "Database", "Deployment"], "ans": 1},
                {"q": "Which command creates a new Git branch?", "opts": ["git push", "git branch", "git merge", "git init"], "ans": 1},
                {"q": "What does 'git clone' do?", "opts": ["Deletes a repo", "Copies a repo locally", "Creates a branch", "Merges code"], "ans": 1},
            ],
            4: [
                {"q": "What does API stand for?", "opts": ["Application Programming Interface", "Applied Protocol Index", "Automated Process Integration", "None"], "ans": 0},
                {"q": "Which HTTP method is used to fetch data?", "opts": ["POST", "PUT", "GET", "DELETE"], "ans": 2},
                {"q": "What format do most APIs return data in?", "opts": ["XML", "JSON", "CSV", "PDF"], "ans": 1},
            ],
            5: [
                {"q": "Which language runs natively in web browsers?", "opts": ["Python", "Java", "JavaScript", "C++"], "ans": 2},
                {"q": "Which of these is a backend framework?", "opts": ["React", "Vue", "Angular", "Django"], "ans": 3},
                {"q": "What does 'frontend' refer to?", "opts": ["Server logic", "Database", "User interface", "Deployment"], "ans": 2},
            ],
            6: [
                {"q": "What does OOP stand for?", "opts": ["Object Oriented Programming", "Open Output Processing", "Optimised Online Protocol", "None"], "ans": 0},
                {"q": "Which OOP concept hides internal details?", "opts": ["Inheritance", "Polymorphism", "Encapsulation", "Abstraction"], "ans": 2},
                {"q": "Which keyword creates a class in Python?", "opts": ["def", "class", "object", "new"], "ans": 1},
            ],
            7: [
                {"q": "Which platform hosts open-source code repositories?", "opts": ["Kaggle", "Heroku", "GitHub", "Jira"], "ans": 2},
                {"q": "What is a pull request?", "opts": ["Downloading code", "Proposing code changes for review", "Deploying an app", "Cloning a repo"], "ans": 1},
                {"q": "Which site is best for coding interview practice?", "opts": ["Behance", "Dribbble", "LeetCode", "Figma"], "ans": 2},
            ],
        }

    elif any(k in cn for k in ["Design", "Creative", "Art", "UX", "UI"]):
        return {
            1: [
                {"q": "What does UX stand for?", "opts": ["User Experience", "User Execution", "Unified Exchange", "None"], "ans": 0},
                {"q": "What does UI stand for?", "opts": ["User Interface", "Unified Input", "User Integration", "None"], "ans": 0},
                {"q": "Which comes first in design process?", "opts": ["Prototyping", "User Research", "Visual Design", "Testing"], "ans": 1},
            ],
            2: [
                {"q": "Which colour model is used for screens?", "opts": ["CMYK", "RGB", "Pantone", "HSV"], "ans": 1},
                {"q": "Which colour model is used for print?", "opts": ["RGB", "HSL", "CMYK", "HEX"], "ans": 2},
                {"q": "What does HEX colour #000000 represent?", "opts": ["White", "Red", "Blue", "Black"], "ans": 3},
            ],
            3: [
                {"q": "What is a wireframe?", "opts": ["A 3D model", "A basic layout sketch", "A colour palette", "A font"], "ans": 1},
                {"q": "What is a prototype?", "opts": ["A final product", "An interactive mockup for testing", "A brand logo", "A database schema"], "ans": 1},
                {"q": "What is a mood board?", "opts": ["A Kanban board", "A visual inspiration collage", "A project timeline", "A colour wheel"], "ans": 1},
            ],
            4: [
                {"q": "Which tool is popular for UI/UX prototyping?", "opts": ["Photoshop", "Figma", "Excel", "Word"], "ans": 1},
                {"q": "Canva is best for:", "opts": ["3D modelling", "Quick graphic design", "Video editing", "Coding"], "ans": 1},
                {"q": "Which Adobe tool is best for photo editing?", "opts": ["Illustrator", "InDesign", "Photoshop", "Premiere"], "ans": 2},
            ],
            5: [
                {"q": "What does the 'F-pattern' refer to in design?", "opts": ["Font selection", "User eye-scanning pattern", "Colour scheme", "Animation"], "ans": 1},
                {"q": "What is visual hierarchy?", "opts": ["Sorting images", "Arranging elements by importance", "Using only one colour", "Aligning text left"], "ans": 1},
                {"q": "Which principle says similar items should be grouped?", "opts": ["Contrast", "Proximity", "Alignment", "Repetition"], "ans": 1},
            ],
            6: [
                {"q": "What is white space in design?", "opts": ["White background", "Empty space around elements", "A font colour", "A design software"], "ans": 1},
                {"q": "What does 'responsive design' mean?", "opts": ["Fast loading", "Design that adapts to screen size", "Bold colours", "Using animations"], "ans": 1},
                {"q": "What is a style guide?", "opts": ["A grammar book", "A document defining design standards", "A font library", "A Figma plugin"], "ans": 1},
            ],
            7: [
                {"q": "Canva is best described as:", "opts": ["A 3D modelling tool", "A video editor", "A graphic design tool", "A coding IDE"], "ans": 2},
                {"q": "Where do designers showcase their portfolio?", "opts": ["LeetCode", "Kaggle", "Behance / Dribbble", "Stack Overflow"], "ans": 2},
                {"q": "What is usability testing?", "opts": ["Testing code bugs", "Testing with real users to find UX issues", "Checking colour contrast", "A/B testing ads"], "ans": 1},
            ],
        }

    elif any(k in cn for k in ["Doctor", "Medical", "Health", "Nurse", "Pharmacy"]):
        return {
            1: [
                {"q": "Which exam is required for MBBS admission in India?", "opts": ["JEE", "NEET", "GATE", "UPSC"], "ans": 1},
                {"q": "MBBS stands for:", "opts": ["Master of Biology and Basic Sciences", "Bachelor of Medicine and Bachelor of Surgery", "Medical Board and Basic Sciences", "None"], "ans": 1},
                {"q": "Which council regulates medical education in India?", "opts": ["UGC", "AICTE", "NMC", "MCI (now NMC)"], "ans": 2},
            ],
            2: [
                {"q": "What is the largest organ in the human body?", "opts": ["Liver", "Lung", "Skin", "Brain"], "ans": 2},
                {"q": "Which organ pumps blood throughout the body?", "opts": ["Liver", "Kidney", "Heart", "Lung"], "ans": 2},
                {"q": "How many chambers does the human heart have?", "opts": ["2", "3", "4", "6"], "ans": 2},
            ],
            3: [
                {"q": "What does ECG measure?", "opts": ["Brain activity", "Heart electrical activity", "Blood pressure", "Temperature"], "ans": 1},
                {"q": "What does MRI stand for?", "opts": ["Medical Radiology Imaging", "Magnetic Resonance Imaging", "Molecular Research Instrument", "None"], "ans": 1},
                {"q": "Normal human body temperature is approximately:", "opts": ["36–37°C", "38–39°C", "34–35°C", "40°C"], "ans": 0},
            ],
            4: [
                {"q": "Which blood type is the universal donor?", "opts": ["AB+", "O+", "O-", "A-"], "ans": 2},
                {"q": "Which blood type is the universal recipient?", "opts": ["O-", "A+", "B+", "AB+"], "ans": 3},
                {"q": "What carries oxygen in the blood?", "opts": ["White blood cells", "Platelets", "Plasma", "Red blood cells"], "ans": 3},
            ],
            5: [
                {"q": "How many bones are in the adult human body?", "opts": ["106", "206", "306", "406"], "ans": 1},
                {"q": "Which bone is the longest in the human body?", "opts": ["Humerus", "Tibia", "Femur", "Radius"], "ans": 2},
                {"q": "What is the smallest bone in the human body?", "opts": ["Stapes (ear)", "Phalanx", "Coccyx", "Patella"], "ans": 0},
            ],
            6: [
                {"q": "What does ICU stand for?", "opts": ["Intensive Care Unit", "Internal Check Unit", "Immediate Care Utility", "None"], "ans": 0},
                {"q": "What does OPD stand for?", "opts": ["Out-Patient Department", "Operating Procedure Division", "Open Patient Directory", "None"], "ans": 0},
                {"q": "Which branch studies diseases?", "opts": ["Cardiology", "Pathology", "Gynaecology", "Radiology"], "ans": 1},
            ],
            7: [
                {"q": "Which vitamin is produced by sunlight exposure?", "opts": ["Vitamin A", "Vitamin B", "Vitamin C", "Vitamin D"], "ans": 3},
                {"q": "Which deficiency causes anaemia?", "opts": ["Vitamin D", "Iron", "Calcium", "Zinc"], "ans": 1},
                {"q": "What does a stethoscope measure?", "opts": ["Blood pressure", "Temperature", "Heart & lung sounds", "Blood sugar"], "ans": 2},
            ],
        }

    else:
        return {
            1: [
                {"q": "What is the best way to learn a new skill?", "opts": ["Read theory only", "Practice regularly", "Watch once", "Memorise notes"], "ans": 1},
                {"q": "What does SMART goal stand for?", "opts": ["Simple, Measurable, Achievable, Realistic, Time-bound", "Specific, Measurable, Achievable, Relevant, Time-bound", "Strong, Motivated, Active, Ready, Tested", "None"], "ans": 1},
                {"q": "What is a growth mindset?", "opts": ["Believing skills are fixed", "Believing skills can be developed", "Avoiding challenges", "Seeking only easy tasks"], "ans": 1},
            ],
            2: [
                {"q": "What does a professional portfolio showcase?", "opts": ["Your salary", "Past work & projects", "Social media", "Hobbies"], "ans": 1},
                {"q": "Which platform is best for a professional portfolio?", "opts": ["TikTok", "Snapchat", "LinkedIn", "WhatsApp"], "ans": 2},
                {"q": "What should a portfolio focus on?", "opts": ["Quantity of work", "Quality and relevance of work", "Only paid work", "Only academic work"], "ans": 1},
            ],
            3: [
                {"q": "What is networking in a career context?", "opts": ["Computer networks", "Building professional relationships", "Followers count", "Email marketing"], "ans": 1},
                {"q": "Which platform is best for professional networking?", "opts": ["Instagram", "LinkedIn", "Pinterest", "Reddit"], "ans": 1},
                {"q": "What is an informational interview?", "opts": ["A job interview", "A casual conversation to learn about a career", "A salary negotiation", "A group interview"], "ans": 1},
            ],
            4: [
                {"q": "What does CV stand for?", "opts": ["Career Vision", "Curriculum Vitae", "Creative Value", "Core Vocation"], "ans": 1},
                {"q": "What is the ideal CV length for a fresher?", "opts": ["5 pages", "3 pages", "1 page", "10 pages"], "ans": 2},
                {"q": "Which section should come first on a CV?", "opts": ["Hobbies", "References", "Personal Information & Objective", "Work Experience"], "ans": 2},
            ],
            5: [
                {"q": "Which skill is most valued by employers?", "opts": ["Technical skills only", "Communication", "Memorisation", "Speed reading"], "ans": 1},
                {"q": "What does 'soft skill' mean?", "opts": ["Physical strength", "Interpersonal and social skills", "Technical coding ability", "Language fluency only"], "ans": 1},
                {"q": "Which is a hard skill?", "opts": ["Teamwork", "Empathy", "Python programming", "Adaptability"], "ans": 2},
            ],
            6: [
                {"q": "What is an internship?", "opts": ["A full-time job", "A short work experience programme", "An online course", "A certification exam"], "ans": 1},
                {"q": "What is the main benefit of an internship?", "opts": ["High salary", "Real-world experience", "Guaranteed job", "Free education"], "ans": 1},
                {"q": "Where can you find internship opportunities in India?", "opts": ["Internshala", "Zomato", "Hotstar", "IRCTC"], "ans": 0},
            ],
            7: [
                {"q": "What does ROI stand for?", "opts": ["Return On Investment", "Rate Of Inflation", "Revenue Over Income", "Risk Of Investment"], "ans": 0},
                {"q": "What is a cover letter?", "opts": ["A page summary of your CV", "A personalised letter explaining why you want a job", "Your reference list", "Your marksheet"], "ans": 1},
                {"q": "What does 'CTC' mean in job offers?", "opts": ["Cost To Company", "Cash Transfer Credit", "Company Tax Contribution", "Career Training Cost"], "ans": 0},
            ],
        }

def get_trial_video_url(career_name, day, task):
    """Return a YouTube search URL relevant to this career + day task."""
    import urllib.parse
    query = f"{career_name} {task}"
    return "https://www.youtube.com/results?search_query=" + urllib.parse.quote_plus(query)

# ─── Daily Motivation ───
DAILY_MOTIVATION = {
    1: "🔥 Day 1 — Starting is already winning!",
    2: "💪 Consistency beats talent.",
    3: "🧠 Skills > Degrees.",
    4: "🚀 You are growing faster than you think.",
    5: "📈 Small steps compound.",
    6: "🏆 Almost there — don't stop!",
    7: "🎉 Trial complete — clarity unlocked!",
}

# ─── Salary & Job Market Data ───
CAREER_MARKET_DATA = {
    "Government": {"salary": "₹6–18 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "Civil": {"salary": "₹6–18 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "IAS": {"salary": "₹10–25 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "UPSC": {"salary": "₹10–25 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "Data": {"salary": "₹5–25 LPA", "growth": "Very High", "demand": "Very High", "growth_icon": "🚀"},
    "Analyst": {"salary": "₹4–20 LPA", "growth": "High", "demand": "High", "growth_icon": "🚀"},
    "Machine Learning": {"salary": "₹8–40 LPA", "growth": "Explosive", "demand": "Very High", "growth_icon": "🚀"},
    "Software": {"salary": "₹5–40 LPA", "growth": "Very High", "demand": "Very High", "growth_icon": "🚀"},
    "Developer": {"salary": "₹4–30 LPA", "growth": "High", "demand": "Very High", "growth_icon": "🚀"},
    "Engineer": {"salary": "₹4–25 LPA", "growth": "High", "demand": "High", "growth_icon": "🟢"},
    "Design": {"salary": "₹3–18 LPA", "growth": "High", "demand": "High", "growth_icon": "🟡"},
    "UX": {"salary": "₹5–22 LPA", "growth": "High", "demand": "High", "growth_icon": "🚀"},
    "Doctor": {"salary": "₹8–50 LPA", "growth": "Stable", "demand": "Very High", "growth_icon": "🟢"},
    "Medical": {"salary": "₹6–40 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "Finance": {"salary": "₹5–30 LPA", "growth": "High", "demand": "High", "growth_icon": "🟡"},
    "CA": {"salary": "₹8–40 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "Law": {"salary": "₹4–30 LPA", "growth": "Stable", "demand": "Moderate", "growth_icon": "🟡"},
    "Teacher": {"salary": "₹3–12 LPA", "growth": "Stable", "demand": "High", "growth_icon": "🟢"},
    "Marketing": {"salary": "₹4–20 LPA", "growth": "High", "demand": "High", "growth_icon": "🟡"},
}

def get_market_data(career_name):
    cn = career_name or ""
    for keyword, data in CAREER_MARKET_DATA.items():
        if keyword.lower() in cn.lower():
            return data
    return {"salary": "₹3–15 LPA", "growth": "Moderate", "demand": "Moderate", "growth_icon": "🟡"}

# ─── Top Colleges & Certifications ───
TOP_COLLEGES = {
    "Government": ["LBSNAA — IAS Training Academy", "SVPNPA — Police Academy", "NAAA — Accounts Academy", "State PSC Training Institutes"],
    "Civil": ["LBSNAA Mussoorie", "State ATIs (Administrative Training Institutes)", "Drishti IAS / Vision IAS Coaching"],
    "Data": ["IIT Data Science Programs", "ISI Kolkata — Statistics", "IIIT Hyderabad — Data Science", "Coursera / Google Data Analytics Cert", "IIM — Business Analytics"],
    "Analyst": ["IIM — Analytics Programs", "ISB Hyderabad", "Great Learning — Data Analytics", "Manipal ProLearn", "Coursera Google Certificate"],
    "Software": ["IITs — B.Tech CSE", "NITs — Computer Science", "BITS Pilani", "VIT / Manipal / IIIT Delhi", "freeCodeCamp + Portfolio (self-taught)"],
    "Developer": ["IITs / NITs / IIIT", "Amity / SRM / Symbiosis", "Full Stack Bootcamps (Scaler, Newton School)", "The Odin Project (free)"],
    "Design": ["NID — National Institute of Design", "NIFT — Fashion & Textile", "MIT Institute of Design", "Srishti School of Art", "Google UX Design Certificate"],
    "UX": ["NID Ahmedabad", "IIT IDC (Industrial Design)", "Pearl Academy", "Google UX Design Certificate (Coursera)", "Interaction Design Foundation"],
    "Doctor": ["AIIMS Delhi / Mumbai", "CMC Vellore", "JIPMER Puducherry", "Maulana Azad Medical College", "Grant Medical College Mumbai"],
    "Medical": ["AIIMS Network", "Armed Forces Medical College (AFMC)", "KMC Manipal", "St. John's Medical College Bangalore"],
    "Finance": ["IIMs — MBA Finance", "SRCC Delhi", "Narsee Monjee (NMIMS)", "CA via ICAI", "CFA Institute (Global)"],
    "Law": ["NLSIU Bangalore (Rank 1 NLU)", "NLU Delhi", "NALSAR Hyderabad", "Symbiosis Law School", "Faculty of Law, Delhi University"],
    "Teacher": ["RIE (Regional Institute of Education)", "DIET (District Institute of Education)", "BHU / DU — B.Ed Programs", "IGNOU — B.Ed Distance", "Unacademy / Vedantu — Educator Platform"],
    "Marketing": ["IIM — MBA Marketing", "MICA Ahmedabad (Marketing Comm.)", "NMIMS Mumbai", "Google Digital Marketing Certificate", "HubSpot Academy (free)"],
}

def get_top_colleges(career_name):
    cn = career_name or ""
    for keyword, colleges in TOP_COLLEGES.items():
        if keyword.lower() in cn.lower():
            return colleges
    return ["IITs / NITs / Central Universities", "State Universities", "Coursera / edX — Online Certifications", "LinkedIn Learning", "Internshala — Short Courses"]

# ─── Resume PDF Generator ───
def generate_resume_pdf(data):
    """Generate a clean resume PDF and return bytes."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=15)

    # ── Header ──
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 10, data.get("full_name") or "Your Name", ln=True, align="C")
    pdf.set_font("Helvetica", "", 10)
    contact_parts = [p for p in [data.get("email"), data.get("phone")] if p]
    pdf.cell(0, 6, "  |  ".join(contact_parts), ln=True, align="C")
    pdf.ln(3)

    def section_title(title):
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(240, 240, 240)
        pdf.cell(0, 8, f"  {title}", ln=True, fill=True)
        pdf.ln(2)

    def body_text(text, bold=False):
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.multi_cell(0, 6, text)

    # ── Career Objective ──
    if data.get("career_objective"):
        section_title("CAREER OBJECTIVE")
        body_text(data["career_objective"])
        pdf.ln(3)

    # ── Education ──
    education = data.get("education", [])
    if education:
        section_title("EDUCATION")
        for edu in education:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, edu.get("degree", ""), ln=True)
            pdf.set_font("Helvetica", "", 10)
            details = []
            if edu.get("college"): details.append(edu["college"])
            if edu.get("year"):    details.append(f"Year: {edu['year']}")
            if edu.get("grade"):   details.append(f"Grade: {edu['grade']}")
            pdf.cell(0, 5, "  |  ".join(details), ln=True)
            pdf.ln(2)

    # ── Skills ──
    skills = data.get("skills", [])
    if skills:
        section_title("SKILLS")
        body_text("  •  ".join(skills))
        pdf.ln(3)

    # ── Work Experience ──
    work = data.get("work_experience", [])
    if work:
        section_title("WORK EXPERIENCE / INTERNSHIPS")
        for w in work:
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, f"{w.get('role', '')}  —  {w.get('company', '')}", ln=True)
            pdf.set_font("Helvetica", "I", 9)
            if w.get("duration"):
                pdf.cell(0, 5, w["duration"], ln=True)
            pdf.set_font("Helvetica", "", 10)
            if w.get("description"):
                pdf.multi_cell(0, 5, w["description"])
            pdf.ln(2)

    return bytes(pdf.output())

# ─── Page Config ───
st.set_page_config(page_title="CareerCompass", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")

# ─── Futuristic CSS Styling ───
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap');

    /* Main background with animated gradient */
    .stApp {
        background: linear-gradient(135deg, #1a0b2e 0%, #2d1b4e 25%, #4a1f6f 50%, #2d1b4e 75%, #1a0b2e 100%);
        background-size: 400% 400%;
        animation: gradientShift 15s ease infinite;
        font-family: 'Rajdhani', sans-serif;
    }

    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Cyberpunk glow effect */
    @keyframes neonGlow {
        0%, 100% { text-shadow: 0 0 10px #ff0080, 0 0 20px #ff0080, 0 0 30px #ff0080; }
        50% { text-shadow: 0 0 20px #ff0080, 0 0 30px #ff0080, 0 0 40px #ff0080, 0 0 50px #ff6b9d; }
    }

    /* Headings */
    h1 {
        font-family: 'Orbitron', sans-serif !important;
        color: #ff6b9d !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        animation: neonGlow 2s ease-in-out infinite;
    }

    h2, h3 {
        font-family: 'Orbitron', sans-serif !important;
        color: #ff6b9d !important;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(255, 0, 128, 0.3);
    }

    h1 {
        font-size: 3rem !important;
        font-weight: 900 !important;
        background: linear-gradient(90deg, #ff0080, #7928ca, #ff6b9d, #ff0080);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
    }

    @keyframes shimmer {
        to { background-position: 200% center; }
    }

    /* Glassmorphism containers */
    .stContainer {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 0, 128, 0.2) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(255, 0, 128, 0.2) !important;
        padding: 20px !important;
        transition: all 0.3s ease !important;
    }

    .stContainer:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px 0 rgba(255, 0, 128, 0.3) !important;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a0b2e 0%, #2d1b4e 100%) !important;
        border-right: 2px solid rgba(255, 0, 128, 0.3) !important;
    }

    [data-testid="stSidebar"] h1 {
        text-align: center;
        font-size: 2rem !important;
        margin-bottom: 2rem;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #7928ca 0%, #ff0080 100%) !important;
        color: white !important;
        border: 2px solid #ff6b9d !important;
        border-radius: 15px !important;
        padding: 12px 30px !important;
        font-family: 'Orbitron', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
        box-shadow: 0 0 20px rgba(255, 0, 128, 0.5) !important;
        transition: all 0.3s ease !important;
        position: relative !important;
        overflow: hidden !important;
    }

    .stButton > button:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }

    .stButton > button:hover:before {
        left: 100%;
    }

    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 30px rgba(255, 0, 128, 0.8) !important;
        border-color: #ff6b9d !important;
    }

    /* Primary buttons */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #ff0080 0%, #ff6b9d 50%, #ff0080 100%) !important;
        background-size: 200% auto;
        animation: pulse 2s infinite, shimmer 3s linear infinite;
    }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 0, 128, 0.6), 0 0 40px rgba(255, 0, 128, 0.3); }
        50% { box-shadow: 0 0 40px rgba(255, 0, 128, 0.8), 0 0 60px rgba(255, 0, 128, 0.4); }
    }

    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stMultiSelect > div > div {
        background: rgba(255, 255, 255, 0.08) !important;
        border: 2px solid rgba(255, 0, 128, 0.3) !important;
        border-radius: 10px !important;
        color: #ff6b9d !important;
        font-family: 'Rajdhani', sans-serif !important;
        padding: 10px !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #ff0080 !important;
        box-shadow: 0 0 15px rgba(255, 0, 128, 0.5) !important;
    }

    /* Metrics */
    [data-testid="stMetricValue"] {
        font-family: 'Orbitron', sans-serif !important;
        color: #ff6b9d !important;
        font-size: 2rem !important;
        font-weight: 900 !important;
        text-shadow: 0 0 10px rgba(255, 0, 128, 0.5);
    }

    [data-testid="stMetricLabel"] {
        color: #c77dff !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
    }

    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #ff0080, #7928ca, #ff6b9d, #ff0080) !important;
        background-size: 200% auto;
        animation: shimmer 2s linear infinite;
        box-shadow: 0 0 10px rgba(255, 0, 128, 0.5);
    }

    /* Markdown text */
    .stMarkdown {
        color: #e0e0e0 !important;
    }

    /* Info/Warning/Success boxes */
    .stAlert {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px) !important;
        border-radius: 15px !important;
        border-left: 4px solid #ff0080 !important;
    }

    /* Slider */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #7928ca, #ff0080) !important;
    }

    /* Caption text */
    .stCaption {
        color: #c77dff !important;
        font-size: 0.9rem !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255, 0, 128, 0.3) !important;
        border-width: 2px !important;
        box-shadow: 0 0 10px rgba(255, 0, 128, 0.2);
    }

    /* Custom card effect */
    div[data-testid="column"] {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 15px;
        padding: 15px;
        border: 1px solid rgba(255, 0, 128, 0.15);
        transition: all 0.3s ease;
    }

    div[data-testid="column"]:hover {
        border-color: rgba(255, 0, 128, 0.3);
        box-shadow: 0 5px 20px rgba(255, 0, 128, 0.2);
    }

    /* Auth form styling */
    .auth-container {
        max-width: 450px;
        margin: 50px auto;
        padding: 40px;
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        border: 2px solid rgba(255, 0, 128, 0.4);
        border-radius: 25px;
        box-shadow: 0 15px 50px rgba(255, 0, 128, 0.3);
    }

    .auth-title {
        text-align: center;
        font-family: 'Orbitron', sans-serif;
        font-size: 2.5rem;
        color: #ff6b9d;
        margin-bottom: 30px;
        animation: neonGlow 2s ease-in-out infinite;
    }

    /* Scanline effect */
    @keyframes scanline {
        0% { transform: translateY(-100%); }
        100% { transform: translateY(100vh); }
    }

    .scanline {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 2px;
        background: linear-gradient(transparent, rgba(255, 0, 128, 0.5), transparent);
        animation: scanline 8s linear infinite;
        z-index: 1000;
        pointer-events: none;
    }

    /* Floating particles effect */
    @keyframes float {
        0%, 100% { transform: translateY(0) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(180deg); }
    }

    /* Enhanced text glow for important elements */
    .stMarkdown p strong {
        color: #ff6b9d;
        text-shadow: 0 0 5px rgba(255, 0, 128, 0.5);
    }

    /* Sidebar buttons enhanced */
    [data-testid="stSidebar"] button {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 0, 128, 0.2) !important;
        transition: all 0.3s ease !important;
    }

    [data-testid="stSidebar"] button:hover {
        background: rgba(255, 0, 128, 0.1) !important;
        border-color: rgba(255, 0, 128, 0.5) !important;
        box-shadow: 0 0 15px rgba(255, 0, 128, 0.3) !important;
    }

    /* Selectbox and multiselect dropdown styling */
    [data-baseweb="select"] {
        background: rgba(255, 255, 255, 0.05);
    }

    /* Success/Error/Warning/Info boxes custom colors */
    .element-container div[data-testid="stMarkdownContainer"] div[data-testid="stMarkdown"] {
        color: #e0e0e0;
    }

    /* Make subheaders stand out */
    .stApp h2, .stApp h3 {
        background: linear-gradient(90deg, #ff0080, #ff6b9d);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Enhanced metrics container */
    [data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        padding: 15px;
        border-radius: 12px;
        border: 1px solid rgba(255, 0, 128, 0.2);
        transition: all 0.3s ease;
    }

    [data-testid="metric-container"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(255, 0, 128, 0.25);
        border-color: rgba(255, 0, 128, 0.4);
    }

    /* Plotly chart containers */
    .js-plotly-plot {
        border-radius: 15px;
        overflow: hidden;
    }

    /* Add glow to icons in navigation */
    [data-testid="stSidebar"] button:hover {
        text-shadow: 0 0 10px rgba(255, 0, 128, 0.5);
    }

    /* Spinner customization */
    .stSpinner > div {
        border-top-color: #ff0080 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─── Data Directory Setup ───
DATA_DIR = "user_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

DB_FILE = os.path.join(DATA_DIR, "careercompass.db")

# ─── SQLite Database Setup ───
def get_db_conn():
    """Return a SQLite connection and ensure schema exists."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            username      TEXT PRIMARY KEY,
            email         TEXT NOT NULL,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS user_sessions (
            username        TEXT PRIMARY KEY,
            page            TEXT DEFAULT 'profiling',
            user_stream     TEXT,
            user_skills     TEXT,
            user_interests  TEXT,
            recommendations TEXT,
            selected_career TEXT,
            trial_progress  TEXT,
            trial_started   INTEGER DEFAULT 0,
            trial_start_date TEXT,
            trial_days_done TEXT
        );
        CREATE TABLE IF NOT EXISTS resumes (
            username          TEXT PRIMARY KEY,
            full_name         TEXT,
            phone             TEXT,
            career_objective  TEXT,
            education         TEXT,
            work_experience   TEXT,
            skills            TEXT
        );
        CREATE TABLE IF NOT EXISTS activity_log (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            action    TEXT NOT NULL,
            detail    TEXT,
            timestamp TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trial_journal (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            username  TEXT NOT NULL,
            career    TEXT NOT NULL,
            day       INTEGER NOT NULL,
            entry     TEXT,
            timestamp TEXT NOT NULL,
            UNIQUE(username, career, day)
        );
    """)
    # Seed demo account
    c.execute(
        "INSERT OR IGNORE INTO users (username, email, password_hash) VALUES (?, ?, ?)",
        ("demo", "demo@careercompass.ai", hashlib.sha256(b"demo123").hexdigest())
    )
    conn.commit()
    return conn

# ─── Authentication Helpers ───
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def db_user_exists(username):
    with get_db_conn() as conn:
        row = conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone()
    return row is not None

def db_check_login(username, password, skip_password=False):
    with get_db_conn() as conn:
        if skip_password:
            row = conn.execute("SELECT email FROM users WHERE username=?", (username,)).fetchone()
        else:
            ph = hash_password(password)
            row = conn.execute(
                "SELECT email FROM users WHERE username=? AND password_hash=?", (username, ph)
            ).fetchone()
    return dict(row) if row else None

def db_save_user(username, email, password):
    with get_db_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO users (username, email, password_hash) VALUES (?,?,?)",
            (username, email, hash_password(password))
        )
        conn.commit()

# ─── Session Persistence ───
def db_save_session(username):
    if not st.session_state.get("authenticated"):
        return
    rec = st.session_state.get("recommendations")
    days_done = {str(d): st.session_state.get(f"trial_day_{d}_done", False) for d in range(1, 8)}
    with get_db_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO user_sessions
            (username, page, user_stream, user_skills, user_interests,
             recommendations, selected_career, trial_progress,
             trial_started, trial_start_date, trial_days_done)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            username,
            st.session_state.page,
            st.session_state.user_stream,
            _json.dumps(st.session_state.user_skills),
            _json.dumps(st.session_state.user_interests),
            rec.to_json() if rec is not None else None,
            _json.dumps(st.session_state.selected_career),
            _json.dumps(st.session_state.trial_progress),
            int(st.session_state.trial_started),
            st.session_state.trial_start_date.isoformat() if st.session_state.trial_start_date else None,
            _json.dumps(days_done),
        ))
        conn.commit()

def db_load_session(username):
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM user_sessions WHERE username=?", (username,)).fetchone()
    if not row:
        return
    row = dict(row)
    st.session_state.page = row.get("page") or "profiling"
    st.session_state.user_stream = row.get("user_stream")
    st.session_state.user_skills = _json.loads(row["user_skills"]) if row.get("user_skills") else []
    st.session_state.user_interests = _json.loads(row["user_interests"]) if row.get("user_interests") else []
    try:
        rec_json = row.get("recommendations")
        st.session_state.recommendations = pd.read_json(io.StringIO(rec_json)) if rec_json else None
    except Exception:
        st.session_state.recommendations = None

    try:
        sc = row.get("selected_career")
        st.session_state.selected_career = _json.loads(sc) if sc else None
    except Exception:
        st.session_state.selected_career = None

    try:
        tp = row.get("trial_progress")
        st.session_state.trial_progress = _json.loads(tp) if tp else {}
    except Exception:
        st.session_state.trial_progress = {}

    st.session_state.trial_started = bool(row.get("trial_started", 0))

    try:
        tsd = row.get("trial_start_date")
        st.session_state.trial_start_date = date.fromisoformat(tsd) if tsd else None
    except (ValueError, TypeError):
        st.session_state.trial_start_date = None

    try:
        days_raw = row.get("trial_days_done")
        if days_raw:
            for d, val in _json.loads(days_raw).items():
                st.session_state[f"trial_day_{d}_done"] = val
    except Exception:
        pass

def save_session_to_storage():
    if st.session_state.get("authenticated") and st.session_state.get("username"):
        db_save_session(st.session_state.username)

def db_log_activity(username, action, detail=""):
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    with get_db_conn() as conn:
        conn.execute(
            "INSERT INTO activity_log (username, action, detail, timestamp) VALUES (?,?,?,?)",
            (username, action, detail, ts)
        )
        conn.commit()

def db_save_journal(username, career, day, entry):
    ts = datetime.now().isoformat(sep=" ", timespec="seconds")
    with get_db_conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO trial_journal (username, career, day, entry, timestamp) VALUES (?,?,?,?,?)",
            (username, career, day, entry, ts)
        )
        conn.commit()

def db_load_journal(username, career):
    with get_db_conn() as conn:
        rows = conn.execute(
            "SELECT day, entry FROM trial_journal WHERE username=? AND career=? ORDER BY day",
            (username, career)
        ).fetchall()
    return {row["day"]: row["entry"] for row in rows}

# ─── Resume Persistence ───
def db_save_resume(username, data):
    with get_db_conn() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO resumes
            (username, full_name, phone, career_objective, education, work_experience, skills)
            VALUES (?,?,?,?,?,?,?)
        """, (
            username,
            data.get("full_name", ""),
            data.get("phone", ""),
            data.get("career_objective", ""),
            _json.dumps(data.get("education", [])),
            _json.dumps(data.get("work_experience", [])),
            _json.dumps(data.get("skills", [])),
        ))
        conn.commit()

def db_load_resume(username):
    with get_db_conn() as conn:
        row = conn.execute("SELECT * FROM resumes WHERE username=?", (username,)).fetchone()
    if not row:
        return None
    row = dict(row)
    return {
        "full_name": row.get("full_name", ""),
        "phone": row.get("phone", ""),
        "career_objective": row.get("career_objective", ""),
        "education": _json.loads(row["education"]) if row.get("education") else [],
        "work_experience": _json.loads(row["work_experience"]) if row.get("work_experience") else [],
        "skills": _json.loads(row["skills"]) if row.get("skills") else [],
    }

def clear_local_storage():
    components.html("""
        <script>
            localStorage.removeItem('careercompass_current_user');
            localStorage.removeItem('careercompass_session');
        </script>
    """, height=0)

# ─── Load Data ───
@st.cache_data
def load_data():
    df = pd.read_csv("500.csv", on_bad_lines="skip")
    df.columns = df.columns.str.strip()
    return df

df = load_data()

# ─── Session State Defaults ───
defaults = {
    "authenticated": False,
    "username": None,
    "email": None,
    "page": "home",
    "user_stream": None,
    "user_skills": [],
    "user_interests": [],
    "recommendations": None,
    "selected_career": None,
    "trial_progress": {},
    "trial_started": False,
    "trial_start_date": None,
    "resume_education": [],
    "resume_work": [],
    "is_admin": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Ensure DB is initialised on startup
get_db_conn().close()

# ── Auto-restore session on page refresh ──
if not st.session_state.authenticated:
    _qp = st.query_params.get("u")
    if _qp:
        if _qp == ADMIN_USERNAME:
            st.session_state.authenticated = True
            st.session_state.is_admin = True
            st.session_state.username = ADMIN_USERNAME
            st.session_state.email = "admin@careercompass.ai"
        else:
            _row = db_check_login(_qp, None, skip_password=True)
            if _row:
                st.session_state.authenticated = True
                st.session_state.username = _qp
                st.session_state.email = _row["email"]
                db_load_session(_qp)

# Add scanline effect and floating particles
st.markdown('''
<div class="scanline"></div>
<div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; overflow: hidden;">
    <div style="position: absolute; width: 4px; height: 4px; background: #ff0080; border-radius: 50%; top: 20%; left: 10%; animation: float 6s ease-in-out infinite; opacity: 0.6; box-shadow: 0 0 10px #ff0080;"></div>
    <div style="position: absolute; width: 3px; height: 3px; background: #ff6b9d; border-radius: 50%; top: 40%; left: 80%; animation: float 8s ease-in-out infinite 1s; opacity: 0.5; box-shadow: 0 0 8px #ff6b9d;"></div>
    <div style="position: absolute; width: 5px; height: 5px; background: #7928ca; border-radius: 50%; top: 60%; left: 30%; animation: float 7s ease-in-out infinite 2s; opacity: 0.4; box-shadow: 0 0 12px #7928ca;"></div>
    <div style="position: absolute; width: 3px; height: 3px; background: #ff0080; border-radius: 50%; top: 80%; left: 70%; animation: float 9s ease-in-out infinite 0.5s; opacity: 0.6; box-shadow: 0 0 10px #ff0080;"></div>
    <div style="position: absolute; width: 4px; height: 4px; background: #c77dff; border-radius: 50%; top: 15%; left: 50%; animation: float 10s ease-in-out infinite 1.5s; opacity: 0.5; box-shadow: 0 0 8px #c77dff;"></div>
    <div style="position: absolute; width: 6px; height: 6px; background: #ff0080; border-radius: 50%; top: 70%; left: 15%; animation: float 6.5s ease-in-out infinite 3s; opacity: 0.4; box-shadow: 0 0 15px #ff0080;"></div>
    <div style="position: absolute; width: 3px; height: 3px; background: #ff6b9d; border-radius: 50%; top: 35%; left: 90%; animation: float 8.5s ease-in-out infinite 2.5s; opacity: 0.5; box-shadow: 0 0 8px #ff6b9d;"></div>
    <div style="position: absolute; width: 4px; height: 4px; background: #7928ca; border-radius: 50%; top: 90%; left: 45%; animation: float 7.5s ease-in-out infinite 1s; opacity: 0.6; box-shadow: 0 0 10px #7928ca;"></div>
</div>
''', unsafe_allow_html=True)

# ═══════════════════════════════════════════
# AUTHENTICATION PAGES
# ═══════════════════════════════════════════
if not st.session_state.authenticated:
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)

    # Toggle between login and signup
    if "auth_mode" not in st.session_state:
        st.session_state.auth_mode = "login"

    if st.session_state.auth_mode == "login":
        st.markdown('<h1 class="auth-title">🧭 CareerCompass</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color: #c77dff; font-size: 1.2rem; margin-bottom: 30px;">Navigate Your Future</p>', unsafe_allow_html=True)

        st.markdown("### 🔐 Login to Your Account")

        login_username = st.text_input("Username", key="login_username", placeholder="Enter your username")
        login_password = st.text_input("Password", type="password", key="login_password", placeholder="Enter your password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Login", type="primary", width="stretch"):
                if login_username and login_password:
                    # Admin check
                    if login_username == ADMIN_USERNAME and hashlib.sha256(login_password.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
                        st.session_state.authenticated = True
                        st.session_state.is_admin = True
                        st.session_state.username = ADMIN_USERNAME
                        st.session_state.email = "admin@careercompass.ai"
                        st.query_params["u"] = ADMIN_USERNAME
                        st.session_state.page = "admin"
                        st.success("✅ Admin login successful!")
                        st.rerun()
                    else:
                        user_row = db_check_login(login_username, login_password)
                        if user_row:
                            st.session_state.authenticated = True
                            st.session_state.username = login_username
                            st.session_state.email = user_row["email"]
                            db_load_session(login_username)
                            db_log_activity(login_username, "login")
                            st.query_params["u"] = login_username
                            if st.session_state.page not in ("home", "profiling", "recommendations", "roadmap", "trial", "score", "resume", "learned"):
                                st.session_state.page = "home"
                            st.success("✅ Login successful! Welcome back!")
                            st.rerun()
                        elif db_user_exists(login_username):
                            st.error("❌ Invalid password")
                        else:
                            st.error("❌ User not found. Please sign up first.")
                else:
                    st.error("⚠️ Please enter both username and password")

        with col2:
            if st.button("Create Account", width="stretch"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        st.markdown('<p style="text-align:center; color: #a0a0a0; margin-top: 30px; font-size: 0.9rem;">Your journey to the perfect career starts here</p>', unsafe_allow_html=True)

    else:  # signup mode
        st.markdown('<h1 class="auth-title">🧭 CareerCompass</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align:center; color: #c77dff; font-size: 1.2rem; margin-bottom: 30px;">Create Your Account</p>', unsafe_allow_html=True)

        st.markdown("### ✨ Join CareerCompass")

        signup_username = st.text_input("Username", key="signup_username", placeholder="Choose a username")
        signup_email = st.text_input("Email", key="signup_email", placeholder="your.email@example.com")
        signup_password = st.text_input("Password", type="password", key="signup_password", placeholder="Create a strong password")
        signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm", placeholder="Confirm your password")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Sign Up", type="primary", width="stretch"):
                if not signup_username or not signup_email or not signup_password:
                    st.error("⚠️ Please fill in all fields")
                elif db_user_exists(signup_username):
                    st.error("❌ Username already exists")
                elif "@" not in signup_email:
                    st.error("⚠️ Please enter a valid email address")
                elif signup_password != signup_confirm:
                    st.error("❌ Passwords do not match")
                elif len(signup_password) < 6:
                    st.error("⚠️ Password must be at least 6 characters")
                else:
                    db_save_user(signup_username, signup_email, signup_password)
                    st.session_state.authenticated = True
                    st.session_state.username = signup_username
                    st.session_state.email = signup_email
                    st.query_params["u"] = signup_username
                    save_session_to_storage()
                    st.success("✅ Account created successfully! Welcome aboard!")
                    st.balloons()
                    st.rerun()

        with col2:
            if st.button("Back to Login", width="stretch"):
                st.session_state.auth_mode = "login"
                st.rerun()

        st.markdown('<p style="text-align:center; color: #a0a0a0; margin-top: 30px; font-size: 0.9rem;">Already have an account? Use the button above to login</p>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# ═══════════════════════════════════════════
# MAIN APP (Authenticated Users Only)
# ═══════════════════════════════════════════

# ─── Sidebar Navigation ───
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 10px;'>
    <h1 style='font-size: 2.5rem; margin: 0; line-height: 1.2;'>🧭</h1>
    <h1 style='font-size: 1.5rem; margin: 0; line-height: 1.2;'>Career</h1>
    <h1 style='font-size: 1.5rem; margin: 0; line-height: 1.2;'>Compass</h1>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")

# User info section
if st.session_state.authenticated:
    st.sidebar.markdown(f"""
    <div style='padding: 15px; background: rgba(255, 0, 128, 0.1); border-radius: 10px; border: 1px solid rgba(255, 0, 128, 0.3); margin-bottom: 20px; box-shadow: 0 5px 15px rgba(255, 0, 128, 0.2);'>
        <p style='color: #ff6b9d; margin: 0; font-weight: bold; font-size: 1.1rem;'>👤 {st.session_state.username}</p>
        <p style='color: #c77dff; margin: 5px 0 0 0; font-size: 0.8rem;'>{st.session_state.email}</p>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.get("is_admin"):
    pages = {"admin": "🛡️ Admin Dashboard"}
else:
    pages = {
        "home": "🏠 Dashboard",
        "profiling": "1. Profile Assessment",
        "recommendations": "2. Career Matches",
        "roadmap": "3. Career GPS",
        "trial": "4. 7-Day Trial",
        "score": "5. Suitability Score",
        "resume": "📄 My Resume",
        "learned": "📘 LearnEd",
    }

for key, label in pages.items():
    if st.sidebar.button(label, width="stretch", key=f"nav_{key}"):
        st.session_state.page = key
        save_session_to_storage()

st.sidebar.markdown("---")

# Logout button
if st.sidebar.button("🚪 Logout", width="stretch"):
    if st.session_state.get("authenticated"):
        db_save_session(st.session_state.username)

    # Clear localStorage and URL param
    clear_local_storage()
    st.query_params.clear()

    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown("---")

page = st.session_state.page


# ═══════════════════════════════════════════
# PAGE 0: HOME DASHBOARD
# ═══════════════════════════════════════════
if page == "home":
    username = st.session_state.username
    career = st.session_state.selected_career
    career_name = career.get("career", "") if career else None

    st.title(f"👋 Welcome back, {username}!")
    st.markdown("Here's your CareerCompass journey so far.")
    st.markdown("---")

    # ── Progress Tracker ──
    steps = [
        ("Profile", st.session_state.user_stream is not None),
        ("Matches", st.session_state.recommendations is not None),
        ("Career Selected", career is not None),
        ("Trial", any(st.session_state.get(f"trial_day_{d}_done") for d in range(1, 8))),
        ("Score", False),  # no persistent score yet
        ("Resume", False),
    ]
    # Check resume
    with get_db_conn() as _c:
        _r = _c.execute("SELECT full_name FROM resumes WHERE username=?", (username,)).fetchone()
    if _r and _r["full_name"]:
        steps[-1] = ("Resume", True)

    st.markdown("### 🗺️ Your Journey")
    cols = st.columns(len(steps))
    for i, (label, done) in enumerate(steps):
        with cols[i]:
            color = "#00ff88" if done else "#555"
            icon = "✅" if done else "⬜"
            st.markdown(f"""<div style='text-align:center; padding:10px; border:1px solid {color};
                border-radius:10px; background:rgba(0,255,136,0.05)'>
                <div style='font-size:20px'>{icon}</div>
                <div style='color:{color}; font-size:12px; font-weight:bold'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Quick Stats ──
    col1, col2, col3, col4 = st.columns(4)
    trial_days_done = sum(1 for d in range(1, 8) if st.session_state.get(f"trial_day_{d}_done"))
    col1.metric("Stream", st.session_state.user_stream or "Not set")
    col2.metric("Career", career_name or "Not chosen")
    col3.metric("Trial Progress", f"{trial_days_done}/7 days")
    col4.metric("Resume", "Built ✅" if (_r and _r["full_name"]) else "Not built")

    st.markdown("---")

    # ── Continue CTA ──
    st.markdown("### ▶ Continue Where You Left Off")
    if not st.session_state.user_stream:
        next_page, next_label = "profiling", "Complete Profile Assessment"
    elif st.session_state.recommendations is None:
        next_page, next_label = "profiling", "Get Career Matches"
    elif not career:
        next_page, next_label = "recommendations", "Pick a Career"
    elif not st.session_state.trial_started:
        next_page, next_label = "roadmap", "Start 7-Day Trial"
    elif trial_days_done < 7:
        next_page, next_label = "trial", f"Continue Trial (Day {trial_days_done + 1})"
    elif not (_r and _r["full_name"]):
        next_page, next_label = "resume", "Build Your Resume"
    else:
        next_page, next_label = "learned", "Keep Learning on LearnEd"

    if st.button(f"🚀 {next_label}", type="primary"):
        st.session_state.page = next_page
        save_session_to_storage()
        st.rerun()

    st.markdown("---")

    # ── Career snapshot if chosen ──
    if career:
        mkt = get_market_data(career_name)
        st.markdown(f"### 💼 Your Career: {career_name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Avg Salary", mkt["salary"])
        c2.metric("Job Demand", mkt["demand"])
        c3.metric("Market Growth", f"{mkt['growth_icon']} {mkt['growth']}")
        c4.metric("Match Score", f"{round(career.get('match_score', 0) * 100, 1)}%")
        colleges = get_top_colleges(career_name)
        with st.expander("🏫 Top Colleges / Certifications for this career"):
            for c in colleges:
                st.markdown(f"- {c}")

# ═══════════════════════════════════════════
# PAGE 1: USER PROFILING
# ═══════════════════════════════════════════
elif page == "profiling":
    st.title("📋 Profile Assessment")
    st.markdown("Tell us about yourself so we can find your best career matches.")
    st.markdown("---")

    # Step 1: Stream selection
    streams = sorted(df["stream_after_12th"].dropna().unique().tolist())
    selected_stream = st.selectbox("What is your stream after 12th?", ["-- Select --"] + streams)

    if selected_stream != "-- Select --":
        st.session_state.user_stream = selected_stream

        # Filter careers for this stream
        stream_careers = df[
            df["stream_after_12th"].str.contains(selected_stream.split(" ")[0], case=False, na=False)
        ]

        # Step 2: Collect all skills & interests from matching careers
        all_skills = set()
        all_interests = set()
        for _, row in stream_careers.iterrows():
            if pd.notna(row["required_skills"]):
                all_skills.update([s.strip() for s in row["required_skills"].split(";")])
            if pd.notna(row["preferred_interests"]):
                all_interests.update([i.strip() for i in row["preferred_interests"].split(";")])

        all_skills = sorted(all_skills)
        all_interests = sorted(all_interests)

        st.markdown("### Your Skills & Strengths")
        selected_skills = st.multiselect(
            "Select skills you have or want to develop:",
            all_skills,
        )

        st.markdown("### Your Interests")
        selected_interests = st.multiselect(
            "Select topics that excite you:",
            all_interests,
        )

        if st.button("🔍 Find My Career Matches", type="primary"):
            if not selected_skills and not selected_interests:
                st.warning("Please select at least one skill or interest.")
            else:
                st.session_state.user_skills = selected_skills
                st.session_state.user_interests = selected_interests

                # Build user text vector
                user_text = " ".join(selected_skills) + " " + " ".join(selected_interests)

                # Build career text vectors from relevant columns
                career_texts = []
                for _, row in df.iterrows():
                    parts = []
                    if pd.notna(row["required_skills"]):
                        parts.append(row["required_skills"].replace(";", " "))
                    if pd.notna(row["preferred_interests"]):
                        parts.append(row["preferred_interests"].replace(";", " "))
                    if pd.notna(row["career_description"]):
                        parts.append(row["career_description"])
                    career_texts.append(" ".join(parts))

                # TF-IDF + Cosine Similarity
                corpus = [user_text] + career_texts
                vectorizer = TfidfVectorizer(stop_words="english")
                tfidf_matrix = vectorizer.fit_transform(corpus)
                similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

                df_copy = df.copy()
                df_copy["match_score"] = similarities
                top_matches = df_copy.nlargest(5, "match_score")

                st.session_state.recommendations = top_matches
                st.session_state.page = "recommendations"
                save_session_to_storage()
                st.rerun()


# ═══════════════════════════════════════════
# PAGE 2: RECOMMENDATIONS
# ═══════════════════════════════════════════
elif page == "recommendations":
    st.title("🎯 Your Career Matches")

    if st.session_state.recommendations is None:
        st.info("Complete the Profile Assessment first to see your matches.")
    else:
        top = st.session_state.recommendations

        for idx, (_, row) in enumerate(top.iterrows()):
            match_pct = round(row["match_score"] * 100, 1)

            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader(f"{'🥇' if idx == 0 else '🥈' if idx == 1 else '🥉' if idx == 2 else '⭐'} {row['career']}")
                    st.markdown(f"**{row['career_description']}**")
                    st.markdown(f"📚 **Education:** {row['education_level_min']} &nbsp;|&nbsp; ⏱ **Duration:** {row['time_years_avg']} years &nbsp;|&nbsp; 💰 **Cost:** ₹{row['cost_inr_avg']:,.0f}")
                    st.markdown(f"📊 **Difficulty:** {row['difficulty_level']} &nbsp;|&nbsp; ⚡ **Risk:** {row['risk_level']} &nbsp;|&nbsp; 🔥 **Popularity:** {row['popularity_in_india']}")
                    mkt = get_market_data(row['career'])
                    st.markdown(f"💰 **Avg Salary:** {mkt['salary']} &nbsp;|&nbsp; {mkt['growth_icon']} **Market Growth:** {mkt['growth']} &nbsp;|&nbsp; 🎯 **Demand:** {mkt['demand']}")

                    skills_raw = row["required_skills"] if pd.notna(row.get("required_skills")) else ""
                    required = [s.strip().lower() for s in skills_raw.split(";") if s.strip()]
                    user_skills_lower = [s.strip().lower() for s in st.session_state.get("user_skills", [])]
                    have = [s for s in required if any(s in u or u in s for u in user_skills_lower)]
                    missing = [s for s in required if s not in have]
                    if required:
                        gap_pct = int(len(have) / len(required) * 100)
                        st.progress(gap_pct / 100, text=f"Skill match: {len(have)}/{len(required)} ({gap_pct}%)")
                        if have:
                            st.caption("✅ You have: " + " • ".join(s.title() for s in have[:5]))
                        if missing:
                            st.caption("📚 To learn: " + " • ".join(s.title() for s in missing[:5]))
                    else:
                        st.caption(f"Skills: {skills_raw.replace(';', ' • ')}")

                with col2:
                    # Match percentage gauge
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=match_pct,
                        number={"suffix": "%"},
                        gauge={
                            "axis": {"range": [0, 100]},
                            "bar": {"color": "#2ecc71" if match_pct > 50 else "#e67e22"},
                            "steps": [
                                {"range": [0, 40], "color": "#fdebd0"},
                                {"range": [40, 70], "color": "#d5f5e3"},
                                {"range": [70, 100], "color": "#abebc6"},
                            ],
                        },
                    ))
                    fig.update_layout(height=180, margin=dict(t=30, b=10, l=30, r=30))
                    st.plotly_chart(fig, use_container_width=True, key=f"gauge_{idx}")

                col_exp, col_cmp = st.columns([2, 1])
                with col_exp:
                    if st.button(f"🚀 Explore {row['career']}", key=f"explore_{idx}"):
                        st.session_state.selected_career = row.to_dict()
                        st.session_state.page = "roadmap"
                        db_log_activity(st.session_state.username, "career_selected", row['career'])
                        save_session_to_storage()
                        st.rerun()
                with col_cmp:
                    cmp_key = f"compare_{idx}"
                    if cmp_key not in st.session_state:
                        st.session_state[cmp_key] = False
                    label = "✅ Selected for Compare" if st.session_state[cmp_key] else "⚖️ Compare"
                    if st.button(label, key=f"cmpbtn_{idx}"):
                        st.session_state[cmp_key] = not st.session_state[cmp_key]
                        st.rerun()

                st.markdown("---")

        # ── Career Comparison Panel ──
        selected_for_compare = [row for idx, (_, row) in enumerate(top.iterrows()) if st.session_state.get(f"compare_{idx}")]
        if len(selected_for_compare) >= 2:
            st.markdown("## ⚖️ Career Comparison")
            c1, c2 = selected_for_compare[0], selected_for_compare[1]
            fields = [
                ("Match Score", lambda r: f"{round(r['match_score']*100,1)}%"),
                ("Avg Salary", lambda r: get_market_data(r['career'])['salary']),
                ("Market Growth", lambda r: get_market_data(r['career'])['growth']),
                ("Job Demand", lambda r: get_market_data(r['career'])['demand']),
                ("Education", lambda r: str(r.get('education_level_min',''))),
                ("Duration", lambda r: f"{r.get('time_years_avg','')} yrs"),
                ("Difficulty", lambda r: str(r.get('difficulty_level',''))),
                ("Risk", lambda r: str(r.get('risk_level',''))),
            ]
            hdr, col_a, col_b = st.columns([2, 3, 3])
            hdr.markdown("**Field**")
            col_a.markdown(f"**{c1['career']}**")
            col_b.markdown(f"**{c2['career']}**")
            for label, fn in fields:
                hdr, col_a, col_b = st.columns([2, 3, 3])
                hdr.markdown(f"*{label}*")
                col_a.markdown(fn(c1))
                col_b.markdown(fn(c2))
            st.markdown("---")
        elif len(selected_for_compare) == 1:
            st.info("Select one more career to compare ⚖️")


# ═══════════════════════════════════════════
# PAGE 3: CAREER GPS ROADMAP
# ═══════════════════════════════════════════
elif page == "roadmap":
    st.title("🗺️ Career GPS — Your Roadmap")

    career = st.session_state.selected_career
    if career is None:
        st.info("Select a career from your matches first.")
    else:
        st.subheader(f"Roadmap for: {career['career']}")
        st.markdown(f"*{career['career_description']}*")
        st.markdown("---")

        # Build roadmap steps from data
        education = career.get("education_level_min", "Bachelor's")
        duration_raw = str(career.get("time_years_avg", "4"))
        cost_raw = career.get("cost_inr_avg", 0)
        try:
            cost = float(cost_raw)
        except (ValueError, TypeError):
            cost = 0
        skills = career.get("required_skills", "").split(";") if pd.notna(career.get("required_skills")) else []
        stream = career.get("stream_after_12th", "")

        # Parse duration safely — handles "4", "4-5", "5.5-10", "10+", etc.
        nums = re.findall(r"[\d.]+", duration_raw)
        dur_start = int(float(nums[0])) if nums else 4
        dur_end = int(float(nums[-1])) if nums else dur_start

        roadmap_steps = [
            {"phase": "Class 12th", "detail": f"Stream: {stream}", "icon": "📖", "year": "Year 0"},
            {"phase": "Entrance Exam", "detail": "Prepare & qualify for entrance exams", "icon": "📝", "year": "Year 0-1"},
            {"phase": "Education", "detail": f"{education} (Est. ₹{cost:,.0f})", "icon": "🎓", "year": f"Year 1-{dur_end}"},
            {"phase": "Skill Building", "detail": " • ".join(skills[:5]), "icon": "🛠️", "year": "Ongoing"},
            {"phase": "Internship / Entry Job", "detail": "Gain hands-on industry experience", "icon": "💼", "year": f"Year {dur_end}"},
            {"phase": "Career Launch", "detail": f"Start as {career['career']}", "icon": "🚀", "year": f"Year {dur_end + 1}+"},
        ]

        # Vertical timeline using Plotly
        phases = [s["phase"] for s in roadmap_steps]
        details = [s["detail"] for s in roadmap_steps]
        icons = [s["icon"] for s in roadmap_steps]
        years = [s["year"] for s in roadmap_steps]
        y_positions = list(range(len(phases) - 1, -1, -1))

        fig = go.Figure()

        # Vertical line
        fig.add_trace(go.Scatter(
            x=[0.5] * len(y_positions),
            y=y_positions,
            mode="lines",
            line=dict(color="#3498db", width=4),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Nodes
        fig.add_trace(go.Scatter(
            x=[0.5] * len(y_positions),
            y=y_positions,
            mode="markers+text",
            marker=dict(size=30, color="#3498db", line=dict(width=2, color="white")),
            text=icons,
            textfont=dict(size=16),
            showlegend=False,
            hoverinfo="skip",
        ))

        # Labels
        for i, (phase, detail, year, yp) in enumerate(zip(phases, details, years, y_positions)):
            fig.add_annotation(
                x=0.9, y=yp,
                text=f"<b>{phase}</b><br><span style='font-size:11px'>{detail}</span>",
                showarrow=False, xanchor="left",
                font=dict(size=14),
            )
            fig.add_annotation(
                x=0.1, y=yp,
                text=f"<b>{year}</b>",
                showarrow=False, xanchor="right",
                font=dict(size=12, color="#7f8c8d"),
            )

        fig.update_layout(
            height=500,
            xaxis=dict(visible=False, range=[-0.5, 3]),
            yaxis=dict(visible=False, range=[-0.5, len(phases)]),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Duration", f"{duration_raw} yrs")
        col2.metric("Cost (Approx)", f"₹{cost:,.0f}")
        col3.metric("Difficulty", career.get("difficulty_level", "N/A"))
        col4.metric("Risk Level", career.get("risk_level", "N/A"))

        # Top colleges
        colleges = get_top_colleges(career["career"])
        mkt = get_market_data(career["career"])
        st.markdown("---")
        col_sal, col_dem, col_grow = st.columns(3)
        col_sal.metric("💰 Avg Salary", mkt["salary"])
        col_dem.metric("🎯 Job Demand", mkt["demand"])
        col_grow.metric("📈 Market Growth", f"{mkt['growth_icon']} {mkt['growth']}")

        with st.expander("🏫 Top Colleges & Certifications"):
            for c in colleges:
                st.markdown(f"- {c}")

        st.markdown("---")
        if st.button("🧪 Start 7-Day Career Trial", type="primary"):
            st.session_state.trial_progress = {}
            st.session_state.trial_started = True
            st.session_state.trial_start_date = None  # will be set on first trial page load
            # Reset per-day completion keys
            for _d in range(1, 8):
                st.session_state[f"trial_day_{_d}_done"] = False
            st.session_state.page = "trial"
            save_session_to_storage()
            st.rerun()


# ═══════════════════════════════════════════
# PAGE 4: 7-DAY CAREER TRIAL
# ═══════════════════════════════════════════
elif page == "trial":
    st.title("🧪 7-Day Career Trial")

    career = st.session_state.selected_career
    if career is None:
        st.info("Select a career first from your matches.")
        st.stop()

    st.subheader(f"Evaluating: **{career['career']}**")
    st.markdown("One task unlocks per day. Come back daily to complete your trial.")
    st.markdown("---")

    # Set trial start date on first visit
    if st.session_state.trial_start_date is None:
        st.session_state.trial_start_date = date.today()
        save_session_to_storage()

    today = date.today()
    days_passed = (today - st.session_state.trial_start_date).days + 1
    unlocked_day = min(days_passed, 7)

    tasks = get_trial_tasks_for_career(career["career"])
    quizzes = get_trial_quizzes(career["career"])
    journal_entries = db_load_journal(st.session_state.username, career["career"])

    completed_count = 0

    for day in range(1, 8):
        locked = day > unlocked_day
        done_key = f"trial_day_{day}_done"
        quiz_answered_key = f"trial_day_{day}_quiz_answered"
        quiz_choice_key = f"trial_day_{day}_quiz_choice"

        if done_key not in st.session_state:
            st.session_state[done_key] = False
        if quiz_answered_key not in st.session_state:
            st.session_state[quiz_answered_key] = False

        with st.container():
            col1, col2, col3 = st.columns([0.5, 3.5, 1])
            with col1:
                st.markdown(f"### Day {day}")
            with col2:
                if locked:
                    st.markdown(f"*{tasks[day]}*")
                    st.info("🔒 Locked — unlocks in a future session")
                elif st.session_state[done_key]:
                    st.markdown(f"~~{tasks[day]}~~")
                    st.caption(DAILY_MOTIVATION[day])
                else:
                    st.markdown(f"**{tasks[day]}**")
                    st.caption(DAILY_MOTIVATION[day])
                    video_url = get_trial_video_url(career["career"], day, tasks[day])
                    st.markdown(f"🎥 [Watch: {tasks[day]}]({video_url})")
            with col3:
                if not locked:
                    if st.session_state[done_key]:
                        st.markdown("✅")
                        completed_count += 1
                    else:
                        if st.button("Mark Done", key=f"btn_day_{day}"):
                            st.session_state[done_key] = True
                            db_log_activity(st.session_state.username, f"trial_day_{day}_done", career["career"])
                            save_session_to_storage()
                            st.rerun()

        # ── Day Quiz (3 questions, shown after task is marked done) ──
        if not locked and st.session_state[done_key]:
            day_questions = quizzes[day]  # list of 3 dicts
            with st.expander(f"🧠 Day {day} Quiz — {len(day_questions)} questions", expanded=not st.session_state[quiz_answered_key]):
                all_answered = True
                for qi, q in enumerate(day_questions):
                    choice_key = f"trial_day_{day}_q{qi}_choice"
                    st.markdown(f"**Q{qi+1}. {q['q']}**")
                    st.radio(
                        f"q{day}_{qi}",
                        options=q["opts"],
                        index=None,
                        key=choice_key,
                        label_visibility="collapsed",
                    )
                    if st.session_state.get(choice_key) is None:
                        all_answered = False
                    st.markdown("")

                if not st.session_state[quiz_answered_key]:
                    if st.button("Submit Answers", key=f"quiz_submit_{day}"):
                        unanswered = [qi+1 for qi, q in enumerate(day_questions) if st.session_state.get(f"trial_day_{day}_q{qi}_choice") is None]
                        if unanswered:
                            st.warning(f"Please answer Q{', Q'.join(map(str, unanswered))} before submitting.")
                        else:
                            st.session_state[quiz_answered_key] = True
                            st.rerun()
                else:
                    correct_count = 0
                    for qi, q in enumerate(day_questions):
                        choice_key = f"trial_day_{day}_q{qi}_choice"
                        correct = q["opts"][q["ans"]]
                        user_choice = st.session_state.get(choice_key)
                        if user_choice == correct:
                            st.success(f"✅ Q{qi+1}: Correct! — **{correct}**")
                            correct_count += 1
                        else:
                            st.error(f"❌ Q{qi+1}: Correct answer — **{correct}**")
                    st.markdown(f"**Score: {correct_count}/{len(day_questions)}**")

        # ── Day Journal ──
        if not locked and st.session_state[done_key]:
            with st.expander(f"📓 Day {day} Reflection Journal", expanded=False):
                journal_key = f"journal_input_day_{day}"
                saved_entry = journal_entries.get(day, "")
                if journal_key not in st.session_state:
                    st.session_state[journal_key] = saved_entry
                entry = st.text_area(
                    "Write your reflection for today (what did you learn? how did it feel?)",
                    value=st.session_state[journal_key],
                    key=f"journal_ta_{day}",
                    height=100,
                )
                if st.button("💾 Save Reflection", key=f"save_journal_{day}"):
                    db_save_journal(st.session_state.username, career["career"], day, entry)
                    st.session_state[journal_key] = entry
                    st.success("Saved!")

        st.markdown("---")

    st.progress(completed_count / 7, text=f"{completed_count}/7 days completed")

    if completed_count == 7:
        st.success("🎉 You've completed the 7-Day Trial! Time to evaluate your experience.")
        if st.button("📊 Calculate Suitability Score", type="primary"):
            st.session_state.page = "score"
            save_session_to_storage()
            st.rerun()
    elif completed_count > 0:
        st.info(f"{7 - completed_count} more days to go. Keep it up!")


# ═══════════════════════════════════════════
# PAGE 5: SUITABILITY SCORE
# ═══════════════════════════════════════════
elif page == "score":
    st.title("📊 Suitability Score")

    career = st.session_state.selected_career
    if career is None:
        st.info("Complete a career trial first.")
    else:
        st.subheader(f"Evaluating: {career['career']}")
        st.markdown("Rate your experience from the 7-Day Trial.")
        st.markdown("---")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### Interest")
            st.caption("How much did the tasks excite you?")
            interest = st.slider("Interest Score", 1, 10, 5, key="interest_slider")

        with col2:
            st.markdown("### Confidence")
            st.caption("How confident do you feel pursuing this?")
            confidence = st.slider("Confidence Score", 1, 10, 5, key="confidence_slider")

        with col3:
            st.markdown("### Satisfaction")
            st.caption("How satisfying was the experience?")
            satisfaction = st.slider("Satisfaction Score", 1, 10, 5, key="satisfaction_slider")

        st.markdown("---")

        if st.button("Calculate My Score", type="primary"):
            score = (interest * 0.4) + (confidence * 0.4) + (satisfaction * 0.2)
            db_log_activity(st.session_state.username, "score_calculated", f"{score:.1f} for {career['career']}")

            st.markdown("---")
            st.markdown("## Your Results")

            # Score gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=score,
                number={"suffix": "/10"},
                title={"text": "Suitability Score"},
                gauge={
                    "axis": {"range": [0, 10]},
                    "bar": {"color": "#2ecc71" if score >= 7 else "#e67e22" if score >= 4 else "#e74c3c"},
                    "steps": [
                        {"range": [0, 4], "color": "#fdebd0"},
                        {"range": [4, 7], "color": "#fef9e7"},
                        {"range": [7, 10], "color": "#d5f5e3"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 7,
                    },
                },
            ))
            fig.update_layout(height=300, margin=dict(t=60, b=20))
            st.plotly_chart(fig, use_container_width=True)

            # Breakdown
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Interest (×0.4)", f"{interest}/10")
            col2.metric("Confidence (×0.4)", f"{confidence}/10")
            col3.metric("Satisfaction (×0.2)", f"{satisfaction}/10")
            col4.metric("Final Score", f"{score:.1f}/10")

            st.markdown("---")

            # Go/No-Go recommendation
            if score >= 7:
                st.success(f"## ✅ GO — {career['career']} is a great fit for you!")
                st.markdown(
                    f"Your score of **{score:.1f}/10** shows strong alignment. "
                    f"You showed genuine interest and confidence in this field. "
                    f"We recommend pursuing **{career['career']}** as a serious career path."
                )
                st.balloons()
            elif score >= 4:
                st.warning(f"## ⚠️ EXPLORE MORE — {career['career']} shows potential")
                st.markdown(
                    f"Your score of **{score:.1f}/10** indicates moderate interest. "
                    f"Consider exploring this career further or trying related careers "
                    f"before making a final decision."
                )
            else:
                st.error(f"## ❌ NO-GO — {career['career']} may not be the best fit")
                st.markdown(
                    f"Your score of **{score:.1f}/10** suggests this career didn't resonate with you. "
                    f"That's completely okay! Go back and explore other career matches."
                )

            st.markdown("---")
            st.markdown("### 🧭 What's Next?")

            if score >= 7:
                st.markdown("You're ready to move forward. Here's your action plan:")
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.markdown("""<div style='padding:16px; border:1px solid #00ff88; border-radius:10px; text-align:center'>
                        <div style='font-size:28px'>📄</div>
                        <div style='font-weight:bold; color:#00ff88'>Build Resume</div>
                        <div style='font-size:12px; color:#aaa'>Showcase your skills & trial experience</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown("")
                    if st.button("Build My Resume", key="next_resume"):
                        st.session_state.page = "resume"
                        save_session_to_storage()
                        st.rerun()
                with c2:
                    st.markdown("""<div style='padding:16px; border:1px solid #00d4ff; border-radius:10px; text-align:center'>
                        <div style='font-size:28px'>📘</div>
                        <div style='font-weight:bold; color:#00d4ff'>Start Learning</div>
                        <div style='font-size:12px; color:#aaa'>Deep-dive into courses, roadmaps & quizzes</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown("")
                    if st.button("Go to LearnEd", key="next_learned"):
                        st.session_state.page = "learned"
                        save_session_to_storage()
                        st.rerun()
                with c3:
                    colleges = get_top_colleges(career.get("career", ""))
                    st.markdown(f"""<div style='padding:16px; border:1px solid #f4c430; border-radius:10px; text-align:center'>
                        <div style='font-size:28px'>🏫</div>
                        <div style='font-weight:bold; color:#f4c430'>Top Colleges</div>
                        <div style='font-size:12px; color:#aaa'>{colleges[0] if colleges else "See recommendations"}</div>
                    </div>""", unsafe_allow_html=True)
                    st.markdown("")
                    with st.expander("See all colleges"):
                        for c in colleges:
                            st.markdown(f"- {c}")

            elif score >= 4:
                st.markdown("You're on the right track — explore deeper before deciding.")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("📘 Go Deeper with LearnEd", key="next_learned_explore"):
                        st.session_state.page = "learned"
                        save_session_to_storage()
                        st.rerun()
                with c2:
                    if st.button("🎯 Try a Different Career", key="next_rec_explore"):
                        st.session_state.page = "recommendations"
                        save_session_to_storage()
                        st.rerun()
            else:
                st.markdown("No worries — finding the wrong fit is useful data. Try a different career.")
                if st.button("🎯 Explore Other Career Matches", key="next_rec_nogo"):
                    st.session_state.page = "recommendations"
                    save_session_to_storage()
                    st.rerun()

            st.markdown("---")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🔙 Back to Career Matches"):
                    st.session_state.page = "recommendations"
                    save_session_to_storage()
                    st.rerun()
            with col_b:
                if st.button("🔄 Start Over with New Profile"):
                    username = st.session_state.username
                    email = st.session_state.email
                    for key in defaults:
                        st.session_state[key] = defaults[key]
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.email = email
                    save_session_to_storage()
                    st.rerun()


# ═══════════════════════════════════════════
# PAGE 6: RESUME
# ═══════════════════════════════════════════
elif page == "resume":
    st.title("📄 My Resume")
    st.markdown("Build your career resume. Your data is saved automatically.")
    st.markdown("---")

    username = st.session_state.username

    # Load saved resume on first visit to this page
    if "resume_loaded" not in st.session_state:
        saved = db_load_resume(username)
        if saved:
            st.session_state.resume_full_name = saved["full_name"]
            st.session_state.resume_phone = saved["phone"]
            st.session_state.resume_objective = saved["career_objective"]
            st.session_state.resume_education = saved["education"]
            st.session_state.resume_work = saved["work_experience"]
            # Skills: use saved if present, else pre-fill from profile
            st.session_state.resume_skills = saved["skills"] if saved["skills"] else st.session_state.user_skills[:]
        else:
            st.session_state.resume_full_name = ""
            st.session_state.resume_phone = ""
            st.session_state.resume_objective = ""
            st.session_state.resume_education = []
            st.session_state.resume_work = []
            st.session_state.resume_skills = st.session_state.user_skills[:]
        st.session_state.resume_loaded = True

    # ── Personal Information ──
    st.subheader("👤 Personal Information")
    col1, col2 = st.columns(2)
    with col1:
        r_name = st.text_input("Full Name", value=st.session_state.resume_full_name, key="r_name")
        r_email = st.text_input("Email", value=st.session_state.email, disabled=True)
    with col2:
        r_phone = st.text_input("Phone Number", value=st.session_state.resume_phone, key="r_phone")
    r_objective = st.text_area(
        "Career Objective",
        value=st.session_state.resume_objective,
        key="r_objective",
        placeholder="A motivated student seeking opportunities in...",
        height=90,
    )

    st.markdown("---")

    # ── Education ──
    st.subheader("🎓 Education")
    if st.session_state.resume_education:
        for i, edu in enumerate(st.session_state.resume_education):
            cols = st.columns([3, 2, 1, 1, 0.5])
            cols[0].write(f"**{edu.get('degree','')}** — {edu.get('college','')}")
            cols[1].write(f"Year: {edu.get('year','')}")
            cols[2].write(f"Grade: {edu.get('grade','')}")
            if cols[4].button("✕", key=f"del_edu_{i}"):
                st.session_state.resume_education.pop(i)
                st.rerun()

    with st.expander("➕ Add Education"):
        ec1, ec2, ec3, ec4 = st.columns(4)
        new_degree = ec1.text_input("Degree / Course", key="new_degree")
        new_college = ec2.text_input("College / School", key="new_college")
        new_year = ec3.text_input("Year of Passing", key="new_year")
        new_grade = ec4.text_input("Grade / %", key="new_grade")
        if st.button("Add Education Entry"):
            if new_degree and new_college:
                st.session_state.resume_education.append({
                    "degree": new_degree, "college": new_college,
                    "year": new_year, "grade": new_grade,
                })
                st.rerun()
            else:
                st.warning("Degree and College are required.")

    st.markdown("---")

    # ── Skills ──
    st.subheader("🛠️ Skills")
    all_available_skills = sorted(set(
        [s.strip() for s in df["required_skills"].dropna().str.split(";").explode().tolist() if s.strip()]
    ))
    r_skills = st.multiselect(
        "Select your skills (pre-filled from your profile):",
        options=all_available_skills,
        default=[s for s in st.session_state.resume_skills if s in all_available_skills],
        key="r_skills_select",
    )

    st.markdown("---")

    # ── Work Experience ──
    st.subheader("💼 Work Experience / Internships")
    if st.session_state.resume_work:
        for i, work in enumerate(st.session_state.resume_work):
            cols = st.columns([2, 2, 1, 0.5])
            cols[0].write(f"**{work.get('role','')}** at {work.get('company','')}")
            cols[1].write(work.get("description", ""))
            cols[2].write(f"{work.get('duration','')}")
            if cols[3].button("✕", key=f"del_work_{i}"):
                st.session_state.resume_work.pop(i)
                st.rerun()

    with st.expander("➕ Add Work Experience"):
        wc1, wc2 = st.columns(2)
        new_company = wc1.text_input("Company / Organisation", key="new_company")
        new_role = wc2.text_input("Role / Position", key="new_role")
        wc3, wc4 = st.columns(2)
        new_duration = wc3.text_input("Duration (e.g. Jun 2024 – Aug 2024)", key="new_duration")
        new_desc = wc4.text_input("Brief Description", key="new_desc")
        if st.button("Add Work Entry"):
            if new_company and new_role:
                st.session_state.resume_work.append({
                    "company": new_company, "role": new_role,
                    "duration": new_duration, "description": new_desc,
                })
                st.rerun()
            else:
                st.warning("Company and Role are required.")

    st.markdown("---")

    # ── Save & Preview ──
    if st.button("💾 Save Resume", type="primary"):
        db_log_activity(username, "resume_saved")
        db_save_resume(username, {
            "full_name": r_name,
            "phone": r_phone,
            "career_objective": r_objective,
            "education": st.session_state.resume_education,
            "work_experience": st.session_state.resume_work,
            "skills": r_skills,
        })
        # Update session cache
        st.session_state.resume_full_name = r_name
        st.session_state.resume_phone = r_phone
        st.session_state.resume_objective = r_objective
        st.session_state.resume_skills = r_skills
        st.success("✅ Resume saved successfully!")

    pdf_bytes = generate_resume_pdf({
        "full_name": r_name,
        "email": st.session_state.email,
        "phone": r_phone,
        "career_objective": r_objective,
        "education": st.session_state.resume_education,
        "work_experience": st.session_state.resume_work,
        "skills": r_skills,
    })
    st.download_button(
        label="📥 Download Resume as PDF",
        data=pdf_bytes,
        file_name=f"{r_name or 'resume'}_resume.pdf",
        mime="application/pdf",
    )

    st.markdown("---")
    st.subheader("👁️ Resume Preview")
    career_name = (st.session_state.selected_career or {}).get("career", "")
    st.markdown(f"""
---
**{r_name or '[ Your Name ]'}**
{st.session_state.email} &nbsp;|&nbsp; {r_phone or '[ Phone ]'}

**Career Objective**
{r_objective or '*Not set*'}

**Education**
""")
    if st.session_state.resume_education:
        for edu in st.session_state.resume_education:
            st.markdown(f"- **{edu['degree']}** — {edu['college']} ({edu.get('year','')}) · {edu.get('grade','')}")
    else:
        st.markdown("*No education entries yet*")

    st.markdown("**Skills**")
    if r_skills:
        st.markdown(" · ".join(r_skills))
    else:
        st.markdown("*No skills selected*")

    st.markdown("**Work Experience**")
    if st.session_state.resume_work:
        for w in st.session_state.resume_work:
            st.markdown(f"- **{w['role']}** at {w['company']} ({w.get('duration','')}) — {w.get('description','')}")
    else:
        st.markdown("*No work experience added yet*")
    st.markdown("---")


# ═══════════════════════════════════════════
# PAGE 7: LEARNED – LEARNING PLATFORM
# ═══════════════════════════════════════════
elif page == "learned":
    # ── Career Resources Data ──
    def get_career_resources(career_name):
        cn = career_name or ""

        if any(k in cn for k in ["Government", "Civil", "IAS", "UPSC", "State Civil"]):
            return {
                "videos": [
                    ("UPSC CSE Complete Strategy — Beginner to Advanced", "https://www.youtube.com/results?search_query=UPSC+CSE+complete+strategy+beginner+to+advanced"),
                    ("How to Read The Hindu for UPSC Current Affairs", "https://www.youtube.com/results?search_query=how+to+read+the+hindu+for+UPSC+current+affairs"),
                    ("IAS Topper Interview & Success Story", "https://www.youtube.com/results?search_query=IAS+topper+interview+success+story"),
                    ("UPSC Prelims GS Paper 1 — Full Syllabus Breakdown", "https://www.youtube.com/results?search_query=UPSC+prelims+GS+paper+1+syllabus+breakdown"),
                    ("Day in the Life of an IAS Officer", "https://www.youtube.com/results?search_query=day+in+life+IAS+officer+vlog"),
                    ("Indian Polity — Laxmikanth Summary", "https://www.youtube.com/results?search_query=indian+polity+laxmikanth+summary+UPSC"),
                ],
                "links": {
                    "Official & Exam": [
                        ("UPSC Official Website", "https://upsc.gov.in/"),
                        ("UPSC Previous Year Papers", "https://upsc.gov.in/examinations/previous-question-papers"),
                        ("PIB — Press Information Bureau", "https://pib.gov.in/"),
                    ],
                    "Free Courses & Study": [
                        ("BYJU's Free IAS Prep", "https://byjus.com/free-ias-prep/"),
                        ("Unacademy UPSC (free lessons)", "https://unacademy.com/goal/upsc-civil-services-examination-ias/KSCIND"),
                        ("Khan Academy — Civics & Government", "https://www.khanacademy.org/humanities/us-government-and-civics"),
                        ("NCERT Books (free PDFs)", "https://ncert.nic.in/textbook.php"),
                    ],
                    "Practice & Mock Tests": [
                        ("Testbook UPSC Mock Tests", "https://testbook.com/upsc"),
                        ("Insights IAS Test Series", "https://www.insightsonindia.com/"),
                        ("Drishti IAS — Current Affairs Quiz", "https://www.drishtiias.com/"),
                    ],
                    "News & Current Affairs": [
                        ("The Hindu — UPSC Essentials", "https://www.thehindu.com/"),
                        ("PRS India — Legislative Research", "https://prsindia.org/"),
                        ("Indian Express Explained", "https://indianexpress.com/section/explained/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Understand the UPSC CSE exam structure: Prelims → Mains → Interview"),
                    ("Beginner", "Start NCERT books (Class 6–12): History, Geography, Polity, Economics, Science"),
                    ("Beginner", "Read Laxmikanth's Indian Polity — the single most important book for Polity"),
                    ("Intermediate", "Follow current affairs daily: The Hindu + PIB + government schemes"),
                    ("Intermediate", "Master CSAT Paper 2: reasoning, comprehension, basic maths"),
                    ("Intermediate", "Complete optional subject selection and start its preparation"),
                    ("Intermediate", "Attempt previous 10 years' UPSC Prelims papers under timed conditions"),
                    ("Advanced", "Join a reputed test series for Prelims (start 4 months before exam)"),
                    ("Advanced", "Practice Mains answer writing daily — structure, content, presentation"),
                    ("Advanced", "Prepare for Interview: current affairs, home state, graduation subject, hobbies"),
                    ("Advanced", "Build mental resilience — multiple attempts are normal; track & revise weak areas"),
                ],
                "quiz": [
                    {"q": "Which exam selects IAS, IPS, and IFS officers?", "opts": ["SSC CGL", "UPSC CSE", "State PSC", "IBPS PO"], "ans": 1},
                    {"q": "How many stages are there in the UPSC Civil Services Exam?", "opts": ["1", "2", "3", "4"], "ans": 2},
                    {"q": "CSAT stands for?", "opts": ["Civil Services Aptitude Test", "Central Services Admission Test", "Common Services Analysis Test", "None of these"], "ans": 0},
                    {"q": "Which NCERT subject is most critical for UPSC History?", "opts": ["Class 11–12 Physics", "Class 6–12 History", "Class 9 Maths", "Class 8 Science"], "ans": 1},
                    {"q": "What is the minimum age to appear in UPSC CSE?", "opts": ["18", "21", "25", "27"], "ans": 1},
                    {"q": "Which stage of UPSC tests answer writing?", "opts": ["Prelims", "Mains", "Interview", "Medical Test"], "ans": 1},
                    {"q": "The Interview stage in UPSC is also called?", "opts": ["Group Discussion", "Personality Test", "CSAT", "Viva Voce Exam"], "ans": 1},
                    {"q": "How many General Studies papers are there in UPSC Mains?", "opts": ["2", "3", "4", "5"], "ans": 2},
                ],
            }

        elif any(k in cn for k in ["Data", "Analyst", "Analytics", "Data Science", "Machine Learning", "AI"]):
            return {
                "videos": [
                    ("Data Analyst Roadmap 2024 — Complete Guide", "https://www.youtube.com/results?search_query=data+analyst+roadmap+complete+guide+2024"),
                    ("Python for Data Science — Full Course", "https://www.youtube.com/results?search_query=python+for+data+science+full+course+beginners"),
                    ("SQL for Data Analysts — Crash Course", "https://www.youtube.com/results?search_query=SQL+for+data+analysts+crash+course"),
                    ("Power BI / Tableau for Beginners", "https://www.youtube.com/results?search_query=power+BI+tableau+beginners+tutorial"),
                    ("Day in the Life of a Data Analyst", "https://www.youtube.com/results?search_query=day+in+life+data+analyst+vlog"),
                    ("Machine Learning Explained Simply", "https://www.youtube.com/results?search_query=machine+learning+explained+simply+beginners"),
                ],
                "links": {
                    "Free Courses": [
                        ("Google Data Analytics Certificate (Coursera)", "https://www.coursera.org/professional-certificates/google-data-analytics"),
                        ("Kaggle Learn — Free Mini-Courses", "https://www.kaggle.com/learn"),
                        ("freeCodeCamp — Data Analysis with Python", "https://www.freecodecamp.org/learn/data-analysis-with-python/"),
                        ("IBM Data Science (Coursera)", "https://www.coursera.org/professional-certificates/ibm-data-science"),
                    ],
                    "Practice Platforms": [
                        ("Kaggle — Datasets & Competitions", "https://www.kaggle.com/"),
                        ("HackerRank — SQL Practice", "https://www.hackerrank.com/domains/sql"),
                        ("StrataScratch — Real Interview Questions", "https://www.stratascratch.com/"),
                        ("Mode Analytics SQL Tutorial", "https://mode.com/sql-tutorial/"),
                    ],
                    "Tools & References": [
                        ("W3Schools SQL Tutorial", "https://www.w3schools.com/sql/"),
                        ("pandas Documentation", "https://pandas.pydata.org/docs/"),
                        ("Matplotlib Cheat Sheet", "https://matplotlib.org/cheatsheets/"),
                        ("Towards Data Science (articles)", "https://towardsdatascience.com/"),
                    ],
                    "Community": [
                        ("r/datascience — Reddit", "https://www.reddit.com/r/datascience/"),
                        ("DataTalks.Club — Free Courses & Community", "https://datatalks.club/"),
                        ("LinkedIn Data Analytics Groups", "https://www.linkedin.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Learn Excel / Google Sheets — pivot tables, VLOOKUP, basic charts"),
                    ("Beginner", "Learn SQL — SELECT, WHERE, JOIN, GROUP BY, subqueries"),
                    ("Beginner", "Learn Python basics — variables, loops, functions, lists, dicts"),
                    ("Intermediate", "Master pandas and NumPy for data cleaning and manipulation"),
                    ("Intermediate", "Learn data visualisation — Matplotlib, Seaborn, or Power BI / Tableau"),
                    ("Intermediate", "Understand statistics — mean, median, distributions, hypothesis testing"),
                    ("Intermediate", "Complete one end-to-end project on Kaggle (EDA + visualisation + insights)"),
                    ("Advanced", "Learn machine learning basics — scikit-learn, regression, classification"),
                    ("Advanced", "Build a portfolio with 3 projects covering different domains (finance, health, etc.)"),
                    ("Advanced", "Learn Git/GitHub for version control and collaboration"),
                    ("Advanced", "Practice SQL interview questions on StrataScratch or HackerRank"),
                    ("Job Ready", "Apply for internships or junior analyst roles; tailor resume with project metrics"),
                ],
                "quiz": [
                    {"q": "Which Python library is used for data manipulation?", "opts": ["NumPy", "pandas", "Matplotlib", "Flask"], "ans": 1},
                    {"q": "What does SQL GROUP BY do?", "opts": ["Sorts data", "Filters rows", "Aggregates rows by a column", "Joins tables"], "ans": 2},
                    {"q": "Which chart type best shows trends over time?", "opts": ["Pie chart", "Bar chart", "Line chart", "Scatter plot"], "ans": 2},
                    {"q": "What is a DataFrame?", "opts": ["A database table", "A 2D labelled data structure in pandas", "A type of chart", "A machine learning model"], "ans": 1},
                    {"q": "What does EDA stand for?", "opts": ["Exploratory Data Analysis", "Estimated Data Accuracy", "External Data API", "Extended Data Aggregation"], "ans": 0},
                    {"q": "Which of these is a data visualisation tool?", "opts": ["Docker", "Tableau", "Git", "Flask"], "ans": 1},
                    {"q": "A correlation of -1 means?", "opts": ["No relationship", "Perfect positive relationship", "Perfect negative relationship", "Weak relationship"], "ans": 2},
                    {"q": "Which platform hosts data science competitions?", "opts": ["LeetCode", "Kaggle", "HackerRank", "GitHub"], "ans": 1},
                ],
            }

        elif any(k in cn for k in ["Software", "Developer", "Engineer", "Programmer", "Coding", "Web"]):
            return {
                "videos": [
                    ("Software Developer Roadmap 2024 — What to Learn", "https://www.youtube.com/results?search_query=software+developer+roadmap+2024+what+to+learn"),
                    ("Web Development Full Course for Beginners", "https://www.youtube.com/results?search_query=web+development+full+course+beginners+HTML+CSS+JavaScript"),
                    ("Data Structures & Algorithms in 1 Hour", "https://www.youtube.com/results?search_query=data+structures+algorithms+crash+course+1+hour"),
                    ("Git & GitHub Crash Course", "https://www.youtube.com/results?search_query=git+github+crash+course+beginners"),
                    ("Day in the Life of a Software Engineer", "https://www.youtube.com/results?search_query=day+in+life+software+engineer+vlog"),
                    ("System Design Interview Basics Explained", "https://www.youtube.com/results?search_query=system+design+interview+basics+explained"),
                ],
                "links": {
                    "Free Courses": [
                        ("freeCodeCamp — Full Stack Curriculum", "https://www.freecodecamp.org/"),
                        ("The Odin Project — Web Dev Path", "https://www.theodinproject.com/"),
                        ("CS50 by Harvard (free on edX)", "https://www.edx.org/learn/computer-science/harvard-university-cs50-s-introduction-to-computer-science"),
                        ("MIT OpenCourseWare — Programming", "https://ocw.mit.edu/courses/6-0001-introduction-to-computer-science-and-programming-in-python-fall-2016/"),
                    ],
                    "Practice & Interview Prep": [
                        ("LeetCode — Coding Problems", "https://leetcode.com/"),
                        ("HackerRank — Programming Challenges", "https://www.hackerrank.com/"),
                        ("GeeksforGeeks — DSA Articles", "https://www.geeksforgeeks.org/"),
                        ("Codeforces — Competitive Programming", "https://codeforces.com/"),
                    ],
                    "Tools & References": [
                        ("MDN Web Docs", "https://developer.mozilla.org/"),
                        ("GitHub — Version Control & Open Source", "https://github.com/"),
                        ("Stack Overflow — Q&A", "https://stackoverflow.com/"),
                        ("DevDocs — API Documentation", "https://devdocs.io/"),
                    ],
                    "Build & Deploy": [
                        ("Vercel — Free Hosting for Web Apps", "https://vercel.com/"),
                        ("Netlify — Deploy Static Sites", "https://www.netlify.com/"),
                        ("Replit — Code in Browser", "https://replit.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Pick a language: Python (recommended for beginners) or JavaScript for web"),
                    ("Beginner", "Learn fundamentals: variables, loops, functions, arrays, objects"),
                    ("Beginner", "Understand how the web works: HTML, CSS, HTTP basics"),
                    ("Intermediate", "Learn data structures: arrays, linked lists, stacks, queues, trees, hashmaps"),
                    ("Intermediate", "Study algorithms: sorting, searching, recursion, time complexity (Big O)"),
                    ("Intermediate", "Build 3 small projects: to-do app, weather app, simple CRUD app"),
                    ("Intermediate", "Learn Git & GitHub — commits, branches, pull requests"),
                    ("Advanced", "Choose a specialisation: frontend, backend, mobile, AI/ML, DevOps"),
                    ("Advanced", "Learn a framework: React / Vue (frontend) or Django / Node.js (backend)"),
                    ("Advanced", "Understand databases: SQL (PostgreSQL / MySQL) and NoSQL (MongoDB)"),
                    ("Advanced", "Contribute to open-source projects on GitHub"),
                    ("Job Ready", "Solve 100+ LeetCode problems (Easy + Medium); practice system design"),
                ],
                "quiz": [
                    {"q": "What does HTML stand for?", "opts": ["Hyper Text Markup Language", "High Text Machine Language", "Hyper Transfer Markup Logic", "None of these"], "ans": 0},
                    {"q": "Which data structure uses LIFO?", "opts": ["Queue", "Stack", "Array", "Tree"], "ans": 1},
                    {"q": "What is Git used for?", "opts": ["Styling web pages", "Version control", "Database management", "Server hosting"], "ans": 1},
                    {"q": "What does API stand for?", "opts": ["Application Programming Interface", "Applied Program Instruction", "Automated Process Integration", "Application Protocol Index"], "ans": 0},
                    {"q": "Which language is primarily used for web styling?", "opts": ["Python", "Java", "CSS", "SQL"], "ans": 2},
                    {"q": "What is the time complexity of binary search?", "opts": ["O(n)", "O(n²)", "O(log n)", "O(1)"], "ans": 2},
                    {"q": "What does OOP stand for?", "opts": ["Object Oriented Programming", "Open Output Protocol", "Online Operation Process", "Ordered Object Pipeline"], "ans": 0},
                    {"q": "Which of these is a JavaScript framework?", "opts": ["Django", "Laravel", "React", "Flask"], "ans": 2},
                ],
            }

        elif any(k in cn for k in ["Design", "Creative", "Art", "UX", "UI", "Graphic", "Animation"]):
            return {
                "videos": [
                    ("UI/UX Design Full Course for Beginners", "https://www.youtube.com/results?search_query=UI+UX+design+full+course+beginners+2024"),
                    ("Figma Complete Tutorial — Zero to Hero", "https://www.youtube.com/results?search_query=figma+complete+tutorial+zero+to+hero"),
                    ("Graphic Design Fundamentals — Colour, Typography, Layout", "https://www.youtube.com/results?search_query=graphic+design+fundamentals+colour+typography+layout"),
                    ("How to Build a Design Portfolio", "https://www.youtube.com/results?search_query=how+to+build+design+portfolio+2024"),
                    ("Day in the Life of a UX Designer", "https://www.youtube.com/results?search_query=day+in+life+UX+designer+vlog"),
                    ("Design Thinking — User Research & Prototyping", "https://www.youtube.com/results?search_query=design+thinking+user+research+prototyping+explained"),
                ],
                "links": {
                    "Free Courses": [
                        ("Google UX Design Certificate (Coursera)", "https://www.coursera.org/professional-certificates/google-ux-design"),
                        ("Canva Design School — Free Tutorials", "https://www.canva.com/learn/"),
                        ("Interaction Design Foundation (IDF)", "https://www.interaction-design.org/"),
                        ("Figma Learning Resources", "https://www.figma.com/resources/learn-design/"),
                    ],
                    "Tools (Free to Start)": [
                        ("Figma — UI/UX Prototyping", "https://www.figma.com/"),
                        ("Canva — Quick Graphic Design", "https://www.canva.com/"),
                        ("Adobe Express (free tier)", "https://www.adobe.com/express/"),
                        ("Coolors — Colour Palette Generator", "https://coolors.co/"),
                    ],
                    "Portfolio & Inspiration": [
                        ("Behance — Design Portfolios", "https://www.behance.net/"),
                        ("Dribbble — Designer Showcase", "https://dribbble.com/"),
                        ("Awwwards — Award-winning Web Design", "https://www.awwwards.com/"),
                        ("Pinterest — Design Mood Boards", "https://www.pinterest.com/"),
                    ],
                    "Freelance & Jobs": [
                        ("Fiverr — Start Freelancing", "https://www.fiverr.com/"),
                        ("Upwork — Design Projects", "https://www.upwork.com/"),
                        ("99designs — Design Competitions", "https://99designs.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Learn the 4 core design principles: Contrast, Alignment, Repetition, Proximity (CARP)"),
                    ("Beginner", "Understand colour theory: hues, saturation, complementary colours, colour psychology"),
                    ("Beginner", "Learn typography: font pairing, hierarchy, readability, spacing"),
                    ("Beginner", "Get comfortable with Canva — recreate existing designs to build muscle memory"),
                    ("Intermediate", "Learn Figma — frames, components, auto-layout, prototyping, design systems"),
                    ("Intermediate", "Study UX fundamentals: user research, personas, user journeys, wireframing"),
                    ("Intermediate", "Complete a case study end-to-end: problem → research → wireframe → prototype → test"),
                    ("Advanced", "Build a portfolio with 3–5 detailed case studies (show process, not just final output)"),
                    ("Advanced", "Learn motion design basics (After Effects or Rive) as a differentiator"),
                    ("Advanced", "Study accessibility: WCAG guidelines, colour contrast, screen reader basics"),
                    ("Job Ready", "Freelance on Fiverr or 99designs to get real-world briefs and feedback"),
                    ("Job Ready", "Network on LinkedIn, attend design meetups, apply for junior designer / internship roles"),
                ],
                "quiz": [
                    {"q": "What does UX stand for?", "opts": ["User Experience", "User Execution", "Unified Experience", "Universal Exchange"], "ans": 0},
                    {"q": "Which colour model is used for digital screens?", "opts": ["CMYK", "RGB", "HSL", "Pantone"], "ans": 1},
                    {"q": "What is a wireframe?", "opts": ["A finished design mockup", "A basic layout blueprint", "A colour palette", "An animation file"], "ans": 1},
                    {"q": "What tool is most widely used for UI/UX prototyping?", "opts": ["Photoshop", "Figma", "Excel", "After Effects"], "ans": 1},
                    {"q": "What does CARP stand for in design?", "opts": ["Contrast, Alignment, Repetition, Proximity", "Colour, Art, Rendering, Print", "Creative, Aesthetic, Ratio, Pattern", "None of these"], "ans": 0},
                    {"q": "In UX, what is a 'persona'?", "opts": ["A brand logo", "A fictional user profile based on research", "A product prototype", "A design system"], "ans": 1},
                    {"q": "What is kerning?", "opts": ["Adjusting space between letters", "Choosing font size", "Picking a colour scheme", "Creating animation"], "ans": 0},
                    {"q": "What is a design system?", "opts": ["A software tool", "A collection of reusable components and guidelines", "A type of animation", "A client brief"], "ans": 1},
                ],
            }

        elif any(k in cn for k in ["Doctor", "Medical", "Health", "Nurse", "Pharmacy", "MBBS", "Surgeon"]):
            return {
                "videos": [
                    ("NEET 2024 — Complete Strategy & Study Plan", "https://www.youtube.com/results?search_query=NEET+2024+complete+strategy+study+plan"),
                    ("Human Anatomy & Physiology — Full Crash Course", "https://www.youtube.com/results?search_query=human+anatomy+physiology+full+crash+course"),
                    ("Day in the Life of a Medical Student in India", "https://www.youtube.com/results?search_query=day+in+life+MBBS+medical+student+India+vlog"),
                    ("Biology for NEET — Cell Biology & Genetics", "https://www.youtube.com/results?search_query=biology+for+NEET+cell+biology+genetics"),
                    ("Medical Specialisations Explained — Which to Choose?", "https://www.youtube.com/results?search_query=medical+specialisations+explained+which+to+choose+India"),
                    ("How to Become a Doctor in India — Complete Roadmap", "https://www.youtube.com/results?search_query=how+to+become+doctor+India+complete+roadmap+MBBS"),
                ],
                "links": {
                    "Official & Exam": [
                        ("NMC India — National Medical Commission", "https://www.nmc.org.in/"),
                        ("NTA NEET Official Site", "https://neet.nta.nic.in/"),
                        ("MCC — Medical Counselling Committee", "https://mcc.nic.in/"),
                    ],
                    "Free Study Resources": [
                        ("Khan Academy — Health & Medicine", "https://www.khanacademy.org/science/health-and-medicine"),
                        ("NCERT Biology Class 11 & 12 (free PDFs)", "https://ncert.nic.in/textbook.php"),
                        ("Aakash NEET Prep", "https://www.aakash.ac.in/neet"),
                        ("Allen NEET Free Resources", "https://www.allen.ac.in/neet/"),
                    ],
                    "Practice & Mock Tests": [
                        ("Embibe NEET Practice", "https://www.embibe.com/exams/neet/"),
                        ("Testbook NEET Mock Tests", "https://testbook.com/neet"),
                        ("MedlinePlus — Medical Reference", "https://medlineplus.gov/"),
                    ],
                    "Career Exploration": [
                        ("Doximity — Medical Professional Network", "https://www.doximity.com/"),
                        ("Medscape — Medical News & Education", "https://www.medscape.com/"),
                        ("IndiaMedical Jobs — Career Listings", "https://www.naukri.com/medical-jobs"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Build a strong foundation in Biology, Physics, and Chemistry (Class 11–12 NCERT)"),
                    ("Beginner", "Understand what NEET is and its eligibility, syllabus, and pattern"),
                    ("Beginner", "Read NCERT Biology Class 11 & 12 cover-to-cover — it is the NEET Bible"),
                    ("Intermediate", "Practice MCQs from past NEET papers (last 10 years)"),
                    ("Intermediate", "Join a coaching programme or structured online course for NEET"),
                    ("Intermediate", "Focus weak areas: Genetics, Ecology, Organic Chemistry, Optics"),
                    ("Intermediate", "Attempt full mock tests weekly; analyse mistakes carefully"),
                    ("Advanced", "Research MBBS colleges — government vs private, fees, ranking, location"),
                    ("Advanced", "Explore medical specialisations: Surgery, Paediatrics, Psychiatry, Radiology, etc."),
                    ("Advanced", "Shadow a doctor or volunteer at a health camp to understand clinical realities"),
                    ("Advanced", "Develop soft skills: empathy, communication, patience — critical for patient care"),
                    ("Job Ready", "Clear NEET → MBBS → Internship → PG (NEET-PG) or USMLE for abroad"),
                ],
                "quiz": [
                    {"q": "Which exam is the gateway to MBBS in India?", "opts": ["JEE", "NEET", "GATE", "CAT"], "ans": 1},
                    {"q": "What is the largest organ in the human body?", "opts": ["Liver", "Heart", "Skin", "Lung"], "ans": 2},
                    {"q": "What does ECG measure?", "opts": ["Brain activity", "Heart electrical activity", "Blood pressure", "Oxygen levels"], "ans": 1},
                    {"q": "Which blood type is the universal donor?", "opts": ["AB+", "O+", "O-", "A-"], "ans": 2},
                    {"q": "The basic unit of life is?", "opts": ["Tissue", "Organ", "Cell", "Atom"], "ans": 2},
                    {"q": "Which body system fights infections?", "opts": ["Nervous system", "Immune system", "Digestive system", "Skeletal system"], "ans": 1},
                    {"q": "MBBS full form?", "opts": ["Master of Biology and Body Science", "Bachelor of Medicine & Bachelor of Surgery", "Medical Board Basis Study", "None of these"], "ans": 1},
                    {"q": "Which organ produces insulin?", "opts": ["Liver", "Kidney", "Pancreas", "Thyroid"], "ans": 2},
                ],
            }

        elif any(k in cn for k in ["Finance", "Commerce", "Accountant", "CA", "Banking", "Investment", "CFA", "Stock"]):
            return {
                "videos": [
                    ("CA Foundation — Complete Roadmap for Beginners", "https://www.youtube.com/results?search_query=CA+foundation+complete+roadmap+beginners+India"),
                    ("Stock Market Basics for Beginners in India", "https://www.youtube.com/results?search_query=stock+market+basics+beginners+India+2024"),
                    ("Financial Modelling Full Course", "https://www.youtube.com/results?search_query=financial+modelling+full+course+beginners"),
                    ("Day in the Life of a CA / Chartered Accountant", "https://www.youtube.com/results?search_query=day+in+life+chartered+accountant+CA+India"),
                    ("Investment Banking Explained Simply", "https://www.youtube.com/results?search_query=investment+banking+explained+simply+India"),
                    ("Personal Finance & Budgeting — Master the Basics", "https://www.youtube.com/results?search_query=personal+finance+budgeting+basics+India"),
                ],
                "links": {
                    "Official & Certifications": [
                        ("ICAI — Institute of Chartered Accountants of India", "https://www.icai.org/"),
                        ("SEBI — Securities & Exchange Board of India", "https://www.sebi.gov.in/"),
                        ("NSE India — Stock Exchange", "https://www.nseindia.com/"),
                        ("NISM — National Institute of Securities Markets", "https://www.nism.ac.in/"),
                    ],
                    "Free Courses": [
                        ("Zerodha Varsity — Free Stock Market Course", "https://zerodha.com/varsity/"),
                        ("Coursera — Finance & Accounting Courses", "https://www.coursera.org/browse/business/finance"),
                        ("CFI — Corporate Finance Institute (free courses)", "https://corporatefinanceinstitute.com/free-courses/"),
                        ("Investopedia — Finance Academy", "https://www.investopedia.com/financial-term-dictionary-4769738"),
                    ],
                    "Practice & Tools": [
                        ("Moneybhai — Virtual Stock Market Game", "https://www.moneybhai.moneycontrol.com/"),
                        ("Excel for Finance — Templates & Tutorials", "https://www.youtube.com/results?search_query=excel+for+finance+financial+modelling+tutorial"),
                        ("Screener.in — Stock Fundamental Analysis", "https://www.screener.in/"),
                    ],
                    "News & Research": [
                        ("Moneycontrol — Markets & Economy", "https://www.moneycontrol.com/"),
                        ("Economic Times — Finance Section", "https://economictimes.indiatimes.com/markets"),
                        ("Bloomberg — Global Finance News", "https://www.bloomberg.com/markets"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Learn accounting basics: assets, liabilities, income statement, balance sheet"),
                    ("Beginner", "Understand personal finance: budgeting, savings, compound interest, inflation"),
                    ("Beginner", "Study Commerce Class 11–12: Accountancy, Business Studies, Economics"),
                    ("Intermediate", "Choose a path: CA / CMA / MBA Finance / CFA / Stock Market / Banking"),
                    ("Intermediate", "For CA: clear Foundation → Intermediate → Final with ICAI articleship"),
                    ("Intermediate", "Learn Excel for finance: VLOOKUP, pivot tables, financial formulas"),
                    ("Intermediate", "Complete Zerodha Varsity to understand equity, mutual funds, derivatives"),
                    ("Advanced", "Learn financial modelling: DCF, comparable company analysis, LBO"),
                    ("Advanced", "Practice ratio analysis on real company balance sheets from NSE/BSE"),
                    ("Advanced", "Prepare for banking exams (IBPS PO / SBI PO) if targeting public sector"),
                    ("Job Ready", "Intern at a CA firm, brokerage, or finance startup for hands-on experience"),
                    ("Job Ready", "Build a stock/investment analysis portfolio on Screener.in or a blog"),
                ],
                "quiz": [
                    {"q": "What does CA stand for?", "opts": ["Certified Analyst", "Chartered Accountant", "Chief Administrator", "Corporate Advisor"], "ans": 1},
                    {"q": "Which body regulates the Indian stock market?", "opts": ["RBI", "SEBI", "IRDA", "ICAI"], "ans": 1},
                    {"q": "What is a balance sheet?", "opts": ["A profit statement", "A record of assets and liabilities", "A budget plan", "A tax document"], "ans": 1},
                    {"q": "What does P/E ratio stand for?", "opts": ["Profit/Equity", "Price/Earnings", "Performance/Evaluation", "Public/Enterprise"], "ans": 1},
                    {"q": "Which bank is India's central bank?", "opts": ["SBI", "HDFC", "RBI", "ICICI"], "ans": 2},
                    {"q": "What is a mutual fund?", "opts": ["A government loan scheme", "A pooled investment vehicle", "A type of insurance", "A bank account"], "ans": 1},
                    {"q": "What does GDP stand for?", "opts": ["Gross Domestic Product", "General Development Plan", "Government Debt Position", "Global Distribution Protocol"], "ans": 0},
                    {"q": "What is compound interest?", "opts": ["Interest on principal only", "Interest earned on principal and accumulated interest", "A fixed government rate", "None of these"], "ans": 1},
                ],
            }

        elif any(k in cn for k in ["Law", "Legal", "Lawyer", "Advocate", "Judge", "LLB", "Attorney"]):
            return {
                "videos": [
                    ("How to Become a Lawyer in India — Complete Guide", "https://www.youtube.com/results?search_query=how+to+become+lawyer+India+LLB+complete+guide"),
                    ("CLAT Preparation Strategy — Law Entrance Exam", "https://www.youtube.com/results?search_query=CLAT+preparation+strategy+law+entrance+exam+India"),
                    ("Day in the Life of a Lawyer in India", "https://www.youtube.com/results?search_query=day+in+life+lawyer+advocate+India+vlog"),
                    ("Indian Constitution Explained Simply", "https://www.youtube.com/results?search_query=Indian+constitution+explained+simply"),
                    ("Corporate Law vs Criminal Law — Which to Choose?", "https://www.youtube.com/results?search_query=corporate+law+vs+criminal+law+career+India"),
                    ("Legal Research & Writing for Beginners", "https://www.youtube.com/results?search_query=legal+research+writing+skills+beginners"),
                ],
                "links": {
                    "Official & Exam": [
                        ("Bar Council of India", "https://www.barcouncilofindia.org/"),
                        ("CLAT Official Website", "https://consortiumofnlus.ac.in/clat-2025/"),
                        ("Supreme Court of India", "https://main.sci.gov.in/"),
                        ("India Code — Laws & Acts", "https://www.indiacode.nic.in/"),
                    ],
                    "Free Study Resources": [
                        ("Legal Services India — Free Articles", "https://www.legalservicesindia.com/"),
                        ("iPleaders Blog — Law Notes", "https://blog.ipleaders.in/"),
                        ("SCC Online — Case Laws (limited free)", "https://www.scconline.com/"),
                        ("Manupatra — Legal Database", "https://www.manupatra.com/"),
                    ],
                    "Practice & Competitions": [
                        ("Moot Court Resources — Lawctopus", "https://www.lawctopus.com/"),
                        ("Lawsikho — Practical Legal Courses", "https://lawsikho.com/"),
                        ("CLATapult — CLAT Mock Tests", "https://clatapult.com/"),
                    ],
                    "Career & Community": [
                        ("Lawctopus — Law School Community", "https://www.lawctopus.com/"),
                        ("LinkedIn — Legal Professionals", "https://www.linkedin.com/"),
                        ("Bar & Bench — Legal News", "https://www.barandbench.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Understand the legal system: judiciary structure, types of courts, branches of law"),
                    ("Beginner", "Read the Indian Constitution basics: Fundamental Rights, DPSPs, Parliament"),
                    ("Beginner", "Prepare for CLAT (Common Law Admission Test) — the gateway to NLUs"),
                    ("Intermediate", "Complete LLB (5-year integrated or 3-year after graduation)"),
                    ("Intermediate", "Choose a specialisation: Criminal, Civil, Corporate, Constitutional, IP, Family Law"),
                    ("Intermediate", "Participate in moot court competitions — builds advocacy skills"),
                    ("Intermediate", "Learn legal research: case laws, statutes, SCC Online, Manupatra"),
                    ("Advanced", "Do internships at law firms, courts, NGOs, or corporate legal teams"),
                    ("Advanced", "Learn legal drafting: petitions, contracts, notices, pleadings"),
                    ("Advanced", "Clear the Bar Council exam (AIBE) to practice as an advocate"),
                    ("Job Ready", "Enroll as an advocate, join a law firm, or prepare for judiciary exams"),
                    ("Job Ready", "For judiciary: clear State Judicial Services Exam after 3 years of practice"),
                ],
                "quiz": [
                    {"q": "CLAT is the entrance exam for?", "opts": ["Medical colleges", "Engineering colleges", "National Law Universities", "Management schools"], "ans": 2},
                    {"q": "How many Fundamental Rights are in the Indian Constitution?", "opts": ["5", "6", "7", "8"], "ans": 1},
                    {"q": "Who is the highest judicial authority in India?", "opts": ["High Court", "Supreme Court", "District Court", "Lok Adalat"], "ans": 1},
                    {"q": "What does LLB stand for?", "opts": ["Law and Legal Business", "Legum Baccalaureus (Bachelor of Laws)", "Legal License Board", "Lower Level Bar"], "ans": 1},
                    {"q": "Which right allows a person to move court if rights are violated?", "opts": ["Right to Equality", "Right to Freedom", "Right to Constitutional Remedies", "Right against Exploitation"], "ans": 2},
                    {"q": "What is a 'moot court'?", "opts": ["A real trial court", "A simulated courtroom exercise for law students", "A lower court", "An arbitration tribunal"], "ans": 1},
                    {"q": "AIBE stands for?", "opts": ["All India Bar Examination", "Advanced Indian Business Exam", "Advocates India Board Entry", "None of these"], "ans": 0},
                    {"q": "The Preamble of the Indian Constitution begins with?", "opts": ["We the Government", "We the People", "We the Citizens", "In the Name of Democracy"], "ans": 1},
                ],
            }

        elif any(k in cn for k in ["Teacher", "Teaching", "Education", "Professor", "Lecturer", "Tutor"]):
            return {
                "videos": [
                    ("How to Become a Teacher in India — B.Ed & More", "https://www.youtube.com/results?search_query=how+to+become+teacher+India+BEd+complete+guide"),
                    ("Effective Teaching Techniques & Classroom Management", "https://www.youtube.com/results?search_query=effective+teaching+techniques+classroom+management"),
                    ("Day in the Life of a School Teacher in India", "https://www.youtube.com/results?search_query=day+in+life+school+teacher+India+vlog"),
                    ("CTET Preparation — Complete Strategy", "https://www.youtube.com/results?search_query=CTET+preparation+complete+strategy+tips"),
                    ("EdTech & Online Teaching — How to Start", "https://www.youtube.com/results?search_query=edtech+online+teaching+how+to+start+India"),
                    ("Bloom's Taxonomy Explained — Teaching & Learning", "https://www.youtube.com/results?search_query=blooms+taxonomy+explained+teaching+learning"),
                ],
                "links": {
                    "Official & Certifications": [
                        ("NCTE — National Council for Teacher Education", "https://ncte.gov.in/"),
                        ("CTET Official Website", "https://ctet.nic.in/"),
                        ("UGC NET Official Website", "https://ugcnet.nta.nic.in/"),
                        ("DIKSHA — National Digital Infrastructure for Teachers", "https://diksha.gov.in/"),
                    ],
                    "Free Courses & Resources": [
                        ("Coursera — Education & Teaching", "https://www.coursera.org/browse/education"),
                        ("SWAYAM — Free Indian Online Courses", "https://swayam.gov.in/"),
                        ("Khan Academy — Teaching Resources", "https://www.khanacademy.org/teacher"),
                        ("TED-Ed — Educational Videos", "https://ed.ted.com/"),
                    ],
                    "EdTech Platforms": [
                        ("Unacademy — Become an Educator", "https://unacademy.com/become-an-educator"),
                        ("Vedantu — Online Teaching Jobs", "https://www.vedantu.com/teach"),
                        ("Byju's — Content & Teaching Roles", "https://byjus.com/"),
                    ],
                    "Community & Growth": [
                        ("Teachers of India — Community", "https://www.teachersofindia.org/"),
                        ("Edutopia — Teaching Best Practices", "https://www.edutopia.org/"),
                        ("LinkedIn — Education Professionals", "https://www.linkedin.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Complete Class 12 with strong academics in your preferred subject"),
                    ("Beginner", "Pursue a relevant Bachelor's degree (B.Sc, B.A, B.Com) in your teaching subject"),
                    ("Intermediate", "Complete B.Ed (Bachelor of Education) — mandatory for school teaching in India"),
                    ("Intermediate", "Clear CTET or State TET to be eligible for government school jobs"),
                    ("Intermediate", "Develop classroom skills: lesson planning, student engagement, assessment design"),
                    ("Intermediate", "Learn Bloom's Taxonomy and other pedagogical frameworks"),
                    ("Advanced", "For college teaching: pursue M.A / M.Sc + clear UGC NET / SET"),
                    ("Advanced", "Build digital literacy: Google Classroom, Canva, presentation design, video lectures"),
                    ("Advanced", "Explore EdTech: teach on Unacademy, Vedantu, or your own YouTube channel"),
                    ("Advanced", "Pursue a PhD for university professorship or research roles"),
                    ("Job Ready", "Apply for government teaching posts (KVS, NVS, State Boards) or private schools"),
                    ("Job Ready", "Build a portfolio: sample lesson plans, student outcomes, curriculum projects"),
                ],
                "quiz": [
                    {"q": "Which exam qualifies a teacher for central government schools?", "opts": ["UPSC", "CTET", "GATE", "NET"], "ans": 1},
                    {"q": "B.Ed stands for?", "opts": ["Bachelor of Editing", "Bachelor of Education", "Board of Examination Department", "Basic Education Degree"], "ans": 1},
                    {"q": "Who regulates teacher education in India?", "opts": ["UGC", "NCERT", "NCTE", "CBSE"], "ans": 2},
                    {"q": "Bloom's Taxonomy is related to?", "opts": ["Medical diagnosis", "Levels of learning objectives", "Financial planning", "Legal frameworks"], "ans": 1},
                    {"q": "UGC NET qualifies a candidate for?", "opts": ["School teaching", "College lectureship & JRF", "Medical practice", "Engineering jobs"], "ans": 1},
                    {"q": "What is a 'lesson plan'?", "opts": ["A school timetable", "A detailed guide for teaching a topic", "A student report card", "A textbook chapter"], "ans": 1},
                    {"q": "DIKSHA platform is maintained by?", "opts": ["Private EdTech companies", "Ministry of Education, India", "World Bank", "UNESCO"], "ans": 1},
                    {"q": "Which teaching method involves students discovering answers themselves?", "opts": ["Lecture method", "Inquiry-based learning", "Rote memorisation", "Dictation"], "ans": 1},
                ],
            }

        elif any(k in cn for k in ["Marketing", "Brand", "Advertising", "Digital Marketing", "PR", "Sales"]):
            return {
                "videos": [
                    ("Digital Marketing Full Course for Beginners 2024", "https://www.youtube.com/results?search_query=digital+marketing+full+course+beginners+2024"),
                    ("How to Build a Brand from Scratch", "https://www.youtube.com/results?search_query=how+to+build+a+brand+from+scratch"),
                    ("Social Media Marketing Strategy — Complete Guide", "https://www.youtube.com/results?search_query=social+media+marketing+strategy+complete+guide"),
                    ("Google Ads & SEO for Beginners", "https://www.youtube.com/results?search_query=Google+Ads+SEO+beginners+tutorial"),
                    ("Day in the Life of a Digital Marketer", "https://www.youtube.com/results?search_query=day+in+life+digital+marketer+vlog"),
                    ("Content Marketing & Copywriting Masterclass", "https://www.youtube.com/results?search_query=content+marketing+copywriting+masterclass"),
                ],
                "links": {
                    "Free Courses & Certifications": [
                        ("Google Digital Garage — Free Certification", "https://learndigital.withgoogle.com/digitalgarage/"),
                        ("HubSpot Academy — Free Marketing Courses", "https://academy.hubspot.com/"),
                        ("Meta Blueprint — Social Media Marketing", "https://www.facebook.com/business/learn"),
                        ("Semrush Academy — SEO & SEM Courses", "https://www.semrush.com/academy/"),
                    ],
                    "Tools (Free to Start)": [
                        ("Google Analytics (GA4)", "https://analytics.google.com/"),
                        ("Canva — Social Media Design", "https://www.canva.com/"),
                        ("Mailchimp — Email Marketing (free tier)", "https://mailchimp.com/"),
                        ("Buffer — Social Media Scheduling", "https://buffer.com/"),
                    ],
                    "Practice & Portfolio": [
                        ("Google Ads Keyword Planner", "https://ads.google.com/home/tools/keyword-planner/"),
                        ("Ubersuggest — Free SEO Tool", "https://neilpatel.com/ubersuggest/"),
                        ("Neil Patel's Blog — Marketing Strategies", "https://neilpatel.com/blog/"),
                    ],
                    "Community & Jobs": [
                        ("r/digital_marketing — Reddit", "https://www.reddit.com/r/digital_marketing/"),
                        ("Marketing Week", "https://www.marketingweek.com/"),
                        ("LinkedIn Marketing Community", "https://www.linkedin.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", "Learn marketing fundamentals: 4Ps (Product, Price, Place, Promotion)"),
                    ("Beginner", "Understand digital channels: SEO, SEM, Social Media, Email, Content"),
                    ("Beginner", "Complete Google Digital Garage free certification (globally recognised)"),
                    ("Intermediate", "Learn SEO basics: keyword research, on-page SEO, backlinks, Google Search Console"),
                    ("Intermediate", "Learn Google Ads and Meta Ads — run small campaigns with a ₹500–1000 budget"),
                    ("Intermediate", "Master content marketing: blogging, copywriting, video scripts, email campaigns"),
                    ("Intermediate", "Learn analytics: Google Analytics 4, tracking conversions, A/B testing"),
                    ("Advanced", "Build a personal brand on LinkedIn or Instagram to showcase expertise"),
                    ("Advanced", "Complete HubSpot or Semrush certifications to stand out"),
                    ("Advanced", "Work on real projects: manage social media for a local business or NGO"),
                    ("Job Ready", "Build a portfolio: case studies showing campaign results (metrics matter)"),
                    ("Job Ready", "Apply for digital marketing internships, content creator, or SEO analyst roles"),
                ],
                "quiz": [
                    {"q": "What does SEO stand for?", "opts": ["Social Engagement Optimisation", "Search Engine Optimisation", "Site Experience Operations", "Structured Email Output"], "ans": 1},
                    {"q": "Which of these is a paid advertising platform?", "opts": ["Google Organic Search", "Google Ads", "SEMrush Blog", "Wikipedia"], "ans": 1},
                    {"q": "What is a 'conversion' in digital marketing?", "opts": ["Changing currency", "When a user completes a desired action", "Switching ad platforms", "None of these"], "ans": 1},
                    {"q": "What does CTA stand for?", "opts": ["Click To Advertise", "Call To Action", "Content Tracking Analytics", "Campaign Traffic Analysis"], "ans": 1},
                    {"q": "What is a 'buyer persona'?", "opts": ["A legal identity document", "A fictional profile of your ideal customer", "A product sample", "A marketing budget"], "ans": 1},
                    {"q": "Which metric measures email open rates?", "opts": ["CTR", "CPC", "Open Rate", "Bounce Rate"], "ans": 2},
                    {"q": "What does A/B testing involve?", "opts": ["Testing two versions to see which performs better", "Testing product quality", "A/B grading system", "Two different websites"], "ans": 0},
                    {"q": "Which platform is best for B2B marketing?", "opts": ["TikTok", "Snapchat", "LinkedIn", "Pinterest"], "ans": 2},
                ],
            }

        else:
            import urllib.parse
            query = urllib.parse.quote_plus(cn or "career")
            return {
                "videos": [
                    (f"{cn or 'Career'} — Getting Started & Roadmap", f"https://www.youtube.com/results?search_query={query}+career+roadmap+how+to+get+started"),
                    (f"{cn or 'Career'} — Day in the Life", f"https://www.youtube.com/results?search_query={query}+day+in+life+vlog"),
                    (f"{cn or 'Career'} — Required Skills & Qualifications", f"https://www.youtube.com/results?search_query={query}+required+skills+qualifications+India"),
                    (f"{cn or 'Career'} — Interview Tips", f"https://www.youtube.com/results?search_query={query}+interview+tips+preparation"),
                ],
                "links": {
                    "Free Courses": [
                        ("Coursera — Browse All Free Courses", "https://www.coursera.org/"),
                        ("edX — University Courses Online", "https://www.edx.org/"),
                        ("SWAYAM — Free Indian Online Courses", "https://swayam.gov.in/"),
                        ("YouTube Learning", "https://www.youtube.com/learning"),
                    ],
                    "Career Tools": [
                        ("LinkedIn — Professional Networking", "https://www.linkedin.com/"),
                        ("Internshala — Internships & Courses", "https://internshala.com/"),
                        ("Naukri.com — Job Listings", "https://www.naukri.com/"),
                        ("Indeed India — Jobs", "https://www.indeed.co.in/"),
                    ],
                    "Skill Building": [
                        ("Skillshare — Creative & Professional Courses", "https://www.skillshare.com/"),
                        ("LinkedIn Learning — Skill Videos", "https://www.linkedin.com/learning/"),
                        ("Udemy — Affordable Courses", "https://www.udemy.com/"),
                    ],
                },
                "roadmap": [
                    ("Beginner", f"Research what a {cn or 'professional'} actually does day-to-day"),
                    ("Beginner", "List the top 5–7 skills and qualifications required for this career"),
                    ("Beginner", "Talk to 2–3 professionals in this field (LinkedIn outreach works well)"),
                    ("Intermediate", "Enroll in a relevant free course on Coursera, SWAYAM, or YouTube"),
                    ("Intermediate", "Complete a beginner project or case study to apply what you've learned"),
                    ("Intermediate", "Build a LinkedIn profile highlighting your learning and goals"),
                    ("Advanced", "Apply for an internship or part-time role in this field"),
                    ("Advanced", "Identify the top companies or organisations hiring for this career"),
                    ("Advanced", "Earn at least one industry-recognised certification"),
                    ("Advanced", "Build a portfolio: documents, projects, or work samples that prove your skills"),
                    ("Job Ready", "Network actively — attend events, join communities, connect with professionals"),
                    ("Job Ready", "Tailor your resume for each application; highlight measurable achievements"),
                ],
                "quiz": [
                    {"q": "What is the best way to learn a new professional skill?", "opts": ["Read theory only", "Practice consistently with real projects", "Watch once and move on", "Memorise notes"], "ans": 1},
                    {"q": "What does a portfolio showcase?", "opts": ["Your salary expectations", "Your past work and projects", "Your social media following", "Your hobbies"], "ans": 1},
                    {"q": "What is networking in a career context?", "opts": ["Computer networking", "Building professional relationships", "Social media follower count", "Cold emailing companies"], "ans": 1},
                    {"q": "What does ROI stand for?", "opts": ["Return On Investment", "Rate Of Inflation", "Revenue Over Income", "Risk Of Investment"], "ans": 0},
                    {"q": "Which platform is most useful for professional networking?", "opts": ["Instagram", "LinkedIn", "Twitter/X", "Facebook"], "ans": 1},
                    {"q": "What is an internship?", "opts": ["A full-time permanent job", "Short-term work experience at a company", "A freelance project", "A government scheme"], "ans": 1},
                    {"q": "What is a cover letter?", "opts": ["A summary on the resume", "A personalised letter accompanying a job application", "A reference letter", "A job description"], "ans": 1},
                    {"q": "What is the purpose of a LinkedIn profile?", "opts": ["Social entertainment", "Professional brand and job networking", "News reading", "Online shopping"], "ans": 1},
                ],
            }

    career = st.session_state.selected_career
    if not career:
        st.title("📘 LearnEd — Learning Platform")
        st.info("Select a career from your Career Matches first to unlock personalised learning content.")
        st.stop()

    career_name = career.get("career", "")
    resources = get_career_resources(career_name)

    st.title("📘 LearnEd — Learning Platform")
    st.subheader(f"Resources for: {career_name}")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["🎥 Videos", "📚 Resources", "🗺️ Roadmap", "🧠 Quiz"])

    with tab1:
        st.markdown("### Curated Videos")
        st.caption("Click a video to open it on YouTube and find the most current, relevant content.")
        for title, url in resources["videos"]:
            st.markdown(f"""
<a href="{url}" target="_blank" style="display:block; padding:16px 20px; margin:10px 0;
   background:linear-gradient(135deg,#1a1a2e,#16213e); border:1px solid #00d4ff;
   border-radius:10px; text-decoration:none; color:#00d4ff; font-size:16px;">
   ▶ &nbsp; {title}
</a>""", unsafe_allow_html=True)

    with tab2:
        st.markdown("### Free Learning Resources")
        links = resources["links"]
        if isinstance(links, dict):
            for category, items in links.items():
                st.markdown(f"**{category}**")
                for name, url in items:
                    st.markdown(f"- [{name}]({url})")
                st.markdown("")
        else:
            for name, url in links:
                st.markdown(f"- [{name}]({url})")

    with tab3:
        st.markdown("### Your Learning Roadmap")
        phase_colors = {"Beginner": "#00d4ff", "Intermediate": "#f4c430", "Advanced": "#ff6b6b", "Job Ready": "#00ff88"}
        current_phase = None
        for i, step in enumerate(resources["roadmap"], 1):
            if isinstance(step, tuple):
                phase, text = step
            else:
                phase, text = None, step
            if phase and phase != current_phase:
                current_phase = phase
                color = phase_colors.get(phase, "#aaa")
                st.markdown(f"<span style='background:{color};color:#000;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:bold'>{phase}</span>", unsafe_allow_html=True)
            st.markdown(f"**{i}.** {text}")

    with tab4:
        st.markdown("### Test Your Knowledge")
        st.markdown("Answer all questions and submit to see your score.")

        if "quiz_submitted" not in st.session_state:
            st.session_state.quiz_submitted = False

        quiz = resources["quiz"]
        user_answers = {}
        for qi, q in enumerate(quiz):
            st.markdown(f"**Q{qi+1}. {q['q']}**")
            choice = st.radio(
                label=f"q{qi+1}",
                options=q["opts"],
                index=None,
                key=f"quiz_{career_name}_{qi}",
                label_visibility="collapsed",
            )
            user_answers[qi] = choice

        if st.button("📝 Submit Quiz", type="primary"):
            if any(v is None for v in user_answers.values()):
                st.warning("Please answer all questions before submitting.")
            else:
                score = sum(
                    1 for qi, q in enumerate(quiz)
                    if user_answers[qi] == q["opts"][q["ans"]]
                )
                st.markdown("---")
                if score == len(quiz):
                    st.success(f"🏆 Perfect score! {score}/{len(quiz)}")
                elif score >= len(quiz) // 2:
                    st.warning(f"👍 Good effort! {score}/{len(quiz)}")
                else:
                    st.error(f"📖 Keep studying! {score}/{len(quiz)}")

                st.markdown("**Correct Answers:**")
                for qi, q in enumerate(quiz):
                    correct = q["opts"][q["ans"]]
                    got = user_answers[qi]
                    icon = "✅" if got == correct else "❌"
                    st.markdown(f"{icon} Q{qi+1}: **{correct}**")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🔙 Back to Career Matches"):
            st.session_state.page = "recommendations"
            save_session_to_storage()
            st.rerun()
    with col_b:
        if st.button("📄 Build My Resume"):
            st.session_state.page = "resume"
            save_session_to_storage()
            st.rerun()


# ═══════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════
elif page == "admin" and st.session_state.get("is_admin"):
    st.title("🛡️ Admin Dashboard")
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "👥 Users", "📋 Career Data", "📜 Activity Logs"])

    # ── Tab 1: Analytics ──
    with tab1:
        st.subheader("Platform Overview")

        with get_db_conn() as conn:
            total_users   = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active_trials = conn.execute("SELECT COUNT(*) FROM user_sessions WHERE trial_started=1").fetchone()[0]
            total_resumes = conn.execute("SELECT COUNT(*) FROM resumes").fetchone()[0]
            sessions_rows = conn.execute("SELECT trial_days_done, selected_career, user_stream FROM user_sessions").fetchall()

        # Count completed trials (all 7 days done)
        completed_trials = 0
        career_counts = {}
        stream_counts = {}
        for row in sessions_rows:
            try:
                days = _json.loads(row[0]) if row[0] else {}
                if all(days.get(str(d), False) for d in range(1, 8)):
                    completed_trials += 1
            except Exception:
                pass
            try:
                c = _json.loads(row[1]) if row[1] else None
                if c and c.get("career"):
                    name = c["career"]
                    career_counts[name] = career_counts.get(name, 0) + 1
            except Exception:
                pass
            if row[2]:
                stream_counts[row[2]] = stream_counts.get(row[2], 0) + 1

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Users", total_users)
        c2.metric("Active Trials", active_trials)
        c3.metric("Trials Completed", completed_trials)
        c4.metric("Resumes Created", total_resumes)
        c5.metric("Total Logins", conn.execute("SELECT COUNT(*) FROM activity_log WHERE action='login'").fetchone()[0] if False else "—")

        # Re-query login count properly
        with get_db_conn() as conn:
            login_count = conn.execute("SELECT COUNT(*) FROM activity_log WHERE action='login'").fetchone()[0]
        c5.metric("Total Logins", login_count)

        st.markdown("---")

        if career_counts:
            top_careers = sorted(career_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            fig = go.Figure(go.Bar(
                x=[c[1] for c in top_careers],
                y=[c[0] for c in top_careers],
                orientation="h",
                marker_color="#ff0080",
            ))
            fig.update_layout(
                title="Top 5 Most Selected Careers",
                xaxis_title="Users",
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e0e0e0"),
                height=300,
                margin=dict(l=10, r=10, t=40, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No career selections yet.")

        if stream_counts:
            st.markdown("**Most Popular Streams**")
            stream_df = pd.DataFrame(stream_counts.items(), columns=["Stream", "Users"]).sort_values("Users", ascending=False)
            st.dataframe(stream_df, use_container_width=True, hide_index=True)

    # ── Tab 2: User Management ──
    with tab2:
        st.subheader("All Users")

        with get_db_conn() as conn:
            rows = conn.execute("""
                SELECT u.username, u.email,
                       s.user_stream, s.selected_career, s.trial_started, s.trial_days_done,
                       CASE WHEN r.username IS NOT NULL THEN 'Yes' ELSE 'No' END AS resume
                FROM users u
                LEFT JOIN user_sessions s ON u.username = s.username
                LEFT JOIN resumes r ON u.username = r.username
            """).fetchall()

        table_data = []
        for row in rows:
            try:
                career_name = _json.loads(row[3]).get("career", "") if row[3] else ""
            except Exception:
                career_name = ""
            try:
                days = _json.loads(row[5]) if row[5] else {}
                trial_status = f"{sum(1 for d in range(1,8) if days.get(str(d), False))}/7 days"
            except Exception:
                trial_status = "Not started"
            table_data.append({
                "Username": row[0], "Email": row[1],
                "Stream": row[2] or "—", "Selected Career": career_name or "—",
                "Trial": trial_status, "Resume": row[6],
            })

        if table_data:
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        else:
            st.info("No users registered yet.")

        st.markdown("---")
        st.subheader("Delete User")
        usernames = [r["Username"] for r in table_data] if table_data else []
        del_user = st.selectbox("Select user to delete", ["— select —"] + usernames, key="admin_del_user")

        if del_user != "— select —":
            st.warning(f"⚠️ This will permanently delete **{del_user}** and all their data.")
            if st.button("🗑️ Confirm Delete", type="primary"):
                with get_db_conn() as conn:
                    for tbl in ["users", "user_sessions", "resumes", "activity_log"]:
                        conn.execute(f"DELETE FROM {tbl} WHERE username=?", (del_user,))
                    conn.commit()
                st.success(f"✅ User **{del_user}** deleted.")
                st.rerun()

    # ── Tab 3: Career Data Editor ──
    with tab3:
        st.subheader("Career Database Editor")
        st.caption(f"{len(df)} careers · columns: {', '.join(df.columns.tolist())}")

        edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic", key="career_editor")

        if st.button("💾 Save Changes to 500.csv", type="primary"):
            edited_df.to_csv("500.csv", index=False)
            load_data.clear()
            st.success("✅ Changes saved and cache cleared.")

    # ── Tab 4: Activity Logs ──
    with tab4:
        st.subheader("User Activity Log")

        with get_db_conn() as conn:
            all_users_log = [r[0] for r in conn.execute("SELECT DISTINCT username FROM activity_log ORDER BY username").fetchall()]
            filter_user = st.selectbox("Filter by user", ["All"] + all_users_log, key="log_filter")

            if filter_user == "All":
                log_rows = conn.execute(
                    "SELECT timestamp, username, action, detail FROM activity_log ORDER BY id DESC LIMIT 200"
                ).fetchall()
            else:
                log_rows = conn.execute(
                    "SELECT timestamp, username, action, detail FROM activity_log WHERE username=? ORDER BY id DESC LIMIT 200",
                    (filter_user,)
                ).fetchall()

        if log_rows:
            log_df = pd.DataFrame(log_rows, columns=["Timestamp", "Username", "Action", "Detail"])
            st.dataframe(log_df, use_container_width=True, hide_index=True)
        else:
            st.info("No activity logged yet.")
