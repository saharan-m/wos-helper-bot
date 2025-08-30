import hashlib
import time
import aiohttp
import logging

logger = logging.getLogger("discord-bot.api")

API_SECRET = "tB87#kPtkxqOS2"
PLAYER_API_URL = "https://wos-giftcode-api.centurygame.com/api/player"
# Redeem endpoint unknown or protected; left as placeholder
REDEEM_API_URL = "https://wos-giftcode.centurygame.com/redeem"  # placeholder

def _make_signature(fid: str):
    ts = str(int(time.time() * 1000))  # milliseconds
    form = f"fid={fid}&time={ts}"
    sign = hashlib.md5((form + API_SECRET).encode("utf-8")).hexdigest()
    return sign, ts

async def get_player_info(fid: str):
    """Async fetch of player info from CenturyGame API."""
    sign, ts = _make_signature(fid)
    payload = f"sign={sign}&fid={fid}&time={ts}"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(PLAYER_API_URL, headers=headers, data=payload, timeout=15) as resp:
                text = await resp.text()
                if resp.status != 200:
                    logger.error(f"Player API HTTP {resp.status}: {text}")
                    return {"error": f"HTTP {resp.status}", "raw": text}
                data = await resp.json()
                logger.info(f"API: fetched player {fid}: {data}")
                return data
        except Exception as e:
            logger.exception(f"Exception fetching player info for {fid}: {e}")
            return {"error": str(e)}

async def redeem_code(fid: str, code: str):
    """
    Placeholder async redeem function.
    Real redemption requires captcha solving and likely session tokens.
    Returns a dict with status/message to keep the flow consistent.
    """
    logger.info(f"redeem_code called for fid={fid} code={code}. Not implemented (captcha).")
    return {"status": "not_implemented", "message": "Redemption requires captcha. Manual or playwright required."}
