import os
import json
import logging

import discord
from discord.ext import tasks

from providers import get_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("dayz-bot")


# ---------- Загрузка конфига ----------
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

instance = config["instances"][0]
server_config = instance["server"]
discord_config = instance["discord"]
status_config = instance["status"]
emojis = instance["emojis"]
interval = int(instance["updater"]["intervalSeconds"])


# ---------- Токен из переменной окружения ----------
TOKEN = os.environ.get("DISCORD_TOKEN") or discord_config.get("token")

if not TOKEN:
    raise ValueError(
        "Не задан токен Discord. "
        "Укажите переменную окружения DISCORD_TOKEN "
        "или заполните поле discord.token в config.json."
    )


# ---------- Провайдер онлайна ----------
provider = get_provider(server_config.get("onlineProvider", "A2S"))


# ---------- Discord-клиент ----------
intents = discord.Intents.default()
bot = discord.Client(intents=intents)


# ---------- Вспомогательные функции ----------
def get_time_emoji(server_time):
    """Возвращает эмодзи дня или ночи по игровому времени"""
    try:
        hour = int(str(server_time).split(":")[0])
        if 6 <= hour < 20:
            return emojis["day"]
        return emojis["night"]
    except Exception:
        return emojis["day"]


def format_presence(server_online):
    """Формирует строку статуса по шаблону из конфига"""
    if not server_online.online:
        return status_config["serverOfflineMessage"]

    time_emoji = get_time_emoji(server_online.server_time)

    queue_block = ""
    if server_online.queue_active or status_config["showQueueIfNotActive"]:
        queue_block = status_config["queueBlock"]
        queue_block = queue_block.replace("${emoji.queue}", emojis["queue"])
        queue_block = queue_block.replace("${queue}", str(server_online.queue_size))

    message = status_config["message"]
    message = message.replace("${emoji.player}", emojis["player"])
    message = message.replace("${online}", str(server_online.current_players))
    message = message.replace("${max}", str(server_online.max_players))
    message = message.replace("${emoji.daytime}", time_emoji)
    message = message.replace("${time}", str(server_online.server_time))
    message = message.replace("${status.queueBlock}", queue_block)

    return message.strip()


def get_activity(status_text):
    """Преобразует строку конфига в объект Activity для discord.py"""
    activity_type = str(status_config.get("activityType", "PLAYING")).upper()

    if activity_type == "LISTENING":
        return discord.Activity(type=discord.ActivityType.listening, name=status_text)
    if activity_type == "WATCHING":
        return discord.Activity(type=discord.ActivityType.watching, name=status_text)
    if activity_type == "COMPETING":
        return discord.Activity(type=discord.ActivityType.competing, name=status_text)

    # По умолчанию — PLAYING
    return discord.Game(name=status_text)


# ---------- Периодическое обновление ----------
@tasks.loop(seconds=interval)
async def update_status():
    try:
        server_online = provider.get_server_online(server_config)
        presence_text = format_presence(server_online)
        activity = get_activity(presence_text)

        await bot.change_presence(activity=activity)
        logger.info("Статус обновлён: %s", presence_text)

    except Exception as e:
        logger.error("Ошибка обновления статуса: %s", e)


@update_status.before_loop
async def before_update_status():
    await bot.wait_until_ready()


# ---------- События ----------
@bot.event
async def on_ready():
    logger.info("Бот подключён как %s (id=%s)", bot.user, bot.user.id)
    if not update_status.is_running():
        update_status.start()


# ---------- Точка входа ----------
if __name__ == "__main__":
    bot.run(TOKEN)