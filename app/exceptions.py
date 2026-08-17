class GameNotFoundError(Exception):
    pass


class SteamUpstreamError(Exception):
    pass


class SteamTimeoutError(SteamUpstreamError):
    pass


class BrowserOpenError(Exception):
    pass
