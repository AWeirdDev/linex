from typing import Any, Optional

import httpx

from .rate_limiting import RateLimit

rr_botInfo = RateLimit.other()
async def get_bot_info(headers: dict) -> dict:
    await rr_botInfo.call()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.line.me/v2/bot/info",
            headers=headers
        )
        return resp.json()


rr_getMemberCount = RateLimit.other()
async def get_group_member_count(headers: dict, group_id: str) -> dict:
    await rr_getMemberCount.call()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://api.line.me/v2/bot/group/{group_id}/members/count",
            headers=headers
        )
        return resp.json()

rr_getGroupChat = RateLimit.other()
async def get_group_chat_summary(
    client: httpx.AsyncClient,
    headers: dict,
    group_id: str
) -> dict[str, str]:
    await rr_getGroupChat.call()

    resp = await client.get(
        f"https://api.line.me/v2/bot/group/{group_id}/summary",
        headers=headers
    )

    return resp.json()

async def reply(
    client: httpx.AsyncClient,
    headers: dict,
    reply_token: str,
    messages: list[dict[str, Any]],
    notificationDisabled: bool
) -> dict:
    resp = await client.post(
        'https://api.line.me/v2/bot/message/reply',
        headers=headers,
        json={
            "replyToken": reply_token,
            "messages": messages,
            "notificationDisabled": notificationDisabled
        }
    )
    return resp.json()

rr_getUser = RateLimit.other()
async def get_user(
    client: httpx.AsyncClient,
    headers: dict,
    user_id: str
) -> dict[str, str]:
    await rr_getUser.call()

    resp = await client.get(
        f"https://api.line.me/v2/bot/profile/{user_id}",
        headers=headers
    )
    return resp.json()

async def get_location(
    location: str
) -> list[dict]:
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://nominatim.openstreetmap.org/search",
            params={
                "q": location,
                "format": "json"
            }
        )
        return resp.json()

rr_setWebhookEndpoint = RateLimit.webhook_endpoint()
async def set_webhook_endpoint(
    headers: dict,
    endpoint: str
) -> dict:
    await rr_setWebhookEndpoint.call()

    async with httpx.AsyncClient() as client:
        resp = await client.put(
            "https://api.line.me/v2/bot/channel/webhook/endpoint",
            headers=headers,
            json={
                "endpoint": endpoint
            }
        )
        return resp.json()

rr_getWebhook = RateLimit.webhook_endpoint()
async def get_webhook(
    headers: dict
) -> dict[str, str | bool]:
    await rr_getWebhook.call()

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.line.me/v2/bot/channel/webhook/endpoint",
            headers=headers
        )
        return resp.json()

rr_testWebhook = RateLimit.stats_and_broadcast()
async def test_webhook(
    headers: dict,
    endpoint: Optional[str] = None
) -> dict[str, bool | str]:
    await rr_testWebhook.call()

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.line.me/v2/bot/channel/webhook/test",
            headers=headers,
            json={
                "endpoint": endpoint,
            }
        )
        return resp.json()

async def get_file(
    headers: dict,
    client: httpx.AsyncClient,
    message_id: str
):
    url = f"https://api-data.line.me/v2/bot/message/{message_id}/content"

    resp = await client.get(url, headers=headers)

    if resp.status_code == 404:
        raise TypeError("(404) Unknown message ID.")
    elif resp.status_code == 410:
        raise TypeError(
            "(410) Message is gone. (usually caused by unsending)"
        )

    return resp
