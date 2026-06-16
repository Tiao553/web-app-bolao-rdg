from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone
from typing import Any
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright, Page, Locator


FIFA_URL = (
    "https://www.fifa.com/pt/tournaments/mens/worldcup/"
    "canadamexicousa2026/scores-fixtures?country=BR&wtw-filter=ALL"
)

USER_LIVE_XPATH = (
    "/html/body/div[1]/div/div[2]/div/main/div/div[1]/div/div/section/"
    "div/div[3]/div/div[5]/div/div[2]/a[4]/div/div[1]/div[2]/div/svg/ellipse"
)

BR_TZ = ZoneInfo("America/Sao_Paulo")

# Default: preserve page order and return games up to the live card.
# Change to True if you want live games first.
SORT_LIVE_FIRST = False


TEAM_TAGS = {
    "Brasil": "BRA",
    "Brazil": "BRA",
    "Argentina": "ARG",
    "França": "FRA",
    "France": "FRA",
    "Alemanha": "GER",
    "Germany": "GER",
    "Espanha": "ESP",
    "Spain": "ESP",
    "Portugal": "POR",
    "México": "MEX",
    "Mexico": "MEX",
    "Estados Unidos": "USA",
    "United States": "USA",
    "EUA": "USA",
    "Canadá": "CAN",
    "Canada": "CAN",
    "Inglaterra": "ENG",
    "England": "ENG",
    "Holanda": "NED",
    "Países Baixos": "NED",
    "Netherlands": "NED",
    "Uruguai": "URU",
    "Uruguay": "URU",
    "Bélgica": "BEL",
    "Belgium": "BEL",
    "Suíça": "SUI",
    "Switzerland": "SUI",
    "Japão": "JPN",
    "Japan": "JPN",
    "Arábia Saudita": "KSA",
    "Saudi Arabia": "KSA",
    "Irã": "IRN",
    "Iran": "IRN",
    "Austrália": "AUS",
    "Australia": "AUS",
    "Marrocos": "MAR",
    "Morocco": "MAR",
    "Croácia": "CRO",
    "Croatia": "CRO",
    "Tchéquia": "CZE",
    "Czech Republic": "CZE",
    "Czechia": "CZE",
    "Escócia": "SCO",
    "Scotland": "SCO",
    "Turquia": "TUR",
    "Turkey": "TUR",
    "Costa do Marfim": "CIV",
    "Ivory Coast": "CIV",
    "Equador": "ECU",
    "Ecuador": "ECU",
    "Suécia": "SWE",
    "Sweden": "SWE",
    "Tunísia": "TUN",
    "Tunisia": "TUN",
    "Cabo Verde": "CPV",
    "Cape Verde": "CPV",
    "Egito": "EGY",
    "Egypt": "EGY",
    "Nova Zelândia": "NZL",
    "New Zealand": "NZL",
    "Noruega": "NOR",
    "Norway": "NOR",
    "Áustria": "AUT",
    "Austria": "AUT",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_br() -> datetime:
    return datetime.now(BR_TZ).replace(microsecond=0)


def clean_text(value: str | None) -> str:
    if not value:
        return ""

    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n+", "\n", value)

    return value.strip()


def parse_lines(text: str) -> list[str]:
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def get_team_tag(name: str | None) -> str | None:
    if not name:
        return None

    if name in TEAM_TAGS:
        return TEAM_TAGS[name]

    clean = "".join(char for char in name.upper() if char.isalpha())

    return clean[:3] if clean else None


def looks_like_score(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,2}", value.strip()))


def extract_score(lines: list[str]) -> dict[str, int | str | None]:
    """
    Best-effort score extraction.

    FIFA cards often render scores as isolated numbers:
    Brazil
    1
    Switzerland
    0
    """

    numbers = []

    for line in lines:
        if looks_like_score(line):
            numbers.append(int(line))

    if len(numbers) >= 2:
        home_goals = numbers[0]
        away_goals = numbers[1]

        return {
            "home_goals": home_goals,
            "away_goals": away_goals,
            "score": f"{home_goals}x{away_goals}",
        }

    return {
        "home_goals": None,
        "away_goals": None,
        "score": None,
    }


def extract_possible_teams(lines: list[str]) -> list[dict[str, str | None]]:
    """
    Best-effort team extraction.

    Important:
    This should not be used to decide whether to keep pre-live cards.
    Some FIFA cards may not expose clean team text in the card itself.
    """

    ignored_patterns = [
        r"^\d{1,2}$",
        r"^\d{1,2}:\d{2}$",
        r"^\d{1,2}/\d{1,2}/\d{2,4}$",
        r"^ao vivo$",
        r"^live$",
        r"^ft$",
        r"^fim$",
        r"^encerrado$",
        r"^finalizado$",
        r"^intervalo$",
        r"^adiado$",
        r"^cancelado$",
        r"^grupo",
        r"^rodada",
        r"^jogo",
        r"^match",
        r"^tempo",
        r"^primeiro tempo$",
        r"^segundo tempo$",
        r"^1º tempo$",
        r"^2º tempo$",
        r"^fifa",
        r"^ingressos$",
        r"^notícias$",
        r"^vídeos$",
        r"^classificação$",
    ]

    candidates = []

    for line in lines:
        normalized = line.strip().lower()

        should_ignore = any(
            re.search(pattern, normalized, flags=re.IGNORECASE)
            for pattern in ignored_patterns
        )

        if should_ignore:
            continue

        if len(line) > 50:
            continue

        if not re.search(r"[A-Za-zÀ-ÿ]", line):
            continue

        candidates.append(line)

    unique = []
    seen = set()

    for item in candidates:
        key = item.lower()

        if key not in seen:
            unique.append(item)
            seen.add(key)

    teams = unique[:2]

    return [
        {
            "name": team,
            "tag": get_team_tag(team),
        }
        for team in teams
    ]


def parse_match_datetime_from_lines(lines: list[str]) -> datetime | None:
    """
    Attempts to parse datetime from card text.

    This is only a fallback because FIFA may place date headers outside cards.
    """

    text = " ".join(lines)

    month_map = {
        "jan": 1,
        "janeiro": 1,
        "fev": 2,
        "fevereiro": 2,
        "mar": 3,
        "março": 3,
        "abr": 4,
        "abril": 4,
        "mai": 5,
        "maio": 5,
        "jun": 6,
        "junho": 6,
        "jul": 7,
        "julho": 7,
        "ago": 8,
        "agosto": 8,
        "set": 9,
        "setembro": 9,
        "out": 10,
        "outubro": 10,
        "nov": 11,
        "novembro": 11,
        "dez": 12,
        "dezembro": 12,
    }

    time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    hour = int(time_match.group(1)) if time_match else 0
    minute = int(time_match.group(2)) if time_match else 0

    # 15/06/2026 or 15/06/26
    date_match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", text)

    if date_match:
        day = int(date_match.group(1))
        month = int(date_match.group(2))
        year = int(date_match.group(3))

        if year < 100:
            year += 2000

        try:
            return datetime(year, month, day, hour, minute, tzinfo=BR_TZ)
        except ValueError:
            return None

    # 15 JUN 2026 / 15 de junho de 2026
    date_match = re.search(
        r"\b(\d{1,2})\s*(?:de\s*)?"
        r"(jan|janeiro|fev|fevereiro|mar|março|abr|abril|mai|maio|jun|junho|jul|julho|ago|agosto|set|setembro|out|outubro|nov|novembro|dez|dezembro)"
        r"\s*(?:de\s*)?(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )

    if date_match:
        day = int(date_match.group(1))
        month_name = date_match.group(2).lower()
        year = int(date_match.group(3))
        month = month_map.get(month_name)

        if not month:
            return None

        try:
            return datetime(year, month, day, hour, minute, tzinfo=BR_TZ)
        except ValueError:
            return None

    return None


def text_has_match_signal(text: str) -> bool:
    """
    Keeps likely match cards and avoids navigation/footer links.

    This is intentionally permissive because pre-live cards may not parse cleanly.
    """

    lower = text.lower()
    lines = parse_lines(text)

    if len(lines) < 2:
        return False

    if len(text) > 1500:
        return False

    negative_terms = [
        "política de privacidade",
        "termos de serviço",
        "cookies",
        "fifa store",
        "inside fifa",
        "fifa+",
        "ingressos",
        "notícias",
        "vídeos",
        "ranking fifa",
        "classificação mundial",
    ]

    if any(term in lower for term in negative_terms):
        return False

    positive_terms = [
        "ao vivo",
        "live",
        "ft",
        "fim",
        "encerrado",
        "intervalo",
        "grupo",
        "rodada",
        "match",
        "jogo",
    ]

    if any(term in lower for term in positive_terms):
        return True

    if re.search(r"\b\d{1,2}:\d{2}\b", text):
        return True

    if re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text):
        return True

    # If any known team name appears in the card, it is probably useful.
    known_team_names = [name.lower() for name in TEAM_TAGS.keys()]

    if any(team_name in lower for team_name in known_team_names):
        return True

    # FIFA cards often have several short lines even when parsing is imperfect.
    short_text_lines = [
        line for line in lines
        if 1 <= len(line) <= 40 and re.search(r"[A-Za-zÀ-ÿ0-9]", line)
    ]

    return len(short_text_lines) >= 3


def should_keep_match(
    *,
    index: int,
    is_live: bool,
    first_live_card_index: int | None,
    match_datetime: datetime | None,
    reference_datetime: datetime,
) -> tuple[bool, str]:
    """
    Main rule:

    1. Keep live cards.
    2. If a live card exists, keep all valid match cards before it or at it.
    3. If no live card exists, keep cards with datetime <= now.
    """

    if is_live:
        return True, "live"

    if first_live_card_index is not None and index <= first_live_card_index:
        return True, "before_or_at_first_live"

    if match_datetime is not None and match_datetime <= reference_datetime:
        return True, "datetime_lte_now"

    return False, "future_or_unknown"


def sort_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not SORT_LIVE_FIRST:
        return sorted(matches, key=lambda item: item.get("index", 999999))

    def sort_key(match: dict[str, Any]) -> tuple[int, int, datetime]:
        is_live_priority = 1 if match.get("is_live") else 0

        keep_reason_priority = {
            "live": 3,
            "before_or_at_first_live": 2,
            "datetime_lte_now": 1,
        }.get(match.get("keep_reason"), 0)

        match_datetime_raw = match.get("match_datetime")

        if match_datetime_raw:
            try:
                match_datetime = datetime.fromisoformat(match_datetime_raw)
            except ValueError:
                match_datetime = datetime.min.replace(tzinfo=BR_TZ)
        else:
            match_datetime = datetime.min.replace(tzinfo=BR_TZ)

        return is_live_priority, keep_reason_priority, match_datetime

    return sorted(matches, key=sort_key, reverse=True)


async def accept_cookies_if_present(page: Page) -> None:
    possible_buttons = [
        "Aceitar todos",
        "Aceitar",
        "Accept all",
        "Accept",
        "Concordo",
        "OK",
    ]

    for label in possible_buttons:
        try:
            button = page.get_by_role("button", name=re.compile(label, re.I))

            if await button.count() > 0:
                await button.first.click(timeout=2500)
                await page.wait_for_timeout(1000)
                return

        except Exception:
            pass


async def auto_scroll_until_loaded(page: Page, max_scrolls: int = 5) -> None:
    """
    Loads lazy-rendered cards.

    Kept moderate to avoid reading too much.
    """

    previous_height = 0

    for _ in range(max_scrolls):
        current_height = await page.evaluate("document.body.scrollHeight")

        if current_height == previous_height:
            break

        previous_height = current_height

        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1200)


