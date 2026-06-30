from collections import Counter, defaultdict
from datetime import datetime, timedelta
import math
import calendar

from utils.content import MOOD_OPTIONS, SLEEP_PALETTE, TIME_SLOTS

def calculate_svg_slice(index, total, inner_r, outer_r, center_x, center_y):
    start_angle = (index * 360 / total) - 90
    end_angle = ((index + 1) * 360 / total) - 90
    
    start_rad = math.radians(start_angle)
    end_rad = math.radians(end_angle)
    
    x1_in = center_x + inner_r * math.cos(start_rad)
    y1_in = center_y + inner_r * math.sin(start_rad)
    x1_out = center_x + outer_r * math.cos(start_rad)
    y1_out = center_y + outer_r * math.sin(start_rad)
    
    x2_in = center_x + inner_r * math.cos(end_rad)
    y2_in = center_y + inner_r * math.sin(end_rad)
    x2_out = center_x + outer_r * math.cos(end_rad)
    y2_out = center_y + outer_r * math.sin(end_rad)
    
    path = f"M {x1_in} {y1_in} L {x1_out} {y1_out} A {outer_r} {outer_r} 0 0 1 {x2_out} {y2_out} L {x2_in} {y2_in} A {inner_r} {inner_r} 0 0 0 {x1_in} {y1_in} Z"
    
    mid_angle = (start_angle + end_angle) / 2
    mid_rad = math.radians(mid_angle)
    text_r = outer_r + 20
    text_x = center_x + text_r * math.cos(mid_rad)
    text_y = center_y + text_r * math.sin(mid_rad)
    
    return path, text_x, text_y, mid_angle


def average(values):
    return round(sum(values) / len(values), 1) if values else 0


def safe_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date()


def calculate_sleep_duration(bedtime, wake_time):
    bed = datetime.strptime(bedtime, "%H:%M")
    wake = datetime.strptime(wake_time, "%H:%M")
    if wake <= bed:
        wake += timedelta(days=1)
    return round((wake - bed).total_seconds() / 3600, 1)


def build_dashboard_context(user, journal_entries, mood_entries, sleep_logs, ledger, challenge_logs, sleep_fact):
    coin_balance = sum(entry["points"] for entry in ledger)
    today = datetime.now().date().isoformat()
    mood_today = {slot: None for slot in TIME_SLOTS}
    for entry in mood_entries:
        if entry["entry_date"] == today and entry["time_slot"] in mood_today and mood_today[entry["time_slot"]] is None:
            mood_today[entry["time_slot"]] = entry

    dominant_emotion = "No entries yet"
    if journal_entries:
        dominant_emotion = Counter(entry["emotion"] for entry in journal_entries).most_common(1)[0][0]

    average_sleep = average([item["duration_hours"] for item in sleep_logs[:7]])
    recent_highlights = []
    for entry in journal_entries[:2]:
        recent_highlights.append(
            {
                "title": f"{entry['emotion']} on {entry['entry_date']}",
                "copy": entry["recommendation"],
                "badge": entry["sentiment"],
            }
        )
    for entry in challenge_logs[:1]:
        recent_highlights.append(
            {
                "title": entry["challenge_title"],
                "copy": f"+{entry['coins_awarded']} coins from a calming challenge.",
                "badge": "Challenge",
            }
        )

    return {
        "welcome_title": (
            f"Welcome back, {user['name'].split()[0]}"
            if user["is_new"] == 0
            else f"Welcome, {user['name'].split()[0]}"
        ),
        "welcome_copy": (
            "Choose where you want to begin: journal, mood, sleep, music, or a quick calming challenge."
            if user["is_new"]
            else "Here is your gentle overview for today with journal, challenge, and insight sections."
        ),
        "summary_cards": [
            {"label": "Coins", "value": coin_balance, "copy": "journaling and activities add to this"},
            {"label": "Dominant Emotion", "value": dominant_emotion, "copy": "seen most often in recent entries"},
            {"label": "Mood Check-ins", "value": sum(1 for item in mood_today.values() if item), "copy": "completed today out of 4"},
            {"label": "Average Sleep", "value": average_sleep or "--", "copy": sleep_fact},
        ],
        "journal_section": {
            "title": "Journal Section",
            "copy": "Write or speak about your day, then let the AI map the feeling behind it.",
            "items": journal_entries[:3],
        },
        "challenge_section": {
            "title": "Daily Challenges Section",
            "copy": "Use tiny calming games when your mind feels crowded, then collect coins.",
            "items": challenge_logs[:3],
        },
        "insight_section": {
            "title": "Insights Section",
            "copy": "Spot patterns between mood, sleep, and reflection without feeling overloaded.",
            "items": recent_highlights,
        },
        "today_mood": mood_today,
        "charts": {
            "journal_dates": [entry["entry_date"] for entry in journal_entries[:7][::-1]],
            "journal_stress": [entry["stress_index"] for entry in journal_entries[:7][::-1]],
            "sleep_dates": [item["sleep_date"] for item in sleep_logs[:7][::-1]],
            "sleep_hours": [item["duration_hours"] for item in sleep_logs[:7][::-1]],
        },
    }


