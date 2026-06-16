from __future__ import annotations

import asyncio
import re
import unicodedata
from datetime import date, datetime, time, timezone
from functools import lru_cache
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from app.integrations.api_football import ProviderMatchRecord, ProviderSyncBatch
from app.models.schema import CompetitionPhase, SyncProvider
from app.services.team_metadata import get_team_metadata_by_code

if TYPE_CHECKING:
    from playwright.async_api import Locator, Page

FIFA_URL = (
    "https://www.fifa.com/pt/tournaments/mens/worldcup/"
    "canadamexicousa2026/scores-fixtures?country=BR&wtw-filter=ALL"
)

BR_TZ = ZoneInfo("America/Sao_Paulo")

LIVE_TERMS = (
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
)

IGNORED_PATTERNS = (
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
)

MONTH_MAP = {
    "jan": 1,
    "janeiro": 1,
    "fev": 2,
    "fevereiro": 2,
    "mar": 3,
    "marco": 3,
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


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\xa0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n+", "\n", value)
    return value.strip()


def parse_lines(text: str) -> list[str]:
    return [clean_text(line) for line in text.splitlines() if clean_text(line)]


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).casefold()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def now_br() -> datetime:
    return datetime.now(BR_TZ).replace(microsecond=0)


def looks_like_score(value: str) -> bool:
    return bool(re.fullmatch(r"\d{1,2}", value.strip()))


def extract_score(lines: list[str]) -> dict[str, int | str | None]:
    numbers: list[int] = []
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


@lru_cache(maxsize=1)
def _team_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for code, metadata in get_team_metadata_by_code().items():
        lookup[normalize_text(code)] = code
        lookup[normalize_text(metadata.name)] = code
        if metadata.iso2:
            lookup[normalize_text(metadata.iso2)] = code
    lookup["brazil"] = "BRA"
    lookup["brasil"] = "BRA"
    lookup["mexico"] = "MEX"
    lookup["méxico"] = "MEX"
    lookup["south africa"] = "RSA"
    lookup["áfrica do sul"] = "RSA"
    return lookup


def lookup_team_code(name: str | None) -> str | None:
    if not name:
        return None
    normalized = normalize_text(name)
    lookup = _team_lookup()
    if normalized in lookup:
        return lookup[normalized]
    for team_name, code in lookup.items():
        if team_name and (team_name in normalized or normalized in team_name):
            return code
    return None


def get_team_tag(name: str | None) -> str | None:
    code = lookup_team_code(name)
    if code:
        return code
    if not name:
        return None
    clean = "".join(char for char in unicodedata.normalize("NFKD", name) if char.isalpha())
    return clean[:3].upper() if clean else None


def extract_possible_teams(lines: list[str]) -> list[dict[str, str | None]]:
    candidates: list[str] = []
    for line in lines:
        normalized = normalize_text(line)
        if any(re.search(pattern, normalized, flags=re.IGNORECASE) for pattern in IGNORED_PATTERNS):
            continue
        if len(line) > 50:
            continue
        if not re.search(r"[A-Za-zÀ-ÿ]", line):
            continue
        candidates.append(line)

    unique: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        key = normalize_text(item)
        if key in seen:
            continue
        unique.append(item)
        seen.add(key)
    teams = unique[:2]
    return [{"name": team, "tag": get_team_tag(team)} for team in teams]


def parse_match_datetime_from_lines(lines: list[str]) -> datetime | None:
    text = " ".join(lines)
    time_match = re.search(r"\b(\d{1,2}):(\d{2})\b", text)
    hour = int(time_match.group(1)) if time_match else 0
    minute = int(time_match.group(2)) if time_match else 0

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

    date_match = re.search(
        r"\b(\d{1,2})\s*(?:de\s*)?"
        r"(jan|janeiro|fev|fevereiro|mar|marco|março|abr|abril|mai|maio|jun|junho|jul|julho|ago|agosto|set|setembro|out|outubro|nov|novembro|dez|dezembro)"
        r"\s*(?:de\s*)?(\d{4})\b",
        text,
        flags=re.IGNORECASE,
    )
    if date_match:
        day = int(date_match.group(1))
        month_name = normalize_text(date_match.group(2))
        year = int(date_match.group(3))
        month = MONTH_MAP.get(month_name)
        if month is None:
            return None
        try:
            return datetime(year, month, day, hour, minute, tzinfo=BR_TZ)
        except ValueError:
            return None

    return None


