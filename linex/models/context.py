# ruff: noqa: E501
from __future__ import annotations

import mimetypes as MT
import time
import uuid
from typing import Any, Literal, Optional

import httpx

from ..abc import AbstractLineMessage
from ..cache import GROUPS, USERS
from ..exceptions import CannotReply
from ..http import get_file, get_group_chat_summary, get_user, reply
from .emoji import Emoji
from .group import Group
from .mention import Mention
from .quick_reply import QuickReplyButton
from .sender import Sender
from .user import BotUser, User


class BaseContext:
    """Represents a base context.

    Args:
        data (dict of str: Any): The event data.
        _client (:obj:`AsyncClient`): Client.
    """
    __slots__ = (
        'event_type',
        '_event_id',
        '_is_redelivery',
        '_timestamp',
        '_source',
        '_reply_token',
        '_mode',
        'ping',
        'client',
        'headers',
    )
    event_type: str
    _event_id: str
    _is_redelivery: bool
    _timestamp: int
    _source: dict[str, str]
    _reply_token: Optional[str]
    _mode: Literal['active', 'standby']
    ping: float
    client: httpx.AsyncClient
    headers: dict[str, str]

    _author: Optional[User] = None
    _group: Optional[Group] = None

    def __init__(
        self,
        data: dict[str, Any],
        _client: httpx.AsyncClient,
        _headers: dict[str, str]
    ):
        self.event_type = data['type']
        self._event_id = data['webhookEventId']
        self._is_redelivery = data['deliveryContext']['isRedelivery']
        self._timestamp = (data['timestamp'] / 1000)
        self._source = data['source']
        self._reply_token = data.get('replyToken')
        self._mode = data['mode']
        self.ping = time.time() - self._timestamp
        self.client = _client
        self.headers = _headers

    @property
    def event_id(self) -> str:
        """The webhook event ID."""
        return self._event_id

    @property
    def is_redelivery(self) -> bool:
        """Whether this event is a webhook redelivery."""
        return self._is_redelivery

    @property
    def timestamp(self) -> int:
        """The timestamp.

        Could be used to calculate the ping.
        """
        return self._timestamp

    @property
    def source(self) -> dict[str, str]:
        """The message source.

        Could be a user, group chat, or multi-person chat.
        """
        return self._source

    @property
    def reply_token(self) -> Optional[str]:
        """The reply token.

        May not contain a reply token if ``mode`` is ``standby``
        """
        return self._reply_token

    @property
    def mode(self) -> Literal['active', 'standby']:
        """Channel state.

        * ``active``: The channel is active. You can send a reply message or
            push message, etc.
        * ``standby``: The channel is waiting for the
            `module <https://developers.line.biz/en/docs/partner-docs/module/>`_ to reply.
            At this point, you cannot reply the message.
        """
        return self._mode

    @property
    def is_active(self) -> bool:
        """A shortcut for detecting whether the current mode is active.

        Example:
            .. code-block :: python

                if not ctx.is_active:
                    return
        """
        return self.mode == "active"

    @property
    def source_type(self) -> Literal['user', 'group', 'room']:
        """Checks the chat (source) type."""
        return self._source['type'] # type: ignore

    async def author(self) -> User:
        """Fetches the author if not already.

        Otherwise, returns cached instead. (coroutine)
        """

        if not self._author:
            self._author = User(await get_user(self.client, self.headers, self.source['userId'])) # type: ignore
            USERS[self._author.id] = self._author

        return self._author

    user = author

    async def group(self) -> Group:
        """Fetches group information."""
        if self._source['type'] != "group":
            raise TypeError("This is not a group chat.")

        if not self._group:
            self._group = Group( # type: ignore
                await get_group_chat_summary(
                    self.client,
                    self.headers,
                    self._source['groupId']
                ),
                self.headers
            )
            GROUPS[self._group.id] = self._group

        return self._group

