from datetime import date, datetime, timedelta
from db.client import get_client


# ──────────────────────────────── Users ────────────────────────────────

async def upsert_user(telegram_id: int, username: str | None) -> dict:
    db = get_client()
    res = db.table("users").upsert(
        {"telegram_id": telegram_id, "username": username},
        on_conflict="telegram_id",
    ).execute()
    return res.data[0]


async def get_user(telegram_id: int) -> dict | None:
    db = get_client()
    res = db.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return res.data[0] if res.data else None


async def update_reminder_time(telegram_id: int, reminder_time: str) -> None:
    db = get_client()
    db.table("users").update({"reminder_time": reminder_time}).eq("telegram_id", telegram_id).execute()


# ──────────────────────────────── Categories ────────────────────────────────

async def get_categories(user_id: int) -> list[dict]:
    db = get_client()
    res = db.table("categories").select("*").eq("user_id", user_id).execute()
    return res.data


async def create_category(user_id: int, name: str, emoji: str = "📌") -> dict:
    db = get_client()
    res = db.table("categories").insert(
        {"user_id": user_id, "name": name, "emoji": emoji}
    ).execute()
    return res.data[0]


async def delete_category(category_id: str, user_id: int) -> None:
    db = get_client()
    db.table("categories").delete().eq("id", category_id).eq("user_id", user_id).execute()


# ──────────────────────────────── Habits ────────────────────────────────

async def get_habits(user_id: int, active_only: bool = True) -> list[dict]:
    db = get_client()
    q = db.table("habits").select("*, categories(name, emoji)").eq("user_id", user_id)
    if active_only:
        q = q.eq("is_active", True)
    res = q.order("created_at").execute()
    return res.data


async def get_habit(habit_id: str, user_id: int) -> dict | None:
    db = get_client()
    res = (
        db.table("habits")
        .select("*, categories(name, emoji)")
        .eq("id", habit_id)
        .eq("user_id", user_id)
        .execute()
    )
    return res.data[0] if res.data else None


async def create_habit(
    user_id: int,
    name: str,
    habit_type: str,
    category_id: str | None = None,
    target_value: int | None = None,
    unit: str | None = None,
) -> dict:
    db = get_client()
    res = db.table("habits").insert({
        "user_id": user_id,
        "name": name,
        "type": habit_type,
        "category_id": category_id,
        "target_value": target_value,
        "unit": unit,
    }).execute()
    return res.data[0]


async def deactivate_habit(habit_id: str, user_id: int) -> None:
    db = get_client()
    db.table("habits").update({"is_active": False}).eq("id", habit_id).eq("user_id", user_id).execute()


# ──────────────────────────────── Habit logs ────────────────────────────────

async def get_today_logs(user_id: int) -> dict[str, dict]:
    """Returns {habit_id: log_record} for today."""
    db = get_client()
    today = date.today().isoformat()
    habits = await get_habits(user_id)
    if not habits:
        return {}
    habit_ids = [h["id"] for h in habits]
    res = (
        db.table("habit_logs")
        .select("*")
        .in_("habit_id", habit_ids)
        .eq("date", today)
        .execute()
    )
    return {row["habit_id"]: row for row in res.data}


async def toggle_boolean_log(habit_id: str, log_date: str | None = None) -> dict:
    db = get_client()
    log_date = log_date or date.today().isoformat()
    existing = db.table("habit_logs").select("*").eq("habit_id", habit_id).eq("date", log_date).execute()
    if existing.data:
        row = existing.data[0]
        new_done = not row["is_done"]
        res = db.table("habit_logs").update({"is_done": new_done}).eq("id", row["id"]).execute()
    else:
        res = db.table("habit_logs").insert(
            {"habit_id": habit_id, "date": log_date, "is_done": True, "value": 0}
        ).execute()
    return res.data[0]


async def set_counter_log(habit_id: str, value: int, log_date: str | None = None) -> dict:
    db = get_client()
    log_date = log_date or date.today().isoformat()
    existing = db.table("habit_logs").select("*").eq("habit_id", habit_id).eq("date", log_date).execute()
    is_done = value > 0
    if existing.data:
        res = db.table("habit_logs").update({"value": value, "is_done": is_done}).eq("id", existing.data[0]["id"]).execute()
    else:
        res = db.table("habit_logs").insert(
            {"habit_id": habit_id, "date": log_date, "is_done": is_done, "value": value}
        ).execute()
    return res.data[0]


# ──────────────────────────────── Statistics ────────────────────────────────

async def get_stats(user_id: int, days: int = 30) -> list[dict]:
    """Returns per-habit stats for the last N days."""
    db = get_client()
    habits = await get_habits(user_id)
    if not habits:
        return []

    since = (date.today() - timedelta(days=days - 1)).isoformat()
    habit_ids = [h["id"] for h in habits]
    logs_res = (
        db.table("habit_logs")
        .select("habit_id, date, is_done")
        .in_("habit_id", habit_ids)
        .gte("date", since)
        .execute()
    )
    logs_by_habit: dict[str, list[dict]] = {}
    for log in logs_res.data:
        logs_by_habit.setdefault(log["habit_id"], []).append(log)

    result = []
    for habit in habits:
        hid = habit["id"]
        logs = logs_by_habit.get(hid, [])
        done_count = sum(1 for l in logs if l["is_done"])
        pct = round(done_count / days * 100)
        streak = _calc_streak(logs)
        best_streak = _calc_best_streak(hid, db)
        result.append({
            "habit": habit,
            "done": done_count,
            "total": days,
            "pct": pct,
            "streak": streak,
            "best_streak": best_streak,
        })
    return result


def _calc_streak(logs: list[dict]) -> int:
    done_dates = {l["date"] for l in logs if l["is_done"]}
    streak = 0
    current = date.today()
    while current.isoformat() in done_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


def _calc_best_streak(habit_id: str, db) -> int:
    res = (
        db.table("habit_logs")
        .select("date, is_done")
        .eq("habit_id", habit_id)
        .eq("is_done", True)
        .order("date")
        .execute()
    )
    if not res.data:
        return 0
    dates = sorted(datetime.strptime(r["date"], "%Y-%m-%d").date() for r in res.data)
    best = current = 1
    for i in range(1, len(dates)):
        if (dates[i] - dates[i - 1]).days == 1:
            current += 1
            best = max(best, current)
        else:
            current = 1
    return best


# ──────────────────────────────── Reminder helpers ────────────────────────────────

async def get_all_users_for_reminder(reminder_time: str) -> list[dict]:
    """Returns users whose reminder_time matches HH:MM."""
    db = get_client()
    res = db.table("users").select("telegram_id").eq("reminder_time", reminder_time).execute()
    return res.data
