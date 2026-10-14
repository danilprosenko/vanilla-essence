import a2s
import logging

logger = logging.getLogger(__name__)


class ServerOnline:
    """Данные о сервере: только онлайн и максимум"""

    def __init__(self, current_players=None, max_players=None, online=False):
        self.current_players = current_players
        self.max_players = max_players
        self.online = online


class A2SProvider:
    """Прямой опрос сервера DayZ через A2S"""

    def get_server_online(self, server_config):
        ip = server_config["ip"]
        port = int(server_config["steamQueryPort"])
        address = (ip, port)

        try:
            info = a2s.info(address, timeout=5.0)

            return ServerOnline(
                current_players=info.player_count,
                max_players=info.max_players,
                online=True
            )

        except Exception as e:
            logger.error("Сервер недоступен (%s:%s): %s", ip, port, e)
            return ServerOnline(online=False)


def get_provider(provider_type):
    """Фабрика провайдеров"""
    providers = {
        "A2S": A2SProvider(),
    }
    return providers.get(str(provider_type).upper(), A2SProvider())