class RepliableContext(BaseContext):
    """A repliable context.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`BaseContext`.
    """
    replied: bool = False

    
    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)

    def _to_valid_message_objects(
        self, 
        messages: tuple[AbstractLineMessage | dict | str]
    ) -> list[dict]:
        """Converts the user-defined message objects to the valid ones.

        Args:
            messages (tuple of :obj:`AbstractLineMessage`): The messages.

        Returns:
            list of dict: List of valid dictionaries / JSON objects.
        """
        if (time.time() - self.timestamp) > 60 * 20:
            # 20mins had passed
            raise CannotReply("Cannnot reply to this message: 20mins had passed.")

        """Converts given messages to valid message objects."""
        collected = []
    
        for message in messages:
            if isinstance(message, str):
                text, emojis = Emoji.emoji_text_to_emojis(message)
                msg = {
                    "type": "text",
                    "text": text,
                    "emojis": emojis or None
                }
                collected.append(msg)

            elif isinstance(message, dict):
                collected.append(message)

            else:
                collected.append(message.to_json())

        return collected

    async def reply(
        self,
        *messages: str | Any,
        sender: Optional[Sender] = None,
        quick_replies: Optional[list[QuickReplyButton]] = None,
        notification_disabled: bool = False
    ):
        """Reply to the message.

        Could only used **once** for each message.

        Args:
            *messages (str | Any): The messages to send.
            sender (:obj:`Sender`, optional): The sender.
            quick_replies (list of :obj:`QuickReplyButton`, optional): List of
                quick reply buttons.
            notification_disabled (bool, optional): Whether to make this message
                silent or not. If ``True``, user will not receive the push
                notification for their device.
        """
        if not self.reply_token:
            raise TypeError("Reply error was not provided, check `ctx.state`.")

        if time.time() - self.timestamp > 60 * 20:
            raise CannotReply(
                "It's been more than 20 minutes since the event occurred; "
                "you cannot reply to this interaction anymore."
            )

        if self.replied:
            raise CannotReply("This interaction has already been replied.")

        valid_messages = self._to_valid_message_objects(messages)

        if quick_replies:
            valid_messages[-1] |= {
                "quickReply": {
                    "items": [item.to_json() for item in quick_replies]
                }
            }

        if sender:
            valid_messages[-1] |= {
                "sender": sender.to_json()
            }

        self.replied = True
        await reply(
            self.client, 
            self.headers, 
            self.reply_token, 
            valid_messages, 
            notification_disabled
        )

    send = respond = reply


