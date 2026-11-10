import asyncio
import re
import time

import aiohttp

import astrbot.api.message_components as Comp
from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .messages import text

API_URL = "https://animeapi.ai/api/generate"
MODELS = ("anime", "ultra", "ultra-max")
ORIENTATIONS = ("portrait", "square", "landscape")
MAX_PROMPT = 1000
COMMAND_RE = re.compile(r"^\s*/?\s*(?:animeapi|anime)\b\s*", re.IGNORECASE)


class AnimeAPIError(Exception):
    def __init__(self, message: str, status: int = 0, code: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.status = status
        self.code = code


class AnimeAPIPlugin(Star):
    """Anime image generation with AnimeAPI (https://animeapi.ai), $0.003 per image."""

    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self._last_use: dict[str, float] = {}
        self._in_flight: set[str] = set()

    def _text(self, key: str, **kwargs: object) -> str:
        return text(str(self.config.get("language", "zh")), key, **kwargs)

    @staticmethod
    def _parse(raw: str) -> tuple[str, str | None, str | None]:
        tokens = COMMAND_RE.sub("", raw, count=1).split()
        model = orientation = None
        while len(tokens) >= 2 and tokens[0] in ("-m", "--model", "-o", "--orientation"):
            if tokens[0] in ("-m", "--model"):
                model = tokens[1].lower()
            else:
                orientation = tokens[1].lower()
            tokens = tokens[2:]
        return " ".join(tokens).strip(), model, orientation

    async def _generate(self, prompt: str, model: str, orientation: str) -> dict:
        allow_nsfw = bool(self.config.get("allow_nsfw", False))
        payload = {
            "prompt": prompt,
            "model": model,
            "orientation": orientation,
            "enhance": bool(self.config.get("enhance", True)),
            "allowNSFW": allow_nsfw,
        }
        headers = {"Authorization": f"Bearer {str(self.config.get('api_key', '')).strip()}"}
        timeout = aiohttp.ClientTimeout(total=int(self.config.get("timeout", 120) or 120))
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            for attempt in (1, 2):
                try:
                    async with session.post(API_URL, json=payload, headers=headers) as res:
                        status = res.status
                        retry_after = res.headers.get("Retry-After", "3")
                        try:
                            data = await res.json(content_type=None)
                        except ValueError:
                            data = {}
                except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                    raise AnimeAPIError(str(exc) or exc.__class__.__name__, code="NETWORK") from exc
                if not isinstance(data, dict):
                    data = {}
                if 200 <= status < 300 and data.get("image_url"):
                    return data
                error = data.get("error")
                message = error if isinstance(error, str) else (error or {}).get("message") or f"HTTP {status}"
                if not allow_nsfw and "nsfw" in message.lower():
                    raise AnimeAPIError(message, status, "NSFW_BLOCKED")
                retryable = data.get("retryable") is True or status in (500, 503)
                if retryable and attempt == 1:
                    try:
                        wait = float(retry_after)
                    except ValueError:
                        wait = 3.0
                    await asyncio.sleep(min(wait, 10))
                    continue
                raise AnimeAPIError(message, status, data.get("code") or "")
        raise AnimeAPIError("unreachable")

    async def _download(self, url: str) -> bytes:
        timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
            async with session.get(url) as res:
                res.raise_for_status()
                return await res.read()

    @filter.command("anime", alias={"animeapi"})
    async def anime(self, event: AstrMessageEvent):
        """生成动漫图片 / Generate an anime image: /anime <描述 prompt>，可选 -o portrait|square|landscape、-m anime|ultra|ultra-max"""
        prompt, model_arg, orientation_arg = self._parse(event.message_str or "")

        if not prompt:
            yield event.plain_result(self._text("no_prompt"))
            return
        if len(prompt) > MAX_PROMPT:
            yield event.plain_result(self._text("too_long"))
            return
        if not str(self.config.get("api_key", "")).strip():
            yield event.plain_result(self._text("no_key"))
            return

        default_model = str(self.config.get("model", "anime"))
        model = default_model if default_model in MODELS else "anime"
        if model_arg:
            if model_arg not in MODELS:
                yield event.plain_result(self._text("bad_model"))
                return
            if not self.config.get("allow_model_override", False) and model_arg != model:
                yield event.plain_result(self._text("model_locked"))
                return
            model = model_arg
        default_orientation = str(self.config.get("orientation", "portrait"))
        orientation = default_orientation if default_orientation in ORIENTATIONS else "portrait"
        if orientation_arg:
            if orientation_arg not in ORIENTATIONS:
                yield event.plain_result(self._text("bad_orientation"))
                return
            orientation = orientation_arg

        user = f"{event.get_platform_name()}:{event.get_sender_id()}"
        if user in self._in_flight:
            yield event.plain_result(self._text("busy_user"))
            return
        cooldown = int(self.config.get("cooldown", 30) or 0)
        if cooldown > 0:
            wait = self._last_use.get(user, 0) + cooldown - time.monotonic()
            if wait > 0:
                yield event.plain_result(self._text("cooldown", seconds=int(wait) + 1))
                return

        self._in_flight.add(user)
        try:
            result = await self._generate(prompt, model, orientation)
        except AnimeAPIError as exc:
            logger.warning(f"AnimeAPI generation failed: {exc.status} {exc.code} {exc.message}")
            if exc.status == 402:
                reply = self._text("no_balance")
            elif exc.status == 401:
                reply = self._text("invalid_key")
            elif exc.code == "NSFW_BLOCKED":
                reply = self._text("blocked_nsfw")
            elif exc.code in ("MODERATION_BLOCKED", "PROVIDER_REJECTED"):
                reply = self._text("rejected", reason=exc.message)
            elif exc.status in (429, 503):
                reply = self._text("busy")
            elif exc.code == "NETWORK":
                reply = self._text("network")
            else:
                reply = self._text("failed", reason=exc.message)
            yield event.plain_result(reply)
            return
        finally:
            self._in_flight.discard(user)

        self._last_use[user] = time.monotonic()
        logger.info(
            f"AnimeAPI image for {user} in {result.get('generation_time_ms')}ms: {result['image_url']} "
            f"(balance ${float(result.get('balance_usd', 0)):.3f})"
        )

        try:
            image = Comp.Image.fromBytes(await self._download(result["image_url"]))
        except Exception as exc:  # the URL still works for platforms that fetch it themselves
            logger.warning(f"Could not download the AnimeAPI image, sending its URL instead: {exc!r}")
            image = Comp.Image.fromURL(result["image_url"])
        chain = [image]
        if self.config.get("show_prompt", False) and result.get("enhanced_prompt"):
            chain.append(Comp.Plain(result["enhanced_prompt"]))
        yield event.chain_result(chain)

    async def terminate(self):
        self._last_use.clear()
        self._in_flight.clear()
