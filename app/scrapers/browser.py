from threading import Lock

from selenium import webdriver
from selenium.common.exceptions import (
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.config import settings
from app.exceptions import BrowserOpenError
from app.models import GameDetailsResponse, GameReview


class VisibleSteamBrowser:
    def __init__(self) -> None:
        self._driver: webdriver.Chrome | None = None
        self._lock = Lock()

    def open(self, url: str) -> None:
        with self._lock:
            try:
                if self._driver is None:
                    options = webdriver.ChromeOptions()
                    if settings.browser_binary:
                        options.binary_location = settings.browser_binary
                    options.add_argument("--start-maximized")
                    options.add_argument(f"--lang={settings.browser_language}")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--no-sandbox")
                    self._driver = webdriver.Chrome(options=options)
                self._driver.get(url)
            except WebDriverException as exc:
                self._close_unlocked()
                raise BrowserOpenError("Could not open the Chrome browser") from exc

    def close(self) -> None:
        with self._lock:
            self._close_unlocked()

    def scrape_details(
        self, app_id: int, url: str, reviews_count: int) -> GameDetailsResponse:
        with self._lock:
            driver: webdriver.Chrome | None = None
            try:
                options = webdriver.ChromeOptions()
                if settings.browser_binary:
                    options.binary_location = settings.browser_binary
                if settings.browser_headless:
                    options.add_argument("--headless=new")
                options.add_argument(f"--lang={settings.browser_language}")
                options.add_argument(f"--window-size={settings.browser_window_size}")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument("--no-sandbox")
                options.add_experimental_option(
                    "prefs",
                    {"intl.accept_languages": settings.browser_accept_languages},
                )
                driver = webdriver.Chrome(options=options)
                driver.set_page_load_timeout(
                    settings.browser_page_load_timeout_seconds
                )
                page_url = (
                    f"{url}?l={settings.steam_language}&cc={settings.steam_country}"
                )
                driver.get(page_url)
                wait = WebDriverWait(driver, settings.browser_wait_timeout_seconds)

                if driver.find_elements(By.ID, "ageYear"):
                    year = driver.find_element(By.ID, "ageYear")
                    driver.execute_script(
                        "arguments[0].value=arguments[1]; "
                        "arguments[0].dispatchEvent(new Event('change'))",
                        year,
                        str(settings.browser_age_gate_year),
                    )
                    buttons = driver.find_elements(By.ID, "view_product_page_btn")
                    if buttons:
                        buttons[0].click()
                        wait.until(EC.presence_of_element_located((By.ID, "app_reviews_hash")))

                wait.until(EC.presence_of_element_located((By.ID, "app_reviews_hash")))
                reviews_anchor = driver.find_element(By.ID, "app_reviews_hash")
                driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'start'});", reviews_anchor
                )

                wait.until(
                    lambda current_driver: len(
                        self._review_cards(current_driver, app_id)
                    )
                    >= 3
                )
                initial_reviews = self._review_fingerprint(driver, app_id)

                recent_filter_selected = False
                for selector in (
                    "#review_context_recent",
                    "[data-reviews-filter='recent']",
                    "a[href*='browsefilter=mostrecent']",
                    "#review_recent",
                ):
                    controls = driver.find_elements(By.CSS_SELECTOR, selector)
                    if controls:
                        driver.execute_script("arguments[0].click();", controls[0])
                        if selector == "#review_context_recent":
                            wait.until(
                                lambda current_driver: current_driver.find_element(
                                    By.ID, "review_context_recent"
                                ).is_selected()
                            )
                        recent_filter_selected = True
                        break

                if recent_filter_selected:
                    wait.until(
                        lambda current_driver: self._reviews_changed(
                            current_driver, app_id, initial_reviews
                        )
                    )

                wait.until(
                    lambda current_driver: len(
                        self._review_cards(current_driver, app_id)
                    )
                    >= reviews_count
                )
                cards = self._review_cards(driver, app_id)[:reviews_count]
                reviews = [self._parse_review(card) for card in cards]

                name = self._text(driver, "#appHubAppName")
                if not name:
                    raise BrowserOpenError("Steam game page did not contain a title")
                price = self._first_text(
                    driver,".game_purchase_price, .discount_final_price, .game_area_dlc_price",
                )
                free_markers = driver.find_elements(
                    By.CSS_SELECTOR, ".btn_addtocart a[href*='install'], .game_area_purchase_game_wrapper"
                )
                is_free = bool(
                    price
                    and any(
                        word in price.casefold()
                        for word in ("безкоштов", "вільний доступ", "free")
                    )
                )
                if not price and free_markers:
                    purchase_text = " ".join(item.text for item in free_markers)
                    is_free = any(word in purchase_text.casefold() for word in ("безкоштов", "free"))

                return GameDetailsResponse(
                    app_id=app_id,
                    name=name,
                    url=driver.current_url.split("?", 1)[0],
                    developer=self._text(driver, "#developers_list"),
                    publisher=self._details_value(driver, "Видавець:", "Publisher:"),
                    release_date=self._first_text(driver, ".release_date .date"),
                    price=price,
                    is_free=is_free,
                    short_description=self._first_text(driver, ".game_description_snippet"),
                    user_score=self._first_text(
                        driver, ".user_reviews_summary_row .game_review_summary"
                    ),
                    reviews=reviews,
                )
            except TimeoutException as exc:
                raise BrowserOpenError(
                    f"Timed out waiting for {reviews_count} rendered Steam reviews"
                ) from exc
            except WebDriverException as exc:
                raise BrowserOpenError("Could not render the Steam game page") from exc
            finally:
                if driver is not None:
                    try:
                        driver.quit()
                    except WebDriverException:
                        pass

    @staticmethod
    def _reviews_changed(
        driver: webdriver.Chrome,
        app_id: int,
        initial_reviews: tuple[str, ...],) -> bool:
        try:
            return (
                VisibleSteamBrowser._review_fingerprint(driver, app_id)
                != initial_reviews
            )
        except StaleElementReferenceException:
            return False

    @staticmethod
    def _review_fingerprint(driver: webdriver.Chrome, app_id: int) -> tuple[str, ...]:
        return tuple(
            card.text.strip()[:500]
            for card in VisibleSteamBrowser._review_cards(driver, app_id)
        )

    @staticmethod
    def _review_cards(driver: webdriver.Chrome, app_id: int) -> list:
        legacy_cards = driver.find_elements(By.CSS_SELECTOR, ".apphub_Card")
        if legacy_cards:
            return legacy_cards
        return driver.execute_script(
            r"""
            const suffix = `/recommended/${arguments[0]}`;
            const seen = new Set();
            return [...document.querySelectorAll('#app_reviews_hash a[href]')]
                .filter(link => {
                    const href = link.href.replace(/\/$/, '');
                    const header = link.innerText.toLocaleLowerCase();
                    if (!link.offsetParent) return false;
                    if (!href.endsWith(suffix) || seen.has(href)) return false;
                    if (!header.includes('рекоменд') && !header.includes('recommend')) return false;
                    seen.add(href);
                    return true;
                })
                .map(link => link.parentElement);
            """,
            app_id,
        )

    @staticmethod
    def _text(driver: webdriver.Chrome, selector: str) -> str | None:
        elements = driver.find_elements(By.CSS_SELECTOR, selector)
        return elements[0].text.strip() if elements and elements[0].text.strip() else None

    @classmethod
    def _first_text(cls, driver: webdriver.Chrome, selector: str) -> str | None:
        for element in driver.find_elements(By.CSS_SELECTOR, selector):
            if element.text.strip():
                return element.text.strip()
        return None

    @staticmethod
    def _details_value(driver: webdriver.Chrome, *labels: str) -> str | None:
        for row in driver.find_elements(By.CSS_SELECTOR, ".details_block"):
            lines = [line.strip() for line in row.text.splitlines() if line.strip()]
            for index, line in enumerate(lines):
                for label in labels:
                    if line.casefold().startswith(label.casefold()):
                        value = line[len(label):].strip()
                        return value or (lines[index + 1] if index + 1 < len(lines) else None)
        return None

    @staticmethod
    def _parse_review(card) -> GameReview:
        def child_text(selector: str) -> str | None:
            children = card.find_elements(By.CSS_SELECTOR, selector)
            return children[0].text.strip() if children and children[0].text.strip() else None

        text = child_text(".apphub_CardTextContent")
        date = child_text(".date_posted")
        if text is None:
            lines = [line.strip() for line in card.text.splitlines() if line.strip()]
            title = lines[0] if lines else ""
            playtime = lines[1] if len(lines) > 1 else None
            date = lines[2] if len(lines) > 2 else ""
            body = lines[3:]
            for index, line in enumerate(body):
                if line.casefold().startswith(("чи була ця рецензія", "was this review")):
                    body = body[:index]
                    break
            return GameReview(
                text="\n".join(body),
                recommended=not any(
                    marker in title.casefold()
                    for marker in ("не рекоменд", "not recommended")
                ),
                published_at=date.removeprefix("ДОДАНО:").strip(),
                playtime=playtime,
            )

        date = date or ""
        for label in ("Опубліковано:", "Posted:"):
            date = date.removeprefix(label).strip()
        playtime = child_text(".hours")
        title = child_text(".title") or ""
        recommended = not any(
            marker in title.casefold()
            for marker in ("не рекоменд", "not recommended")
        )
        return GameReview(
            text=text,
            recommended=recommended,
            published_at=date,
            playtime=playtime,
        )

    def _close_unlocked(self) -> None:
        if self._driver is not None:
            try:
                self._driver.quit()
            except WebDriverException:
                pass
            finally:
                self._driver = None

steam_browser = VisibleSteamBrowser()