class TextMessageContext(RepliableContext):
    """Represents a text message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        "_text",
        "_id",
        "_emojis",
        "_mentions"
    )
    _text: str
    _id: str
    _emojis: list[dict[str, str | int]]
    _mentions: list[dict[str, int | str]]
    
    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        msg = data['message']

        self._text = msg['text']
        self._id = msg['id']
        self._emojis = msg.get('emojis', [])
        self._mentions = msg.get('mention', {}).get('mentionees', [])

    @property
    def text(self) -> str:
        """The text content."""
        return self._text

    content = text

    @property
    def id(self) -> str:
        """The message ID."""
        return self._id

    @property
    def emojis(self) -> list[Emoji]:
        """List of emojis.

        May not be present.
        """
        return [
            Emoji(
                emoji['productId'], # type: ignore
                emoji['emojiId']    # type: ignore
            ) for emoji in self._emojis
        ]

    @property
    def text_with_emojis(self) -> str:
        """Returns text, but with the Linex LINE emoji format.

        For example:
        .. code-block ::
            [emoji id](product id)
        """
        emojis = []

        for emoji in self.emojis:
            data = emoji.to_json()
            emojis.append(data)
        
        return Emoji.fit_on_texts(self.text, emojis)

    @property
    def mentions(self) -> list[Mention]:
        """Returns a list of mentions in the message."""
        return [
            Mention(
                mention['type'],       # type: ignore
                user=mention.get('userId') # type: ignore
            ) for mention in self._mentions
        ]

    def mentioned(self, user: str | User | BotUser) -> bool:
        """Checks whether a user is mentioned in a message or not.

        Args:
            user (:obj:`BotUser` | :obj:`User` | str): The user to check for. Could be a user ID or object.
        """
        return Mention.includes_mention(
            self._mentions,
            user
        )

class ImageMessageContext(RepliableContext):
    """Represents an image message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_id',
        '_contentProvider',
        '_imageSet'
    )
    _id: str
    _contentProvider: dict[str, str]
    _imageSet: dict[str, str | int]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        msg = data['message']
        self._id = msg['id']
        self._contentProvider = msg['contentProvider']
        self._imageSet = msg.get('imageSet')

    @property
    def id(self) -> str:
        """The ID of the message."""
        return self._id

    @property
    def content_provider(self) -> dict[str, str]:
        """The content provider of the message.

        `Reference <https://developers.line.biz/en/reference/messaging-api/#wh-image>`_
        """
        return self._contentProvider

    @property
    def image_set(self) -> Optional[dict[str, str | int]]:
        """The image set.

        May be None.

        `Reference <https://developers.line.biz/en/reference/messaging-api/#wh-image>`_
        """
        return self._imageSet

    async def download(
        self, 
        fn: Optional[str] = None,
        *, 
        raise_if_external: bool = False,
        disable_string_parsing: bool = False
    ) -> str:
        """Downloads the file.

        .. note ::
            In the ``fn``, use ``${random}`` to use a random filename, ``${ext}``
            for the extension name (includes the dot).

        Args:
            fn (str, optional): The filename or path.
            raise_if_external (bool, optional): Whether to raise an exception
                if content is external. Default ``False``.
            disable_string_parsing (bool, optional): Whether to disable string parsing.
                See the note.

        Returns:
            str: The filename or path.
        """
        if self.content_provider['type'] == "line":
            resp = await get_file(
                self.headers,
                self.client,
                self.id
            )

        else:
            if raise_if_external:
                raise TypeError("Content if external.")

            resp = await self.client.get(
                self.content_provider['originalContentUrl']
            )

            if resp.status_code != 200:
                raise BaseException(
                    "This external resource cannot be reached."
                )

        extension = MT.guess_extension(resp.headers['Content-Type'])
        fn = fn or str(uuid.uuid4()) + (extension or "")

        if not disable_string_parsing:
            fn = fn\
                .replace("${random}", str(uuid.uuid4()))\
                .replace("${ext}", extension or "")

        with open(
            fn,
            'wb'
        ) as f:
            f.write(resp.content)

        return fn