async def has_user_xpath_live_marker(page: Page) -> bool:
    try:
        locator = page.locator(f"xpath={USER_LIVE_XPATH}")
        return await locator.count() > 0
    except Exception:
        return False


async def card_has_live_marker(card: Locator) -> bool:
    """
    Detects live status by:
    1. SVG ellipse inside the card.
    2. Live-related text.
    """

    try:
        ellipse_count = await card.locator("svg ellipse").count()

        if ellipse_count > 0:
            return True

    except Exception:
        pass

    try:
        text = clean_text(await card.inner_text(timeout=3000)).lower()

        live_terms = [
            "ao vivo",
            "live",
            "1º tempo",
            "2º tempo",
            "primeiro tempo",
            "segundo tempo",
            "intervalo",
            "half-time",
            "first half",
            "second half",
        ]

        return any(term in text for term in live_terms)

    except Exception:
        return False


async def get_candidate_cards(page: Page) -> list[Locator]:
    """
    Important correction:
    The previous version stopped at the first selector that returned cards.
    That could return only live cards.

    This version reads broader candidates and de-duplicates them.
    """

    selectors = [
        "main section a[href]",
        "main a[href]",
    ]

    candidates: list[Locator] = []
    seen_keys: set[str] = set()

    for selector in selectors:
        locator = page.locator(selector)
        count = await locator.count()

        for index in range(count):
            card = locator.nth(index)

            try:
                text = clean_text(await card.inner_text(timeout=1500))
                href = await card.get_attribute("href")

                if not text_has_match_signal(text):
                    continue

                key = f"{href or ''}::{text[:250]}"

                if key in seen_keys:
                    continue

                seen_keys.add(key)
                candidates.append(card)

            except Exception:
                continue

    return candidates


