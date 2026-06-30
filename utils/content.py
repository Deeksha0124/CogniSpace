APP_BRAND = "CogniSpace"
APP_SUBTITLE = "Your calm AI wellness journal"

TIME_SLOTS = ["Morning", "Noon", "Evening", "Night"]

TAB_INTRO = {
    "dashboard": {
        "title": "Home",
        "copy": "See your journal, daily challenges, and insights in one calming place.",
    },
    "journal": {
        "title": "Journal",
        "copy": "Write or speak about your day and let the AI turn your reflection into emotional patterns and gentle suggestions.",
    },
    "mood": {
        "title": "Mood Tracker",
        "copy": "Track how each day feels through color and notice the monthly story your moods create.",
    },
    "sleep": {
        "title": "Sleep Tracker",
        "copy": "Log your rest, spot your rhythm, and see your sleep month bloom into a visual pattern.",
    },
    "challenges": {
        "title": "Daily Challenges",
        "copy": "Play calm mini challenges when you need a reset, earn coins, and unlock a simple weekly insight.",
    },
    "music": {
        "title": "Music",
        "copy": "Play your own soothing songs or explore carefully chosen calm listening suggestions.",
    },
    "profile": {
        "title": "Profile",
        "copy": "Keep your personal details and activity summary in one uncluttered view.",
    },
}

ONBOARDING_PATHS = [
    {"title": "Journal", "copy": "Write or dictate how your day felt.", "endpoint": "journal"},
    {"title": "Mood", "copy": "Fill your monthly mood board with color.", "endpoint": "mood"},
    {"title": "Sleep", "copy": "Build a soft moon-ring of your sleep.", "endpoint": "sleep"},
    {"title": "Challenges", "copy": "Play quick calm games and collect coins.", "endpoint": "challenges"},
    {"title": "Music", "copy": "Upload songs or try a soothing suggestion.", "endpoint": "music"},
]

MOOD_OPTIONS = [
    {"key": "happy", "label": "Happy", "color": "#F7C5D6", "score": 5},
    {"key": "calm", "label": "Calm", "color": "#CBE8F5", "score": 4},
    {"key": "excited", "label": "Excited", "color": "#FFF1BF", "score": 5},
    {"key": "motivated", "label": "Motivated", "color": "#E4D4F7", "score": 4},
    {"key": "tired", "label": "Tired", "color": "#D8D8D8", "score": 2},
    {"key": "sad", "label": "Sad", "color": "#AFC8EE", "score": 1},
    {"key": "stressed", "label": "Stressed", "color": "#FFD682", "score": 2},
    {"key": "angry", "label": "Angry", "color": "#FF98B2", "score": 1},
    {"key": "grateful", "label": "Grateful", "color": "#D8C3F2", "score": 4},
    {"key": "neutral", "label": "Neutral", "color": "#DDEFD0", "score": 3},
]

SLEEP_FACTS = [
    "Keeping your sleep and wake times close together each day helps your circadian rhythm stay steady.",
    "A calm wind-down routine can make it easier for your body to understand that rest is coming.",
    "Light exposure in the morning often helps your body feel more alert during the day and sleepier at night.",
    "Late caffeine can stretch into the night longer than people expect, even if you still feel sleepy.",
    "Good sleep quality is shaped by both duration and consistency, not just the number of hours on one night.",
]

SLEEP_PALETTE = [
    {"label": "0-4 hrs", "color": "#F6C4EC"},
    {"label": "4-5 hrs", "color": "#D8B7FF"},
    {"label": "5-6 hrs", "color": "#B5B6FF"},
    {"label": "6-7 hrs", "color": "#8CD4FF"},
    {"label": "7-8 hrs", "color": "#BCEBBE"},
    {"label": "8+ hrs", "color": "#FFEAA7"},
]

CHALLENGE_GAMES = [
    {
        "key": "breathing",
        "title": "Breathing Bloom",
        "coins": 10,
        "copy": "Follow the inhale and exhale circle for a short reset.",
    },
    {
        "key": "reflection",
        "title": "Reflection Prompt",
        "coins": 10,
        "copy": "Answer one gentle prompt and collect calm coins.",
    },
    {
        "key": "memory",
        "title": "Memory Lights",
        "coins": 10,
        "copy": "Watch the color sequence and repeat it from memory.",
    },
    {
        "key": "pattern",
        "title": "Pattern Spark",
        "coins": 10,
        "copy": "Solve a tiny number pattern challenge.",
    },
    {
        "key": "focus",
        "title": "Focus Tap",
        "coins": 10,
        "copy": "Catch the floating dots to bring your focus back to the present.",
    },
    {
        "key": "word",
        "title": "Word Garden",
        "coins": 10,
        "copy": "Unscramble one calm word before the timer fades.",
    },
]

REFLECTION_PROMPTS = [
    "What made you feel safest today?",
    "What made you happy today?",
    "What stressed you out today?",
    "What helped you feel calmer than before?",
    "What do you need a little more of tomorrow?",
]

MUSIC_SUGGESTIONS = [
    {
        "title": "Deep Sleep Piano Music",
        "kind": "Sleep",
        "copy": "Long-form piano sleep music with no sudden vocals or heavy percussion.",
        "url": "https://music.youtube.com/playlist?list=PLWuO4z0TgFRHofw9N26R4MTRF6DhlqQQv",
        "source": "YouTube Music",
    },
    {
        "title": "Breathing Cycles",
        "kind": "Breathing",
        "copy": "Music-guided breathing designed specifically for calm, balance, and nervous-system regulation.",
        "url": "https://breathingcycles.com/en/",
        "source": "Breathing Cycles",
    },
    {
        "title": "Relaxing Ambient Music for Sleep",
        "kind": "Ambient",
        "copy": "Slow, uninterrupted ambient soundscapes for sleep, meditation, and quiet journaling.",
        "url": "https://www.youtube.com/watch?v=WAQbqXlXffA",
        "source": "YouTube",
    },
]