def parse_match_date_header(text: str) -> date | None:
    normalized = normalize_text(text)
    match = re.search(
        r"\b(\d{1,2})\s*(?:de\s*)?"
        r"(jan|janeiro|fev|fevereiro|mar|marco|março|abr|abril|mai|maio|jun|junho|jul|julho|ago|agosto|set|setembro|out|outubro|nov|novembro|dez|dezembro)"
        r"\s*(?:de\s*)?(\d{4})\b",
        normalized,
        flags=re.IGNORECASE,
    )
    if match is None:
        return None
    day = int(match.group(1))
    month_name = match.group(2).lower()
    year = int(match.group(3))
    month = MONTH_MAP.get(month_name)
    if month is None:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def text_has_match_signal(text: str) -> bool:
    lower = text.lower()
    lines = parse_lines(text)
    if len(lines) < 2:
        return False
    if len(text) > 1500:
        return False
    negative_terms = (
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
    )
    if any(term in lower for term in negative_terms):
        return False
    positive_terms = ("ao vivo", "live", "ft", "fim", "encerrado", "intervalo", "grupo", "rodada", "match", "jogo")
    if any(term in lower for term in positive_terms):
        return True
    if re.search(r"\b\d{1,2}:\d{2}\b", text):
        return True
    if re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", text):
        return True
    known_team_names = [normalize_text(metadata.name) for metadata in get_team_metadata_by_code().values()]
    known_team_names.extend([
        "brazil",
        "brasil",
        "mexico",
        "south africa",
    ])
    if any(team_name in lower for team_name in known_team_names):
        return True
    short_text_lines = [line for line in lines if 1 <= len(line) <= 40 and re.search(r"[A-Za-zÀ-ÿ0-9]", line)]
    return len(short_text_lines) >= 3


async def accept_cookies_if_present(page: Page) -> None:
    for label in ("Aceitar todos", "Aceitar", "Accept all", "Accept", "Concordo", "OK"):
        try:
            button = page.get_by_role("button", name=re.compile(label, re.I))
            if await button.count() > 0:
                await button.first.click(timeout=2500)
                await page.wait_for_timeout(1000)
                return
        except Exception:
            continue


async def auto_scroll_until_loaded(page: Page, max_scrolls: int = 5) -> None:
    previous_height = 0
    for _ in range(max_scrolls):
        current_height = await page.evaluate("document.body.scrollHeight")
        if current_height == previous_height:
            break
        previous_height = current_height
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(1200)


async def get_candidate_cards(page: Page) -> list[Locator]:
    selectors = ["main section a[href]", "main a[href]"]
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


async def card_has_live_marker(card: Locator) -> bool:
    try:
        if await card.locator("svg ellipse").count() > 0:
            return True
    except Exception:
        pass
    try:
        text = normalize_text(clean_text(await card.inner_text(timeout=3000)))
        return any(term in text for term in LIVE_TERMS)
    except Exception:
        return False


def should_keep_match(
    *,
    index: int,
    is_live: bool,
    first_live_card_index: int | None,
    match_datetime: datetime | None,
    reference_datetime: datetime,
) -> tuple[bool, str]:
    if is_live:
        return True, "live"
    if first_live_card_index is not None and index <= first_live_card_index:
        return True, "before_or_at_first_live"
    if match_datetime is not None and match_datetime <= reference_datetime:
        return True, "datetime_lte_now"
    return False, "future_or_unknown"


async def _section_date_for_card(card: Locator) -> date | None:
    try:
        section_text = await card.evaluate(
            """(el) => {
                const section = el.closest('section');
                return section ? section.innerText : '';
            }"""
        )
    except Exception:
        return None
    lines = parse_lines(section_text or "")
    if not lines:
        return None
    return parse_match_date_header(lines[0])