async def find_first_live_card_index(cards: list[Locator]) -> int | None:
    for index, card in enumerate(cards):
        try:
            if await card_has_live_marker(card):
                return index
        except Exception:
            continue

    return None


async def scrape_fifa_matches(headless: bool = True) -> dict[str, Any]:
    reference_datetime = now_br()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )

        context = await browser.new_context(
            locale="pt-BR",
            timezone_id="America/Sao_Paulo",
            viewport={"width": 1440, "height": 1200},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )

        page = await context.new_page()

        await page.goto(FIFA_URL, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        await accept_cookies_if_present(page)

        await page.locator("main").wait_for(timeout=30000)

        await auto_scroll_until_loaded(page)

        user_xpath_live = await has_user_xpath_live_marker(page)

        cards = await get_candidate_cards(page)

        first_live_card_index = await find_first_live_card_index(cards)

        matches: list[dict[str, Any]] = []
        discarded_future_or_unknown = 0
        discarded_non_match = 0

        for index, card in enumerate(cards):
            try:
                text = clean_text(await card.inner_text(timeout=3000))
                lines = parse_lines(text)

                href = await card.get_attribute("href")

                if href and href.startswith("/"):
                    href = f"https://www.fifa.com{href}"

                is_live = await card_has_live_marker(card)
                score = extract_score(lines)
                teams = extract_possible_teams(lines)
                match_datetime = parse_match_datetime_from_lines(lines)

                # Do not drop pre-live cards because teams/score failed.
                # Only drop cards that do not look like match cards at all.
                if not text_has_match_signal(text):
                    discarded_non_match += 1
                    continue

                keep, keep_reason = should_keep_match(
                    index=index,
                    is_live=is_live,
                    first_live_card_index=first_live_card_index,
                    match_datetime=match_datetime,
                    reference_datetime=reference_datetime,
                )

                if not keep:
                    discarded_future_or_unknown += 1
                    continue

                matches.append(
                    {
                        "source": "fifa_scores_fixtures_page",
                        "index": index,
                        "first_live_card_index": first_live_card_index,
                        "keep_reason": keep_reason,
                        "is_live": is_live,
                        "href": href,
                        "match_datetime": (
                            match_datetime.isoformat()
                            if match_datetime
                            else None
                        ),
                        "teams": teams,
                        "result": score,
                        "raw_lines": lines,
                        "raw_text": text,
                    }
                )

            except Exception as exc:
                matches.append(
                    {
                        "source": "fifa_scores_fixtures_page",
                        "index": index,
                        "error": str(exc),
                    }
                )

        await browser.close()

        matches = sort_matches(matches)

        return {
            "url": FIFA_URL,
            "fetched_at_utc": utc_now_iso(),
            "reference_datetime_br": reference_datetime.isoformat(),
            "filter_rule": (
                "keep if is_live == true OR card_index <= first_live_card_index "
                "OR match_datetime <= reference_datetime_br"
            ),
            "sort_mode": "page_order" if not SORT_LIVE_FIRST else "live_first",
            "user_xpath_live_marker_found": user_xpath_live,
            "first_live_card_index": first_live_card_index,
            "cards_scanned": len(cards),
            "total_matches_returned": len(matches),
            "live_matches_found": sum(1 for item in matches if item.get("is_live")),
            "discarded_non_match": discarded_non_match,
            "discarded_future_or_unknown": discarded_future_or_unknown,
            "matches": matches,
        }


async def main() -> None:
    data = await scrape_fifa_matches(headless=True)
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())