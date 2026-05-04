from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from db import queries

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message) -> None:
    stats = await queries.get_stats(message.from_user.id, days=30)
    if not stats:
        await message.answer("Нет данных. Сначала добавь привычки через /add и отмечай через /checkin")
        return

    lines = ["📊 Твоя статистика за 30 дней:\n"]

    streaks = [(s["habit"]["name"], s["streak"]) for s in stats if s["streak"] > 0]
    if streaks:
        lines.append("🔥 Стрики:")
        for name, streak in sorted(streaks, key=lambda x: -x[1]):
            lines.append(f"  • {name} — {streak} дн. подряд")
        lines.append("")

    lines.append("📈 Выполнение:")
    for s in sorted(stats, key=lambda x: -x["pct"]):
        bar = _progress_bar(s["pct"])
        lines.append(f"  • {s['habit']['name']} — {s['pct']}% ({s['done']}/{s['total']}) {bar}")

    best = max(stats, key=lambda x: x["best_streak"])
    if best["best_streak"] > 0:
        lines.append(f"\n🏆 Лучший стрик: {best['habit']['name']} — {best['best_streak']} дней")

    await message.answer("\n".join(lines))


def _progress_bar(pct: int) -> str:
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)
