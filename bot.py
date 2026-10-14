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


# ---------- Токен ----------
TOKEN = os.environ.get("DISCORD_TOKEN") or discord_config.get("token")

if not TOKEN or TOKEN == "YOUR_BOT_TOKEN_HERE":
    raise ValueError("Не задан токен Discord. Укажите переменную окружения DISCORD_TOKEN.")


# ---------- Провайдер ----------
provider = get_provider(server_config.get("onlineProvider", "A2S"))


# ---------- Discord-клиент ----------
intents = discord.Intents.default()
bot = discord.Client(intents=intents)


# ---------- Формирование статуса ----------
def format_presence(server_online):
    if not server_online.online:
        return status_config["serverOfflineMessage"]

    players = server_online.current_players if server_online.current_players is not None else "?"
    max_players = server_online.max_players if server_online.max_players is not None else "?"

    message = status_config["message"]
    message = message.replace("${emoji.player}", emojis["player"])
    message = message.replace("${online}", str(players))
    message = message.replace("${max}", str(max_players))

    return message.strip()


def get_activity(status_text):
    activity_type = str(status_config.get("activityType", "PLAYING")).upper()

    if activity_type == "LISTENING":
        return discord.Activity(type=discord.ActivityType.listening, name=status_text)
    if activity_type == "WATCHING":
        return discord.Activity(type=discord.ActivityType.watching, name=status_text)
    if activity_type == "COMPETING":
        return discord.Activity(type=discord.ActivityType.competing, name=status_text)

    return discord.Game(name=status_text)


# ---------- Обновление ----------
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
