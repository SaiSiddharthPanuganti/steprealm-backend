from datetime import datetime, timedelta

from app.auth.models import User

MANA_PER_TICK = 5
TICK_MINUTES = 10
MANA_CAP = 200
STEPS_PER_BONUS = 1000
BONUS_MANA_PER_CHUNK = 20
DAILY_BONUS_CAP = 200


def apply_passive_regen(user: User) -> bool:
    now = datetime.utcnow()

    if user.mana >= MANA_CAP:
        user.last_regen_time = now
        return True

    elapsed_seconds = (now - user.last_regen_time).total_seconds()
    ticks = int(elapsed_seconds // (TICK_MINUTES * 60))
    if ticks <= 0:
        return False

    regenerated = ticks * MANA_PER_TICK
    new_mana = min(MANA_CAP, user.mana + regenerated)

    user.mana = new_mana
    if new_mana >= MANA_CAP:
        user.last_regen_time = now
    else:
        user.last_regen_time = user.last_regen_time + timedelta(minutes=ticks * TICK_MINUTES)
    return True


def apply_step_bonus(user: User, step_delta: int) -> int:
    available_bonus = max(0, DAILY_BONUS_CAP - user.daily_mana_earned)
    available_mana_space = max(0, MANA_CAP - user.mana)
    potential_bonus = (step_delta // STEPS_PER_BONUS) * BONUS_MANA_PER_CHUNK

    bonus_to_award = min(potential_bonus, available_bonus, available_mana_space)
    if bonus_to_award <= 0:
        return 0

    user.mana += bonus_to_award
    user.daily_mana_earned += bonus_to_award
    return bonus_to_award
