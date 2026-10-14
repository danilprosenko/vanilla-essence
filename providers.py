import a2s
import logging

logger = logging.getLogger(__name__)


class ServerOnline:
    """Аналог ServerOnlineFun из Java"""

    def __init__(self, current_players=None, max_players=None, server_time=None,
                 queue_size=None, queue_active=False, online=False):
        self.current_players = current_players
        self.max_players = max_players
        self.server_time = server_time
        self.queue_size = queue_size
        self.queue_active = queue_active
        self.online = online


class A2SProvider:
    """Прямой опрос сервера DayZ по A2S (логика из A2SOnlineProvider.java)"""

    def get_server_online(self, server_config):
        ip = server_config["ip"]
        port = int(server_config["steamQueryPort"])
        address = (ip, port)

        try:
            info = a2s.info(address, timeout=5.0)

            server_time = None
            queue = None

            # Пробуем вытащить keywords — там DayZ хранит очередь и время
            try:
                rules = a2s.rules(address, timeout=5.0)

                # В Java это поле называется "keywords"
                keywords = rules.get("keywords", "")

                if keywords:
                    # В Java: s.split(",")
                    parts = keywords.split(",")

                    # Ищем очередь: строка начинается с "lqs"
                    for part in parts:
                        if part.startswith("lqs") and len(part) > 3:
                            queue = part[3:]
                            break

                    # Время — последний элемент списка
                    if parts:
                        server_time = parts[-1]

            except Exception as e:
                logger.debug("Не удалось получить rules: %s", e)

            return ServerOnline(
                current_players=info.player_count,
                max_players=info.max_players,
                server_time=server_time,
                queue_size=queue,
                queue_active=(queue is not None and queue != "0"),
                online=True
            )

        except Exception as e:
            logger.error("Сервер недоступен (%s:%s): %s", ip, port, e)
            return ServerOnline(online=False)


def get_provider(provider_type):
    """Фабрика провайдеров (аналог OnlineProviderFactory)"""
    providers = {
        "A2S": A2SProvider(),
    }
    return providers.get(str(provider_type).upper(), A2SProvider())
