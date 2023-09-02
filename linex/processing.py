from typing import Any, Union

import httpx

from .cache import MESSAGES
from .log import logger
from .models import (
    AccountLinkContext,
    AudioMessageContext,
    BeaconContext,
    DeviceLinkContext,
    DeviceUnlinkContext,
    FileMessageContext,
    FollowContext,
    ImageMessageContext,
    JoinContext,
    LeaveContext,
    LINEThingsScenarioExecutionContext,
    LocationMessageContext,
    MemberJoinContext,
    MemberLeaveContext,
    PostbackContext,
    StickerMessageContext,
    TextMessageContext,
    UnfollowContext,
    UnsendContext,
    VideoMessageContext,
    VideoViewingCompleteContext,
)


def add_to_cache(
    context: Union[
        TextMessageContext,
        ImageMessageContext,
        VideoMessageContext,
        AudioMessageContext,
        FileMessageContext,
        LocationMessageContext,
        StickerMessageContext
    ]
) -> None:
    """Adds a message context to the cache."""
    MESSAGES[context.id] = context

async def process(
    cls, 
    payload: dict, 
    client: httpx.AsyncClient, 
    headers: dict[str, str]
) -> None:
    """Process the webhook event payload.

    Args:
        cls (:obj:`Client`): A constructed (intiailized) client class.
        payload (dict): The webhook event payload sent from LINE.
        client (:obj:`AsyncClient`): The httpx async client.
        headers (dict of str: str): The headers.
    """
    events: list[dict] = payload['events']

    if not events:
        settings_link = f"https://manager.line.biz/account/{cls.user.basic_id}/setting/response"
        return logger.log(
            "[blue]Successfully verified![/blue] Next:\n"
            "1. Please flip the 'Use Webhook' switch!\n"
            "2. Turn off auto-reply messages.\n"
            "3. Turn off greeting messages.\n"
            "4. (optional) Allow bot to join group chats.\n\n"
            f"[link={settings_link}]✨ Open Settings[/link]"
        )

    args: tuple[httpx.AsyncClient, dict[str, str]] = (client, headers)

    def fulfill_pendings(name: str, context: Any):
        for item in list(cls.pending[name]):
            cls.pending[name][item] = context
    
    for event in events:
        if event['mode'] == 'standby' and cls.ignore_standby:
            continue

        if event['type'] == 'message':
            finder = {
                "text": TextMessageContext,
                "image": ImageMessageContext,
                "video": VideoMessageContext,
                "audio": AudioMessageContext,
                "file": FileMessageContext,
                "location": LocationMessageContext,
                "sticker": StickerMessageContext
            }
            _type = name = event['message']['type']
            context = finder[_type](event, *args)
            add_to_cache(context)

        elif event['type'] == 'unsend':
            name = "unsend"
            context = UnsendContext(event, *args)

        elif event['type'] == 'follow':
            name = "follow"
            context = FollowContext(event, *args)

        elif event['type'] == 'unfollow':
            name = "unfollow"
            context = UnfollowContext(event, *args)

        elif event['type'] == 'join':
            name = "join"
            context = JoinContext(event, *args)

        elif event['type'] == 'leave':
            name = "leave"
            context = LeaveContext(event, *args)

        elif event['type'] == 'memberJoined':
            name = "member_join"
            context = MemberJoinContext(event, *args)

        elif event['type'] == 'memberLeft':
            name = "member_leave"
            context = MemberLeaveContext(event, *args)

        elif event['type'] == 'postback':
            name = "postback"
            context = PostbackContext(event, *args)

        elif event['type'] == 'videoPlayComplete':
            name = "video_complete"
            VideoViewingCompleteContext(event, *args)

        elif event['type'] == 'beacon':
            name = "beacon"
            BeaconContext(event, *args)

        elif event['type'] == 'accountLink':
            name = "account_link"
            AccountLinkContext(event, *args)

        elif event['type'] == 'things':
            pre_context, name = {
                "link": (
                    DeviceLinkContext,
                    "device_link"
                ),
                "unlink": (
                    DeviceUnlinkContext,
                    "device_unlink"
                ),
                "scenarioResult": (
                    LINEThingsScenarioExecutionContext, 
                    "scenario_result"
                )
            }[event['things']['type']]
            context = pre_context(event, *args)

        else:
            raise TypeError(f"Unknown event type: {event['type']!r}")
        
        fulfill_pendings(name, context) # type: ignore

        await cls.emit(name, context) # type: ignore

