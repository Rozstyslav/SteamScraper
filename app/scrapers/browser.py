from threading import Lock

from selenium import webdriver
from selenium.common.exceptions import WebDriverException

from app.exceptions import BrowserOpenError


class VisibleSteamBrowser:
    def __init__(self) -> None:
        self._driver: webdriver.Chrome | None = None
        self._lock = Lock()

    def open(self, url: str) -> None:
        with self._lock:
            try:
                if self._driver is None:
                    options = webdriver.ChromeOptions()
                    options.add_argument("--start-maximized")
                    self._driver = webdriver.Chrome(options=options)
                self._driver.get(url)
            except WebDriverException as exc:
                self._close_unlocked()
                raise BrowserOpenError("Could not open the Chrome browser") from exc

    def close(self) -> None:
        with self._lock:
            self._close_unlocked()

    def _close_unlocked(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except WebDriverException:
                pass
            finally:
                self._driver = None

steam_browser = VisibleSteamBrowser()