class VideoMessageContext(RepliableContext):
    """Represents a video message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_id',
        '_contentProvider',
        '_duration'
    )
    _id: str
    _contentProvider: dict[str, str]
    _duration: Optional[int]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        msg = data['message']
        self._id = msg['id']
        self._contentProvider = msg['contentProvider']
        self._duration = msg.get('duration')

    @property
    def id(self) -> str:
        """The ID of the message."""
        return self._id

    @property
    def content_provider(self) -> dict[str, str]:
        """The content provider of the message.

        `Reference <https://developers.line.biz/en/reference/messaging-api/#wh-image>`_
        """
        return self._contentProvider

    @property
    def duration(self) -> Optional[int]:
        """Duration of the video file. (milliseconds).

        May not always include.
        """
        return self._duration

    async def download(
        self, 
        fn: Optional[str] = None,
        *, 
        raise_if_external: bool = False,
        disable_string_parsing: bool = False
    ) -> str:
        """Downloads the file.

        .. note ::
            In the ``fn``, use ``${random}`` to use a random filename, ``${ext}``
            for the extension name (includes the dot).

        Args:
            fn (str, optional): The filename or path.
            raise_if_external (bool, optional): Whether to raise an exception
                if content is external. Default ``False``.
            disable_string_parsing (bool, optional): Whether to disable string parsing.
                See the note.

        Returns:
            str: The filename or path.
        """
        if self.content_provider['type'] == "line":
            resp = await get_file(
                self.headers,
                self.client,
                self.id
            )

        else:
            if raise_if_external:
                raise TypeError("Content if external.")

            resp = await self.client.get(
                self.content_provider['originalContentUrl']
            )

            if resp.status_code != 200:
                raise BaseException(
                    "This external resource cannot be reached."
                )

        extension = MT.guess_extension(resp.headers['Content-Type'])
        fn = fn or str(uuid.uuid4()) + (extension or "")

        if not disable_string_parsing:
            fn = fn\
                .replace("${random}", str(uuid.uuid4()))\
                .replace("${ext}", extension or "")

        with open(
            fn,
            'wb'
        ) as f:
            f.write(resp.content)

        return fn


class AudioMessageContext(VideoMessageContext):
    """Represents an audio message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """

    @property
    def duration(self) -> Optional[int]:
        """Duration of the audio file. (milliseconds).

        May not always include.
        """
        return self._duration

class FileMessageContext(RepliableContext):
    """Represents a file message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        'fn',
        'fs',
    )
    fn: str
    fs: int
    _id: str

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        msg = data['message']
        self.fn = msg['fileName']
        self.fs = msg['fileSize']
        self._id = msg['id']

    @property
    def file_name(self) -> str:
        """The filename."""
        return self.fn

    name = filename = file_name

    @property
    def file_size(self) -> int:
        """The file size in bytes."""
        return self.fs

    @property
    def id(self) -> str:
        """The ID of the message."""
        return self._id

    async def download(
        self, 
        fn: Optional[str] = None,
        *, 
        disable_string_parsing: bool = False
    ) -> str:
        """Downloads the file.

        .. note ::
            In the ``fn``, use ``${random}`` to use a random filename, ``${ext}``
            for the extension name (includes the dot).

        Args:
            fn (str, optional): The filename or path.
            disable_string_parsing (bool, optional): Whether to disable string parsing.
                See the note.

        Returns:
            str: The filename or path.
        """
        resp = await get_file(
            self.headers,
            self.client,
            self.id
        )

        extension = MT.guess_extension(resp.headers['Content-Type'])
        fn = fn or str(uuid.uuid4()) + (extension or "")

        if not disable_string_parsing:
            fn = fn\
                .replace("${random}", str(uuid.uuid4()))\
                .replace("${ext}", extension or "")

        with open(
            fn,
            'wb'
        ) as f:
            f.write(resp.content)

        return fn

