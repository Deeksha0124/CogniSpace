from functools import lru_cache

from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline


ZERO_SHOT_MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"

EMOTION_LABELS = [
    "calm",
    "joy",
    "stress",
    "anxiety",
    "sadness",
    "anger",
    "overwhelm",
    "motivation",
]

SENTIMENT_LABELS = ["positive", "neutral", "negative"]

THEME_LABELS = [
    "workload",
    "academics",
    "sleep",
    "relationships",
    "health",
    "exercise",
    "food",
    "self-care",
    "finances",
    "creativity",
]

ENERGY_BY_EMOTION = {
    "calm": "Moderate",
    "joy": "High",
    "stress": "High",
    "anxiety": "High",
    "sadness": "Low",
    "anger": "High",
    "overwhelm": "High",
    "motivation": "High",
}

STRESS_BY_EMOTION = {
    "calm": 24,
    "joy": 18,
    "stress": 82,
    "anxiety": 86,
    "sadness": 63,
    "anger": 74,
    "overwhelm": 88,
    "motivation": 30,
}

RECOMMENDATIONS = {
    "calm": "This entry carries steadier energy. Protect what helped and build another small supportive routine around it.",
    "joy": "Your mood is being supported by something meaningful. Try naming the moment clearly so you can repeat it later in the week.",
    "stress": "The text shows pressure building up. Break the next task into the smallest possible first step and take one short pause before resuming.",
    "anxiety": "This reflection sounds future-focused and tense. Shift from vague worry to a short list of what is known, unknown, and controllable.",
    "sadness": "The emotional tone feels heavy. Keep today gentle and try one supportive action that reconnects you with comfort or company.",
    "anger": "There is a sharper edge in the language. Try noting the trigger, the unmet need behind it, and one calmer response you can try next.",
    "overwhelm": "A lot seems to be happening at once. Reduce the load by choosing one priority, one support, and one thing that can wait.",
    "motivation": "This entry carries drive and forward motion. Capture what gave you energy so it remains available when motivation dips.",
}


@lru_cache(maxsize=1)
def get_zero_shot_pipeline():
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            ZERO_SHOT_MODEL_NAME,
            local_files_only=True,
        )
        model = AutoModelForSequenceClassification.from_pretrained(
            ZERO_SHOT_MODEL_NAME,
            local_files_only=True,
        )
        return pipeline(
            "zero-shot-classification",
            model=model,
            tokenizer=tokenizer,
        )
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(ZERO_SHOT_MODEL_NAME)
        model = AutoModelForSequenceClassification.from_pretrained(ZERO_SHOT_MODEL_NAME)
        return pipeline("zero-shot-classification", model=model, tokenizer=tokenizer)


def classify_labels(text, labels, hypothesis_template):
    results = get_zero_shot_pipeline()(
        text,
        candidate_labels=labels,
        hypothesis_template=hypothesis_template,
        multi_label=False,
    )
    return list(zip(results["labels"], results["scores"]))


def classify_themes(text):
    results = get_zero_shot_pipeline()(
        text,
        candidate_labels=THEME_LABELS,
        hypothesis_template="This journal entry is mostly about {}.",
        multi_label=True,
    )
    matches = [
        label.title()
        for label, score in zip(results["labels"], results["scores"])
        if score >= 0.24
    ]
    return matches[:3] or ["General Reflection"]


def build_forecast(emotion, sentiment, themes):
    lead_theme = themes[0].lower()
    if sentiment == "Negative":
        return (
            f"If the current {lead_theme} pattern continues, emotional load may stay elevated over the next few check-ins."
        )
    if sentiment == "Positive":
        return (
            f"The current {lead_theme} pattern looks supportive. Repeating it may help keep your week more stable."
        )
    return (
        f"The {lead_theme} pattern is still mixed. A few more detailed entries will make the next forecast more reliable."
    )


def analyze_text_entry(text, input_language="en-US"):
    emotion_pairs = classify_labels(
        text,
        EMOTION_LABELS,
        "The dominant emotion in this text is {}.",
    )
    sentiment_pairs = classify_labels(
        text,
        SENTIMENT_LABELS,
        "The overall sentiment of this text is {}.",
    )

    dominant_emotion, dominant_emotion_score = emotion_pairs[0]
    dominant_sentiment, dominant_sentiment_score = sentiment_pairs[0]
    themes = classify_themes(text)

    stress_index = STRESS_BY_EMOTION.get(dominant_emotion, 50)
    if dominant_sentiment == "negative":
        stress_index = min(100, stress_index + 6)
    elif dominant_sentiment == "positive":
        stress_index = max(0, stress_index - 8)

    recommendation = RECOMMENDATIONS.get(dominant_emotion, RECOMMENDATIONS["calm"])

    return {
        "input_language": input_language,
        "sentiment": dominant_sentiment.title(),
        "sentiment_score": round(dominant_sentiment_score, 4),
        "emotion": dominant_emotion.title(),
        "emotion_confidence": round(dominant_emotion_score, 4),
        "emotion_scores": {
            label.title(): round(score, 4) for label, score in emotion_pairs
        },
        "themes": themes,
        "energy_level": ENERGY_BY_EMOTION.get(dominant_emotion, "Moderate"),
        "stress_index": stress_index,
        "recommendation": recommendation,
        "forecast": build_forecast(
            dominant_emotion,
            dominant_sentiment.title(),
            themes,
        ),
    }