async def scrape_recent_result_payloads(limit: int = 15, *, headless: bool = True) -> dict[str, Any]:
    from playwright.async_api import async_playwright

    reference_datetime = now_br()
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
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

        cards = await get_candidate_cards(page)
        first_live_card_index: int | None = None
        for index, card in enumerate(cards):
            if await card_has_live_marker(card):
                first_live_card_index = index
                break

        matches: list[dict[str, Any]] = []
        discarded_non_match = 0
        discarded_future_or_unknown = 0
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
                match_date = match_datetime.date() if match_datetime else await _section_date_for_card(card)
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
                        "page_index": index,
                        "index": index,
                        "first_live_card_index": first_live_card_index,
                        "keep_reason": keep_reason,
                        "is_live": is_live,
                        "href": href,
                        "match_date": match_date.isoformat() if match_date else None,
                        "match_datetime": match_datetime.isoformat() if match_datetime else None,
                        "teams": teams,
                        "result": score,
                        "raw_lines": lines,
                        "raw_text": text,
                    }
                )
            except Exception as exc:
                matches.append({"source": "fifa_scores_fixtures_page", "page_index": index, "index": index, "error": str(exc)})

        await browser.close()

        matches = sorted(matches, key=lambda item: item.get("page_index", item.get("index", 999999)))
        return {
            "url": FIFA_URL,
            "fetched_at_utc": utc_now_iso(),
            "reference_datetime_br": reference_datetime.isoformat(),
            "first_live_card_index": first_live_card_index,
            "cards_scanned": len(cards),
            "total_matches_returned": len(matches),
            "discarded_non_match": discarded_non_match,
            "discarded_future_or_unknown": discarded_future_or_unknown,
            "matches": matches[:limit],
        }


def _map_scraped_match(row: dict[str, Any]) -> ProviderMatchRecord | None:
    teams = row.get("teams")
    if not isinstance(teams, list) or len(teams) < 2:
        return None
    home_raw = teams[0] if isinstance(teams[0], dict) else {}
    away_raw = teams[1] if isinstance(teams[1], dict) else {}
    home_name = clean_text(str(home_raw.get("name") or "")) or None
    away_name = clean_text(str(away_raw.get("name") or "")) or None
    if home_name is None or away_name is None:
        return None

    result = row.get("result") if isinstance(row.get("result"), dict) else {}
    home_goals = result.get("home_goals")
    away_goals = result.get("away_goals")
    match_date_raw = row.get("match_date")
    match_datetime_raw = row.get("match_datetime")
    match_datetime: datetime | None = None
    if isinstance(match_datetime_raw, str) and match_datetime_raw:
        try:
            match_datetime = datetime.fromisoformat(match_datetime_raw)
        except ValueError:
            match_datetime = None
    match_date = None
    if isinstance(match_date_raw, str) and match_date_raw:
        try:
            match_date = date.fromisoformat(match_date_raw)
        except ValueError:
            match_date = None
    if match_datetime is None:
        if match_date is not None:
            match_datetime = datetime.combine(match_date, time.min, tzinfo=BR_TZ)
        else:
            match_datetime = datetime.now(BR_TZ)
    starts_at = match_datetime.astimezone(timezone.utc)
    home_code = lookup_team_code(home_name)
    away_code = lookup_team_code(away_name)
    external_id = parse_external_id(row.get("href")) or f"{normalize_text(home_name)}-{normalize_text(away_name)}-{match_date.isoformat() if match_date else 'unknown'}"
    winner_team_name = None
    if isinstance(home_goals, int) and isinstance(away_goals, int):
        if home_goals > away_goals:
            winner_team_name = home_name
        elif away_goals > home_goals:
            winner_team_name = away_name
    phase = parse_competition_phase(row.get("raw_lines", []))
    group_name = extract_group_name(row.get("raw_lines", [])) if isinstance(row.get("raw_lines"), list) else None
    status = parse_status(is_live=bool(row.get("is_live")), lines=row.get("raw_lines", []) if isinstance(row.get("raw_lines"), list) else [])
    return ProviderMatchRecord(
        provider=SyncProvider.THE_SPORTS_DB,
        external_id=external_id,
        starts_at=starts_at,
        status=status,
        phase=phase,
        stage_round=None,
        group_name=group_name,
        bracket_slot=None,
        venue=None,
        home_team_name=home_name,
        away_team_name=away_name,
        home_team_fifa_code=home_code,
        away_team_fifa_code=away_code,
        involves_brazil=is_brazil_match(home_name, away_name, home_code, away_code),
        official_home_goals=home_goals if isinstance(home_goals, int) else None,
        official_away_goals=away_goals if isinstance(away_goals, int) else None,
        winner_team_name=winner_team_name,
        source_payload=dict(row),
    )


