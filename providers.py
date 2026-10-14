import a2s
from a2s import dayzquery
import logging

logger = logging.getLogger(__name__)


class ServerOnline:
    """Аналог ServerOnlineFun из Java-версии"""

    def __init__(self, current_players, max_players, server_time,
                 queue_size, queue_active, online):
        self.current_players = current_players
        self.max_players = max_players
        self.server_time = server_time
        self.queue_size = queue_size
        self.queue_active = queue_active
        self.online = online


class A2SProvider:
    """Прямой опрос сервера DayZ по протоколу Valve A2S"""

    def get_server_online(self, server_config):
        address = (server_config["ip"], int(server_config["steamQueryPort"]))

        try:
            info = a2s.info(address, timeout=5.0)

            server_time = "12:00"
            queue_size = 0
            queue_active = False

            try:
                rules = dayzquery.dayz_rules(address, timeout=5.0)

                if "dayz_time" in rules:
                    server_time = rules["dayz_time"]
                elif "time" in rules:
                    server_time = rules["time"]

                if "dayz_queue_size" in rules:
                    queue_size = int(rules["dayz_queue_size"])
                elif "queue_size" in rules:
                    queue_size = int(rules["queue_size"])

                if "dayz_queue_active" in rules:
                    queue_active = rules["dayz_queue_active"] == "1"
                elif "queue_active" in rules:
                    queue_active = rules["queue_active"] == "1"

            except Exception as e:
                logger.debug("Не удалось получить rules: %s", e)

            return ServerOnline(
                current_players=info.player_count,
                max_players=info.max_players,
                server_time=server_time,
                queue_size=queue_size,
                queue_active=queue_active,
                online=True
            )

        except Exception as e:
            logger.error("Сервер недоступен (%s:%s): %s",
                         server_config["ip"],
                         server_config["steamQueryPort"],
                         e)
            return ServerOnline(0, 0, "00:00", 0, False, False)


def get_provider(provider_type):
    """Фабрика провайдеров (аналог OnlineProviderFactory)"""
    providers = {
        "A2S": A2SProvider(),
    }
    return providers.get(str(provider_type).upper(), A2SProvider())