def build_mood_page_context(mood_entries):
    if not mood_entries:
        return {
            "summary": {
                "average_mood": 0,
                "best_time": "Not enough data",
                "toughest_day": "Not enough data",
                "weekly_story": "Start with a few check-ins and your monthly tracker will begin to fill with color.",
            },
            "legend": MOOD_OPTIONS,
            "month_cells": [],
            "insights": [
                "Try one mood check-in in the morning and one at night to start building your monthly picture."
            ],
            "charts": {
                "weekdays": [],
                "weekday_scores": [],
                "slot_labels": [],
                "slot_scores": [],
            },
        }

    score_values = [entry["mood_score"] for entry in mood_entries]
    slot_scores = defaultdict(list)
    weekday_scores = defaultdict(list)
    by_day = {}

    for entry in mood_entries:
        slot_scores[entry["time_slot"]].append(entry["mood_score"])
        weekday_scores[safe_date(entry["entry_date"]).strftime("%A")].append(entry["mood_score"])
        by_day.setdefault(entry["entry_date"], []).append(entry)

    best_time = max(slot_scores.items(), key=lambda item: average(item[1]))[0]
    toughest_day = min(weekday_scores.items(), key=lambda item: average(item[1]))[0]

    tracker_month = ""
    recent_dates = sorted(by_day.keys(), reverse=True)
    if recent_dates:
        anchor_date = safe_date(recent_dates[0])
        tracker_month = calendar.month_name[anchor_date.month].upper()
        # Find exact number of days logically:
        days_in_month = calendar.monthrange(anchor_date.year, anchor_date.month)[1]
        month_cells = []
        for day_number in range(1, days_in_month + 1):
            path, text_x, text_y, rot = calculate_svg_slice(day_number - 1, days_in_month, 90, 160, 200, 200)
            
            matching_entries = [
                entry for value, entries in by_day.items()
                if safe_date(value).month == anchor_date.month and safe_date(value).day == day_number
                for entry in entries
            ]
            if matching_entries:
                day_score = average([item["mood_score"] for item in matching_entries])
                dominant = sorted(matching_entries, key=lambda item: item["mood_score"], reverse=True)[0]
                month_cells.append(
                    {
                        "day": day_number,
                        "label": dominant["mood_label"],
                        "color_hex": dominant["color_hex"],
                        "score": day_score,
                        "note": matching_entries[-1]["note"],
                        "filled": True,
                        "svg_path": path,
                        "text_x": text_x,
                        "text_y": text_y
                    }
                )
            else:
                month_cells.append(
                    {
                        "day": day_number,
                        "label": "No check-in",
                        "color_hex": "transparent",
                        "score": None,
                        "note": "",
                        "filled": False,
                        "svg_path": path,
                        "text_x": text_x,
                        "text_y": text_y
                    }
                )
    else:
        month_cells = []

    average_mood = average(score_values)
    insights = [
        f"Your mood feels strongest during {best_time.lower()} check-ins.",
        f"Your heaviest dips tend to show up on {toughest_day}s.",
        "A tiny note on low-energy days makes the weekly summary much smarter and kinder.",
    ]

    if average_mood >= 4:
        weekly_story = "Your month looks gently supported right now. Keep the routines that are helping."
    elif average_mood >= 3:
        weekly_story = "Your mood pattern feels mixed and human. Small consistent check-ins will make it clearer."
    else:
        weekly_story = "This month carries some heavier color. Stay gentle with yourself and keep notes short but honest."

    ordered_weekdays = list(weekday_scores.keys())
    return {
        "summary": {
            "average_mood": average_mood,
            "best_time": best_time,
            "toughest_day": toughest_day,
            "weekly_story": weekly_story,
        },
        "legend": MOOD_OPTIONS,
        "tracker_month": tracker_month,
        "month_cells": month_cells,
        "insights": insights,
        "charts": {
            "weekdays": ordered_weekdays,
            "weekday_scores": [average(weekday_scores[day]) for day in ordered_weekdays],
            "slot_labels": list(slot_scores.keys()),
            "slot_scores": [average(slot_scores[slot]) for slot in slot_scores.keys()],
        },
    }


def sleep_color_for_hours(hours):
    if hours < 4:
        return SLEEP_PALETTE[0]["color"]
    if hours < 5:
        return SLEEP_PALETTE[1]["color"]
    if hours < 6:
        return SLEEP_PALETTE[2]["color"]
    if hours < 7:
        return SLEEP_PALETTE[3]["color"]
    if hours < 8:
        return SLEEP_PALETTE[4]["color"]
    return SLEEP_PALETTE[5]["color"]