def parse_external_id(href: str | None) -> str | None:
    if not href:
        return None
    match = re.search(r"/(\d+)(?:\?.*)?$", href)
    return match.group(1) if match else href.rsplit("/", 1)[-1]


def parse_competition_phase(lines: list[str]) -> CompetitionPhase:
    normalized = normalize_text(" ".join(lines))
    if "grupo " in normalized or "primeira fase" in normalized:
        return CompetitionPhase.GROUP_STAGE
    if "round of 32" in normalized or "16 avos" in normalized:
        return CompetitionPhase.ROUND_OF_32
    if "round of 16" in normalized or "oitavas" in normalized:
        return CompetitionPhase.ROUND_OF_16
    if "quarter" in normalized or "quartas" in normalized:
        return CompetitionPhase.QUARTER_FINAL
    if "semi" in normalized or "semifinal" in normalized:
        return CompetitionPhase.SEMI_FINAL
    if "third place" in normalized or "terceiro lugar" in normalized:
        return CompetitionPhase.THIRD_PLACE
    if "final" in normalized:
        return CompetitionPhase.FINAL
    return CompetitionPhase.GROUP_STAGE


def parse_status(*, is_live: bool, lines: list[str]) -> str:
    if is_live:
        return "LIVE"
    normalized = normalize_text(" ".join(lines))
    if "fim" in normalized or "final" in normalized or "encerrado" in normalized:
        return "FT"
    return "SCHEDULED"


def is_brazil_match(home_name: str | None, away_name: str | None, home_code: str | None, away_code: str | None) -> bool:
    values = {normalize_text(item) for item in (home_name, away_name, home_code, away_code) if item}
    return "bra" in values or "brasil" in values or "brazil" in values


def extract_group_name(lines: list[str]) -> str | None:
    text = " ".join(lines)
    match = re.search(r"grupo\s+([a-z])", text, flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


def sort_matches(matches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(matches, key=lambda item: item.get("page_index", item.get("index", 999999)))


def scrape_recent_results_batch(*, limit: int = 15, headless: bool = True) -> ProviderSyncBatch:
    payload = asyncio.run(scrape_recent_result_payloads(limit=limit, headless=headless))
    matches = tuple(
        match
        for row in payload.get("matches", [])
        if isinstance(row, dict)
        if (match := _map_scraped_match(row)) is not None
    )
    return ProviderSyncBatch(
        provider=SyncProvider.THE_SPORTS_DB,
        fetched_at=datetime.now(timezone.utc),
        matches=matches,
        top_scorers=(),
        metadata={
            "source": "FIFA_GAMEDAY",
            "url": payload.get("url", FIFA_URL),
            "cards_scanned": payload.get("cards_scanned", 0),
            "total_matches_returned": len(matches),
            "discarded_non_match": payload.get("discarded_non_match", 0),
            "discarded_future_or_unknown": payload.get("discarded_future_or_unknown", 0),
            "first_live_card_index": payload.get("first_live_card_index"),
        },
    )


class FifaGamedayClient:
    provider = SyncProvider.THE_SPORTS_DB
    configured = True

    def fetch_match_batch(
        self,
        *,
        fixture_ids: list[str] | tuple[str, ...] | None = None,
        include_top_scorers: bool = False,
    ) -> ProviderSyncBatch:
        del include_top_scorers
        try:
            batch = scrape_recent_results_batch(limit=15, headless=True)
            if fixture_ids:
                requested = {item for item in fixture_ids if item}
                filtered = tuple(match for match in batch.matches if match.external_id in requested)
                if filtered:
                    return ProviderSyncBatch(
                        provider=batch.provider,
                        fetched_at=batch.fetched_at,
                        matches=filtered,
                        top_scorers=(),
                        metadata={**batch.metadata, "requested_fixture_ids": list(requested)},
                    )
            return batch
        except Exception:
            from app.integrations.the_sports_db import TheSportsDBClient

            fallback_client = TheSportsDBClient()
            return fallback_client.fetch_match_batch(
                fixture_ids=fixture_ids,
                include_top_scorers=False,
            )
