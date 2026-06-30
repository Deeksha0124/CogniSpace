import json
import os
import random
import re
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from utils.content import (
    APP_BRAND,
    APP_SUBTITLE,
    CHALLENGE_GAMES,
    MOOD_OPTIONS,
    MUSIC_SUGGESTIONS,
    ONBOARDING_PATHS,
    REFLECTION_PROMPTS,
    SLEEP_FACTS,
    TAB_INTRO,
    TIME_SLOTS,
)
from utils.db import get_connection, init_db
from utils.model_service import analyze_text_entry
from utils.pattern_analyzer import (
    build_challenges_context,
    build_dashboard_context,
    build_mood_page_context,
    build_sleep_page_context,
    calculate_sleep_duration,
)


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-for-production")


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def query_one(query, params=()):
    conn = get_connection()
    try:
        return conn.execute(query, params).fetchone()
    finally:
        conn.close()


def query_all(query, params=()):
    conn = get_connection()
    try:
        return conn.execute(query, params).fetchall()
    finally:
        conn.close()


def execute_write(query, params=()):
    conn = get_connection()
    try:
        cursor = conn.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def format_display_date(value):
    if not value:
        return ""
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d-%m-%Y")
    except ValueError:
        return value


def strong_password_message(password):
    if len(password) < 8:
        return "Use at least 8 characters for a stronger password."
    if not re.search(r"[a-z]", password):
        return "Add at least one lowercase letter."
    if not re.search(r"[A-Z]", password):
        return "Add at least one uppercase letter."
    if not re.search(r"\d", password):
        return "Add at least one number."
    if not re.search(r"[^A-Za-z0-9]", password):
        return "Add at least one special character."
    return ""