class LocationMessageContext(RepliableContext):
    """Represents a location message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_id',
        '_title',
        '_address',
        '_lat',
        '_lon'
    )
    _id: str
    _title: Optional[str]
    _address: Optional[str]
    _lat: float
    _lon: float

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        msg = data['message']
        self._id = msg['id']
        self._title = msg.get('title')
        self._address = msg.get('address')
        self._lat = msg['latitude']
        self._lon = msg['longitude']

    @property
    def id(self) -> str:
        """The ID of the message."""
        return self._id

    @property
    def title(self) -> Optional[str]:
        """The title.

        May not be present.
        """
        return self._title

    @property
    def address(self) -> Optional[str]:
        """The address.

        May not be present.
        """
        return self._address

    @property
    def latitude(self) -> float:
        """Latitude."""
        return self._lat

    @property
    def longitude(self) -> float:
        """Longitude."""
        return self._lon

    @property
    def gmap(self) -> str:
        """The location in Google Map."""
        return (
            "http://maps.google.com/maps"
            "?z=12" # zoom 12%
            "&t=m" # type: ('m') map
            f"&q=loc:{self.latitude}+{self.longitude}"
        )

    google_map = gmap

class StickerMessageContext(RepliableContext):
    """Represents a sticker message context.

    Args:
        data (dict of str: Any): The message event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_id',
        '_pi',
        '_si',
        '_rT',
        '_kw',
        '_text'
    )
    _id: str
    _pi: str
    _si: str
    _rT: Literal[
        'STATIC',
        'ANIMATION',
        'SOUND',
        'ANIMATION_SOUND',
        'POPUP',
        'POPUP_SOUND',
        'CUSTOM',
        'MESSAGE',
        #'NAME_TEXT',        (deprecated)
        #'PER_STICKER_TEXT'  (deprecated)
    ]
    _kw: Optional[list[str]]
    _text: Optional[str]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        msg = data['message']
        self._id = msg['id']
        self._pi = msg['packageId']
        self._si = msg['stickerId']
        self._rT = msg['stickerResourceType']
        self._kw = msg.get('keywords')
        self._text = msg.get('text')

    @property
    def id(self) -> str:
        """The ID of the message."""
        return self._id

    @property
    def package_id(self) -> str:
        """The package ID."""
        return self._pi

    @property
    def sticker_id(self) -> str:
        """The sticker ID."""
        return self._si

    @property
    def resource_type(self) -> Literal[
            'STATIC',
            'ANIMATION',
            'SOUND',
            'ANIMATION_SOUND',
            'POPUP',
            'POPUP_SOUND',
            'CUSTOM',
            'MESSAGE'
        ]:
        """The sticker resource type."""
        return self._rT

    type = sticker_resource_type = resource_type

    @property
    def keywords(self) -> Optional[list[str]]:
        """The keywords to describe the sticker."""
        return self._kw

    @property
    def text(self) -> Optional[str]:
        """The message text.

        Only available when ``type`` is ``MESSAGE``.
        """
        return self.text

class UnsendContext(BaseContext):
    """Represents a unsend event context.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`BaseContext`.
    """
    __slots__ = (
        '_id',
    )
    _id: str

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._id = data['unsend']['messageId']

    @property
    def id(self) -> str:
        """The unsent message ID."""
        return self._id

class FollowContext(RepliableContext):
    """Represents a follow event context when your LINE Official Account is added as a.

    friend (or unblocked).

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)

class UnfollowContext(BaseContext):
    """Event object for when your LINE Official Account is blocked.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`BaseContext`.
    """
    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)

class JoinContext(RepliableContext):
    """A join event is triggered at different times for group chats and multi-person chats.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)


class LeaveContext(BaseContext):
    """Event object for when a user removes your LINE Official Account from a group chat.

    or when your LINE Official Account leaves a group chat or multi-person chat.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`BaseContext`.
    """
    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)

class MemberJoinContext(RepliableContext):
    """Event object for when a user joins a group chat or multi-person chat that the.

    LINE Official Account is in.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_members',
    )
    _members: list[dict[str, str]]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._members = data['joined']['members']

    @property
    def members(self) -> list[dict[str, str]]:
        """Users who joined.

        Array of source user objects.
        """
        return self._members

class MemberLeaveContext(BaseContext):
    """Event object for when a user leaves a group chat or multi-person chat that the.

    LINE Official Account is in. (Cannot reply)

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`BaseContext`.
    """
    __slots__ = (
        '_members',
    )
    _members: list[dict[str, str]]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._members = data['joined']['members']

    @property
    def members(self) -> list[dict[str, str]]:
        """Users who joined.

        Array of source user objects.
        """
        return self._members

class PostbackContext(RepliableContext):
    """Event object for when a user joins a group chat or multi-person chat that the.

    LINE Official Account is in.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    _pb: dict[str, str | dict[str, str]]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._pb = data['postback']

    @property
    def postback(self) -> dict[str, str | dict[str, str]]:
        """The original postback object."""
        return self._pb

    @property
    def data(self) -> str:
        """The postback data (developer-defined custom ID)."""
        return self._pb['data'] # type: ignore

    custom_id = data

    @property
    def datetime(self) -> Optional[str]:
        """The datetime. Only valid when this is DatetimePicker-triggered."""
        return self._pb['params'].get('datetime')

    @property
    def newRichMenuAliasId(self) -> Optional[str]:
        """The new rich menu alias ID after tapping the action.

        Only valid when this is RichMenuSwitch-triggered.
        """
        return self._pb['params'].get('newRichMenuAliasId')