def build_sleep_page_context(sleep_logs, sleep_fact):
    # Convert sqlite3.Row objects to plain dicts so .get() works
    sleep_logs = [dict(log) for log in sleep_logs]
    
    if not sleep_logs:
        import calendar
        from datetime import datetime
        now = datetime.now()
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        empty_points = [{"day": d, "x": 60 + ((d - 1) / max(1, days_in_month - 1)) * 620, "has_data": False} for d in range(1, days_in_month + 1)]
        
        return {
            "summary": {
                "average_duration": 0,
                "average_quality": 0,
                "consistency": "No trend yet",
                "weekly_story": "Add a few nights and your sleep graph will begin to plot your patterns.",
            },
            "insights": [sleep_fact],
            "graph_points": empty_points,
            "graph_path": "",
            "days_in_month": days_in_month,
            "legend": SLEEP_PALETTE,
            "charts": {"dates": [], "hours": [], "quality": []},
        }

    durations = [log["duration_hours"] for log in sleep_logs[:7]]
    qualities = [log["quality_rating"] for log in sleep_logs[:7]]
    consistency_range = max(durations) - min(durations) if len(durations) > 1 else 0

    if consistency_range <= 1:
        consistency = "Very consistent"
    elif consistency_range <= 2:
        consistency = "Mostly consistent"
    else:
        consistency = "Quite irregular"

    avg_duration = average(durations)
    avg_quality = average(qualities)

    if avg_duration >= 7 and avg_quality >= 4:
        weekly_story = "Your sleep month looks soft and supportive. Keep protecting this rhythm."
    elif avg_duration < 6.5:
        weekly_story = "Your rest looks shorter than your body may want. An earlier wind-down could help."
    else:
        weekly_story = "Your sleep is present but uneven. A more regular bedtime may make mornings gentler."

    import calendar
    
    anchor_date = safe_date(sleep_logs[0]["sleep_date"])
    latest_month = anchor_date.month
    days_in_month = calendar.monthrange(anchor_date.year, latest_month)[1]
    
    by_day = {safe_date(log["sleep_date"]).day: log for log in sleep_logs if safe_date(log["sleep_date"]).month == latest_month}
    graph_points = []
    line_path_parts = []
    draw_next_as_m = True
    
    pad_l, pad_r, pad_t, pad_b = 60, 20, 20, 30
    g_w = 700 - pad_l - pad_r
    g_h = 250 - pad_t - pad_b
    
    for day_number in range(1, days_in_month + 1):
        x = pad_l + ((day_number - 1) / max(1, days_in_month - 1)) * g_w
        log = by_day.get(day_number)
        
        if log:
            hours = log["duration_hours"]
            h_capped = max(4, min(10, hours))
            y = pad_t + g_h - ((h_capped - 5) / 5) * g_h
            
            graph_points.append({
                "day": day_number,
                "hours": hours,
                "quality": log["quality_rating"],
                "color": sleep_color_for_hours(log["duration_hours"]),
                "x": x,
                "y": y,
                "has_data": True,
                "note": log.get("note", "")
            })
            
            prefix = "M" if draw_next_as_m else "L"
            line_path_parts.append(f"{prefix} {x} {y}")
            draw_next_as_m = False
        else:
            graph_points.append({
                "day": day_number,
                "x": x,
                "has_data": False
            })
            draw_next_as_m = True

    insights = [
        sleep_fact,
        f"Your average sleep duration this week is {avg_duration} hours.",
        "If weekends shift later than weekdays, try pulling bedtime back gradually instead of all at once.",
    ]

    return {
        "summary": {
            "average_duration": avg_duration,
            "average_quality": avg_quality,
            "consistency": consistency,
            "weekly_story": weekly_story,
        },
        "insights": insights,
        "graph_points": graph_points,
        "graph_path": " ".join(line_path_parts),
        "days_in_month": days_in_month,
        "legend": SLEEP_PALETTE,
        "charts": {
            "dates": [log["sleep_date"] for log in sleep_logs[:7][::-1]],
            "hours": [log["duration_hours"] for log in sleep_logs[:7][::-1]],
            "quality": [log["quality_rating"] for log in sleep_logs[:7][::-1]],
        },
    }


def build_challenges_context(user, ledger, challenge_logs, journal_entries, mood_entries, reflection_prompt, insight_unlocked):
    coin_balance = sum(entry["points"] for entry in ledger)
    most_frequent_emotion = "No entries yet"
    suggestion = "Write a few journal entries or mood notes to unlock a more personal pattern."

    if journal_entries:
        emotion_counts = Counter(entry["emotion"] for entry in journal_entries)
        most_frequent_emotion = emotion_counts.most_common(1)[0][0]
        suggestion = journal_entries[0]["recommendation"]

    mood_days = Counter(entry["mood_label"] for entry in mood_entries)
    return {
        "coin_balance": coin_balance,
        "progress_to_unlock": min(100, int((coin_balance / 20) * 100)),
        "challenge_logs": challenge_logs[:6],
        "reflection_prompt": reflection_prompt,
        "insight_unlocked": insight_unlocked and coin_balance >= 20,
        "weekly_insight": {
            "emotion": most_frequent_emotion,
            "suggestion": suggestion,
            "mood_hint": mood_days.most_common(1)[0][0] if mood_days else "No mood pattern yet",
        },
    }