def create_coin_entry(user_id, coins, category, description):
    execute_write(
        """
        INSERT INTO reward_ledger (user_id, points, category, description, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, coins, category, description, datetime.now().isoformat(timespec="seconds")),
    )


def get_coin_balance(user_id):
    row = query_one(
        "SELECT COALESCE(SUM(points), 0) AS coin_balance FROM reward_ledger WHERE user_id = ?",
        (user_id,),
    )
    return row["coin_balance"] if row else 0


def current_sleep_fact(user_id):
    index = (user_id + date.today().toordinal()) % len(SLEEP_FACTS)
    return SLEEP_FACTS[index]


def current_reflection_prompt(user_id):
    index = (user_id + date.today().toordinal()) % len(REFLECTION_PROMPTS)
    return REFLECTION_PROMPTS[index]


@app.template_filter("display_date")
def display_date_filter(value):
    return format_display_date(value)


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
        return
    g.user = query_one("SELECT * FROM users WHERE id = ?", (user_id,))


@app.context_processor
def inject_globals():
    return {
        "app_brand": APP_BRAND,
        "app_subtitle": APP_SUBTITLE,
        "current_user": g.user,
        "today_iso": date.today().isoformat(),
        "tab_intro": TAB_INTRO,
        "current_endpoint": request.endpoint or "",
    }


@app.route("/")
def root():
    if g.user:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()

        if not all([name, email, phone, password]):
            flash("Please fill in every field so we can create your space.", "error")
        elif query_one(
            "SELECT id FROM users WHERE email = ? OR phone = ?",
            (email, phone),
        ):
            flash("An account already exists with that email or phone number.", "error")
        else:
            user_id = execute_write(
                """
                INSERT INTO users (name, email, phone, password_hash, is_new, seen_tour, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    name,
                    email,
                    phone,
                    generate_password_hash(password),
                    1,
                    0,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            session.clear()
            session["user_id"] = user_id
            flash("Your account is ready. Let's begin gently.", "success")
            return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip().lower()
        password = request.form.get("password", "").strip()
        user = query_one(
            "SELECT * FROM users WHERE email = ? OR phone = ?",
            (identifier, identifier),
        )

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("That login did not match our records. Please try again.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            flash(f"Welcome back, {user['name'].split()[0]}.", "success")
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("You've been signed out safely.", "success")
    return redirect(url_for("login"))


@app.route("/profile/delete", methods=["POST"])
@login_required
def delete_profile():
    confirmation = request.form.get("confirmation", "").strip()
    if confirmation != "DELETE":
        flash('Type "DELETE" exactly to remove your profile.', "error")
        return redirect(url_for("profile"))

    user_id = g.user["id"]
    conn = get_connection()
    try:
        for table_name in [
            "challenge_logs",
            "reward_ledger",
            "sleep_logs",
            "mood_entries",
            "journal_entries",
            "users",
        ]:
            conn.execute(f"DELETE FROM {table_name} WHERE user_id = ?" if table_name != "users" else "DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()

    session.clear()
    flash("Your profile and personal data were deleted.", "success")
    return redirect(url_for("signup"))


@app.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password", "").strip()
    new_password = request.form.get("new_password", "").strip()

    if not current_password or not new_password:
        flash("Please provide both current and new passwords.", "error")
        return redirect(url_for("profile"))

    user = query_one("SELECT * FROM users WHERE id = ?", (g.user["id"],))
    if not check_password_hash(user["password_hash"], current_password):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("profile"))

    password_error = strong_password_message(new_password)
    if password_error:
        flash(f"New password is not strong enough: {password_error}", "error")
        return redirect(url_for("profile"))

    execute_write(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (generate_password_hash(new_password), g.user["id"])
    )
    flash("Your password has been securely updated.", "success")
    return redirect(url_for("profile"))


@app.route("/tour-complete", methods=["POST"])
@login_required
def complete_tour():
    execute_write("UPDATE users SET seen_tour = 1, is_new = 0 WHERE id = ?", (g.user["id"],))
    flash("You can reopen this tour any time from the home page if you need a reminder.", "success")
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    journal_entries = query_all(
        "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC",
        (g.user["id"],),
    )
    mood_entries = query_all(
        "SELECT * FROM mood_entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC",
        (g.user["id"],),
    )
    sleep_logs = query_all(
        "SELECT * FROM sleep_logs WHERE user_id = ? ORDER BY sleep_date DESC, id DESC",
        (g.user["id"],),
    )
    ledger = query_all(
        "SELECT * FROM reward_ledger WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (g.user["id"],),
    )
    challenge_logs = query_all(
        "SELECT * FROM challenge_logs WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (g.user["id"],),
    )

    context = build_dashboard_context(
        g.user,
        journal_entries,
        mood_entries,
        sleep_logs,
        ledger,
        challenge_logs,
        current_sleep_fact(g.user["id"]),
    )

    return render_template(
        "dashboard.html",
        payload=context,
        chart_payload=json.dumps(context["charts"]),
        onboarding_paths=ONBOARDING_PATHS,
        show_tour=g.user["seen_tour"] == 0,
    )


@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    if request.method == "POST":
        entry_date = request.form.get("entry_date", "").strip()
        journal_text = request.form.get("journal_text", "").strip()
        input_language = request.form.get("input_language", "en-US").strip()
        source_type = request.form.get("source_type", "text").strip()

        if not entry_date or not journal_text:
            flash("Please add a date and a reflection before analyzing.", "error")
        else:
            analysis = analyze_text_entry(journal_text, input_language=input_language)
            execute_write(
                """
                INSERT INTO journal_entries (
                    user_id, entry_date, journal_text, source_type, input_language,
                    sentiment, sentiment_score, emotion, emotion_confidence, emotion_scores,
                    themes, energy_level, stress_index, recommendation, forecast, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    g.user["id"],
                    entry_date,
                    journal_text,
                    source_type,
                    input_language,
                    analysis["sentiment"],
                    analysis["sentiment_score"],
                    analysis["emotion"],
                    analysis["emotion_confidence"],
                    json.dumps(analysis["emotion_scores"]),
                    json.dumps(analysis["themes"]),
                    analysis["energy_level"],
                    analysis["stress_index"],
                    analysis["recommendation"],
                    analysis["forecast"],
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            create_coin_entry(
                g.user["id"],
                5,
                "journal",
                "Added a journal entry",
            )
            execute_write("UPDATE users SET is_new = 0 WHERE id = ?", (g.user["id"],))
            flash("Your journal entry has been analyzed and saved.", "success")
            return redirect(url_for("journal"))

    entries = query_all(
        "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC",
        (g.user["id"],),
    )
    latest_entry = entries[0] if entries else None
    return render_template("journal.html", entries=entries, latest_entry=latest_entry)


@app.route("/mood", methods=["GET", "POST"])
@login_required
def mood():
    if request.method == "POST":
        entry_date = request.form.get("entry_date", "").strip()
        time_slot = request.form.get("time_slot", "").strip()
        mood_key = request.form.get("mood_key", "").strip()
        note = request.form.get("note", "").strip()
        input_language = request.form.get("input_language", "en-US").strip()
        source_type = request.form.get("source_type", "text").strip()

        mood_meta = next((item for item in MOOD_OPTIONS if item["key"] == mood_key), None)

        if not entry_date or not time_slot or mood_meta is None:
            flash("Choose a date, time, and mood color before saving.", "error")
        else:
            journal_entry_id = None
            if note:
                analysis = analyze_text_entry(note, input_language=input_language)
                journal_entry_id = execute_write(
                    """
                    INSERT INTO journal_entries (
                        user_id, entry_date, journal_text, source_type, input_language,
                        sentiment, sentiment_score, emotion, emotion_confidence, emotion_scores,
                        themes, energy_level, stress_index, recommendation, forecast, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        g.user["id"],
                        entry_date,
                        note,
                        source_type,
                        input_language,
                        analysis["sentiment"],
                        analysis["sentiment_score"],
                        analysis["emotion"],
                        analysis["emotion_confidence"],
                        json.dumps(analysis["emotion_scores"]),
                        json.dumps(analysis["themes"]),
                        analysis["energy_level"],
                        analysis["stress_index"],
                        analysis["recommendation"],
                        analysis["forecast"],
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )

            execute_write(
                """
                INSERT INTO mood_entries (
                    user_id, entry_date, time_slot, mood_key, mood_label, color_hex,
                    mood_score, note, journal_entry_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    g.user["id"],
                    entry_date,
                    time_slot,
                    mood_meta["key"],
                    mood_meta["label"],
                    mood_meta["color"],
                    mood_meta["score"],
                    note,
                    journal_entry_id,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            create_coin_entry(
                g.user["id"],
                10,
                "mood",
                f"Completed a {time_slot.lower()} mood check-in",
            )
            execute_write("UPDATE users SET is_new = 0 WHERE id = ?", (g.user["id"],))
            flash("Your mood check-in has been added.", "success")
            return redirect(url_for("mood"))

    mood_entries = query_all(
        "SELECT * FROM mood_entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC",
        (g.user["id"],),
    )
    mood_context = build_mood_page_context(mood_entries)
    mood_entries_list = [dict(e) for e in mood_entries]
    return render_template(
        "mood.html",
        mood_entries=mood_entries_list,
        mood_context=mood_context,
        mood_chart_payload=json.dumps(mood_context["charts"]),
        mood_options=MOOD_OPTIONS,
        time_slots=TIME_SLOTS,
    )


@app.route("/sleep", methods=["GET", "POST"])
@login_required
def sleep():
    if request.method == "POST":
        sleep_date = request.form.get("sleep_date", "").strip()
        bedtime = request.form.get("bedtime", "").strip()
        wake_time = request.form.get("wake_time", "").strip()
        quality_rating = int(request.form.get("quality_rating", "3"))
        note = request.form.get("note", "").strip()

        if not sleep_date or not bedtime or not wake_time:
            flash("Please log bedtime and wake time to save sleep data.", "error")
        else:
            duration_hours = calculate_sleep_duration(bedtime, wake_time)
            execute_write(
                """
                INSERT INTO sleep_logs (
                    user_id, sleep_date, bedtime, wake_time, duration_hours,
                    quality_rating, note, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    g.user["id"],
                    sleep_date,
                    bedtime,
                    wake_time,
                    duration_hours,
                    quality_rating,
                    note,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            create_coin_entry(
                g.user["id"],
                10,
                "sleep",
                f"Logged sleep ({duration_hours} hrs, quality {quality_rating}/5)",
            )
            execute_write("UPDATE users SET is_new = 0 WHERE id = ?", (g.user["id"],))
            flash("Sleep log saved. Your monthly tracker has been updated.", "success")
            return redirect(url_for("sleep"))

    sleep_logs = query_all(
        "SELECT * FROM sleep_logs WHERE user_id = ? ORDER BY sleep_date DESC, id DESC",
        (g.user["id"],),
    )
    sleep_context = build_sleep_page_context(sleep_logs, current_sleep_fact(g.user["id"]))
    return render_template(
        "sleep.html",
        sleep_logs=sleep_logs,
        sleep_context=sleep_context,
        sleep_chart_payload=json.dumps(sleep_context["charts"]),
    )


@app.route("/challenges", methods=["GET", "POST"])
@login_required
def challenges():
    if request.method == "POST":
        action = request.form.get("action", "").strip()
        challenge_key = request.form.get("challenge_key", "").strip()
        challenge = next((item for item in CHALLENGE_GAMES if item["key"] == challenge_key), None)

        if action == "complete_challenge" and challenge is not None:
            notes = request.form.get("notes", "").strip()
            execute_write(
                """
                INSERT INTO challenge_logs (
                    user_id, challenge_key, challenge_title, coins_awarded, notes, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    g.user["id"],
                    challenge["key"],
                    challenge["title"],
                    challenge["coins"],
                    notes,
                    datetime.now().isoformat(timespec="seconds"),
                ),
            )
            create_coin_entry(
                g.user["id"],
                challenge["coins"],
                "challenge",
                f"Completed {challenge['title']}",
            )
            flash(f"You earned {challenge['coins']} coins from {challenge['title']}.", "success")
            return redirect(url_for("challenges"))

        if action == "unlock_weekly_insight":
            if get_coin_balance(g.user["id"]) >= 20:
                session["weekly_insight_unlocked"] = True
                flash("Weekly mood insight unlocked.", "success")
            else:
                flash("You need at least 20 coins to unlock the weekly mood insight.", "error")
            return redirect(url_for("challenges"))

    journal_entries = query_all(
        "SELECT * FROM journal_entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC",
        (g.user["id"],),
    )
    mood_entries = query_all(
        "SELECT * FROM mood_entries WHERE user_id = ? ORDER BY entry_date DESC, id DESC",
        (g.user["id"],),
    )
    ledger = query_all(
        "SELECT * FROM reward_ledger WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (g.user["id"],),
    )
    challenge_logs = query_all(
        "SELECT * FROM challenge_logs WHERE user_id = ? ORDER BY created_at DESC, id DESC",
        (g.user["id"],),
    )
    context = build_challenges_context(
        g.user,
        ledger,
        challenge_logs,
        journal_entries,
        mood_entries,
        current_reflection_prompt(g.user["id"]),
        session.get("weekly_insight_unlocked", False),
    )
    return render_template(
        "challenges.html",
        challenges_context=context,
        challenge_games=CHALLENGE_GAMES,
    )


@app.route("/rewards")
@login_required
def rewards_redirect():
    return redirect(url_for("challenges"))


@app.route("/music")
@login_required
def music():
    return render_template("music.html", playlists=MUSIC_SUGGESTIONS)


@app.route("/profile")
@login_required
def profile():
    stats = {
        "journal_entries": query_one(
            "SELECT COUNT(*) AS count FROM journal_entries WHERE user_id = ?",
            (g.user["id"],),
        )["count"],
        "mood_checkins": query_one(
            "SELECT COUNT(*) AS count FROM mood_entries WHERE user_id = ?",
            (g.user["id"],),
        )["count"],
        "sleep_logs": query_one(
            "SELECT COUNT(*) AS count FROM sleep_logs WHERE user_id = ?",
            (g.user["id"],),
        )["count"],
        "coin_balance": get_coin_balance(g.user["id"]),
    }
    return render_template("profile.html", stats=stats)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