class VideoViewingCompleteContext(RepliableContext):
    """Event for when a user finishes viewing a video at least once with the specified.

    ``tracking_id`` sent by the LINE Official Account.

    .. note ::
        A video viewing complete event doesn't necessarily indicate the number of
        times a user has watched a video.
        Watching a video multiple times in a single session in a chat room doesn't
        result in a duplicate event. However, if you close the chat room and reopen
        it to watch the video again, the event may reoccur.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_tracking',
    )

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._tracking = data['videoPlayComplete']['trackingId']

    @property
    def tracking_id(self) -> str:
        """ID used to identify a video.

        Returns the same value as the one assigned
        to the video message.
        """
        return self._tracking

    custom_id = tracking_id


class BeaconContext(RepliableContext):
    """Event object for when a user enters the range of a LINE Beacon.

    You can reply to beacon events.

    `LINE Beacon <https://developers.line.biz/en/docs/messaging-api/using-beacons/>`_

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_beacon',
    )
    _beacon: dict[str, str]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._beacon = data['beacon']

    @property
    def hwid(self) -> str:
        """Hardware ID of the beacon that was detected."""
        return self._beacon['hwid']

    hardware_id = hwid

    @property
    def type(self) -> Literal['enter', 'banner', 'stay']:
        """Type of beacon event:

        * ``enter``: Entered beacon's reception range.
        * ``banner``: Tapped beacon banner.
        * ``stay``: The user is within the range of the beacon's reception.
                    This event is sent repeatedly at a minimum interval of 10 seconds.
        """
        return self._beacon['type']

    beacon_event_type = type

    @property
    def dm(self) -> Optional[str]:
        """Device message of beacon that was detected.

        This message consists of
        data generated by the beacon to send notifications to bot servers.

        Only included in webhook events from devices that support the
        "device message" property.
        """
        return self._beacon.get('dm')

    device_message = dm

class AccountLinkContext(RepliableContext):
    """Event object for when a user has linked their LINE account with a provider's.

    service account. You can reply to account link events.

    If the link token has expired or has already been used, no webhook event will
    be sent and the user will be shown an error.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_link',
    )
    _link: dict[str, str]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._link = data['link']

    @property
    def result(self) -> Literal['ok', 'failed']:
        """One of the following values to indicate whether linking the account.

        was successful or not:

        * ``ok``: Indicates linking the account was successful.
        * ``failed``: Indicates linking the account failed for any reason, such as due
            to a user impersonation.

        .. note ::
            You cannot reply to the user if linking the account has failed.
        """
        return self._link['result']

    @property
    def nounce(self) -> str:
        """Specified nonce (number used once) when verifying the user ID.

        For more information, see Generate a nonce and redirect the user to the LINE Platform in the Messaging API documentation.

        `Generate a nonce and redirect the user to the LINE Platform <https://developers.line.biz/en/docs/messaging-api/linking-accounts/#step-four-verifying-user-id>`_
        """
        return self._link['nounce']

class DeviceLinkContext(RepliableContext):
    """Indicates that a user linked a device with LINE.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_things',
    )
    _things: dict[str, str]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._things = data['things']

    @property
    def type(self) -> Literal['link']:
        return 'link'

    @property
    def device_id(self) -> str:
        return self._things['deviceId']

    id = device_id

class DeviceUnlinkContext(RepliableContext):
    """Indicates that a user unlinked a device with LINE.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_things',
    )
    _things: dict[str, str]

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._things = data['things']

    @property
    def type(self) -> Literal['unlink']:
        return 'unlink'

    @property
    def device_id(self) -> str:
        return self._things['deviceId']

    id = device_id

class LINEThingsScenarioExecutionContext(RepliableContext):
    """This event indicates that an automatic communication scenario has been executed.

    Rather than returning an aggregated result for a scenario set, an execution
        result is returned for each individual scenario.

    Args:
        data (dict of str: Any): The event data.
        *args: Arguments for :obj:`RepliableContext`.
    """
    __slots__ = (
        '_things',
        '_result'
    )
    _things: dict[str, str]
    _result: LINEThingsScenarioExecutionContext.Result

    class Result:
        """Represents the result of the scenario."""
        def __init__(self, things: dict[str, Any]):
            self.things = things

        @property
        def scenario_id(self) -> str:
            """Scenario ID executed."""
            return self.things['scenarioId']

        @property
        def revision(self) -> int:
            """Revision number of the scenario set containing the executed scenario."""
            return self.things['revision']

        @property
        def start_time(self) -> float:
            """Timestamp for when execution of scenario action started.

            (milliseconds, LINE app time)
            """
            return self.things['startTime'] / 1000

        @property
        def end_time(self) -> float:
            """Timestamp for when execution of scenario was completed/.

            (milliseconds, LINE app time)
            """
            return self.things['endTime'] / 1000

        @property
        def elapsed(self) -> float:
            """Elapsed time for execution."""
            return self.end_time - self.start_time

        @property
        def code(self) -> str:
            """The result code.

            `Result Code Definitions <https://developers.line.biz/en/reference/messaging-api/#things-result-resultcode>_`
            """
            return self.things['resultCode']

        result_code = code

        @property
        def error_reason(self) -> Optional[str]:
            """Error reason.

            Only included if ``result_code`` is ``gatt_error`` or ``runtime_error``.
            """
            return self.things.get('errorReason')

        @property
        def ble_notification_payload(self) -> Optional[str]:
            """Data contained in notification.

            The value is Base64-encoded binary data.

            Only included for scenarios where trigger type is ``BLE_NOTIFICATION``.
            """
            return self.things.get('bleNotificationPayload')

        @property
        def action_results(self) -> Optional[list[str, str]]:
            """Execution result of individual operations specified in action.

            Only included when ``result_code`` is ``success``.

            Note that an array of actions specified in a scenario has the following
            characteristics:

            * The actions defined in a scenario are performed sequentially, from top to
                bottom.
            * Each action produces some result when executed.
            * Even actions that do not generate data, such as SLEEP, return an execution
                result of type void.
            * The number of items in an action array may be 0.

            Therefore, ``action_results`` has the following properties:

            * The number of items in the array matches the number of actions defined in the scenario.
            * The order of execution results matches the order in which actions are performed.
                That is, in a scenario set with multiple ``GATT_READ`` actions, the results are returned in the order in which each individual ``GATT_READ`` action was performed.
            * If 0 actions are defined in the scenario, the number of items in ``action_results``
                will be 0.

            Example:
                Below shows an example of the ``action_results`` list.
                .. code-block :: json
                    {
                      "type": "binary",
                      "data": "/w=="
                    }
            """
            return self.things.get("actionResults")

    def __init__(
        self,
        data: dict[str, Any],
        *args
    ):
        super().__init__(data, *args)
        self._things = data['things']
        self._result = LINEThingsScenarioExecutionContext.Result(self._things['result'])

    @property
    def type(self) -> Literal['scenarioResult']:
        return 'scenarioResult'

    @property
    def device_id(self) -> str:
        return self._things['deviceId']

    @property
    def result(self) -> LINEThingsScenarioExecutionContext.Result:
        return self._result

    id = device_id
