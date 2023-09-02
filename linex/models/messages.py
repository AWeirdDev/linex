# ruff: noqa: SIM102

from __future__ import annotations

from typing import Any, Literal, Optional

from ..abc import AbstractLineAction, AbstractLineMessage
from ..exceptions import NotFound
from ..http import get_location
from .emoji import Emoji


class Text(AbstractLineMessage):
    """Represents a text message object.

    .. note ::
        To use quick replies, please add it to ``ctx.reply``.

    Args:
        text (str): The text (max 2000 chars).
            To add emojis, use ``[emoji id](product id)`` in-text.
        render_emojis (bool, optional): Whether to render the emojis from text or not.
    """
    __slots__ = (
        "_text",
        "_emojis"
    )
    _text: str
    _emojis: list[dict[str, Any]]

    def __init__(
        self,
        text: str,
        *,
        render_emojis: bool = True
    ):
        emojis = []

        if render_emojis:
            text, emojis = Emoji.emoji_text_to_emojis(text)

        self._text = text
        self._emojis = emojis

    def to_json(self) -> dict[str, Any]:
        """Converts to a valid JSON payload."""
        return {
            "type": "text",
            "text": self._text,
            "emojis": self._emojis or None
        }

class Sticker(AbstractLineMessage):
    """Represents a sticker message object.

    .. note ::
        1. To use quick replies, please add it to ``ctx.reply``.
        2. `All Stickers <https://developers.line.biz/en/docs/messaging-api/sticker-list/>`_

    Args:
        package_id (str): The package ID.
        sticker_id (str): The sticker ID.
    """
    __slots__ = (
        "_pid",
        "_sid"
    )
    _pid: str
    _sid: str

    def __init__(
        self,
        package_id: str,
        sticker_id: str
    ):
        self._pid = package_id
        self._sid = sticker_id

    def to_json(self) -> dict[str, str]:
        """Converts to a valid JSON payload."""
        return {
            "type": "sticker",
            "packageId": self._pid,
            "stickerId": self._sid
        }

class Image(AbstractLineMessage):
    """Represents an image message object.

    .. note ::
        To use quick replies, please add it to ``ctx.reply``.

    Args:
        original_content_url (str): Image URL (Max character limit: 2000)
            HTTPS over TLS 1.2 or later
            JPEG or PNG
            Max file size: 10 MB
            The URL should be percent-encoded using UTF-8.
        preview_content_url(str, optional): Preview image (Max character limit: 2000)
            If not given, uses ``original_content_url`` instead.
            HTTPS over TLS 1.2 or later
            JPEG or PNG
            Max file size: 1 MB
    """
    __slots__ = (
        "original",
        "preview"
    )
    original: str
    preview: str
    
    def __init__(
        self,
        original_content_url: str,
        preview_content_url: Optional[str] = None
    ):
        self.original = original_content_url
        self.preview = preview_content_url or original_content_url

    def to_json(self):
        """Converts to a valid JSON payload."""
        return {
            "type": "image",
            "originalContentUrl": self.original,
            "previewContentUrl": self.preview
        }

class Video(AbstractLineMessage):
    """Represents a video message object.

    .. note ::
        **Video aspect ratio**

        * A very wide or tall video may be cropped when played in some environments.
        * The aspect ratio of the video specified in ``originalContentUrl`` and the
            preview image specified in ``previewImageUrl`` should be the same.
            If the aspect ratio is different, a preview image will appear behind
            the video.

        .. image :: https://developers.line.biz/assets/img/image-overlapping-en.0e89fa18.png
            :alt: Aspect Ratio

    Args:
        original_content_url (str): URL of video file (Max character limit: 2000)
            HTTPS over TLS 1.2 or later
            mp4
            Max file size: 200 MB
        preview_image_url (str): URL of preview image (Max character limit: 2000)
            HTTPS over TLS 1.2 or later
            JPEG or PNG
            Max file size: 1 MB
        tracking_id (str, optional): ID used to identify the video when Video viewing
            complete event occurs. If you send a video message with ``tracking_id``, the
            video viewing complete event occurs when the user finishes watching.
            You can use the same ID in multiple messages.
            Max character limit: 100
            Supported character types: Half-width alphanumeric characters
            (a-z, A-Z, 0-9) and symbols ``(-.=,+*()%$&;:@{}!?<>[])``
            **You can't use the this in messages for group / multi-person chats,
            or audience match.**

    Raises:
        ValueError: One character from tracking_id is not supported, or too long.
        Raises only when ``tracking_id`` is not ``None``.
    """
    __slots__ = (
        "original",
        "preview",
        "tracking"
    )
    original: str
    preview: str
    tracking: Optional[str]

    def __init__(
        self,
        original_content_url: str,
        preview_image_url: str,
        tracking_id: Optional[str] = None
    ):
        valids: str = "(-.=,+*()%$&;:@{}!?<>[])"

        self.original = original_content_url
        self.preview = preview_image_url

        if tracking_id is not None:
            if any(char not in valids for char in tracking_id):
                raise ValueError(
                    f"One character from {tracking_id!r}is not in {valids}."
                )
            if len(tracking_id) > 100:
                raise ValueError("tracking_id is too long (max 100 chars)")
    
        self.tracking = tracking_id

    def to_json(self):
        """Converts to a valid JSON payload."""
        return {
            "type": "video",
            "originalContentUrl": self.original,
            "previewImageUrl": self.preview,
            "trackingId": self.tracking
        }

class Audio(AbstractLineMessage):
    """Represents an audio message object.

    .. note ::
        Only M4A files are supported on the Messaging API.
        If a service only supports MP3 files, you can use converters like FFmpeg.

    Args:
        original_content_url (str): URL of audio file (Max character limit: 2000)
            HTTPS over TLS 1.2 or later
            m4a
            Max file size: 200 MB
        duration (int): Length of audio file (milliseconds).
    """
    __slots__ = (
        "original",
        "duration"
    )
    original: str
    duration: int

    def __init__(
        self,
        original_content_url: str,
        duration: int
    ):
        self.original = original_content_url
        self.duration = duration

    def to_json(self):
        return {
            "type": "audio",
            "originalContentUrl": self.original,
            "duration": self.duration
        }

class Location(AbstractLineMessage):
    """Represents a location message object.

    .. note ::
        Use ``Location.from_name`` to instantly get a location from its name.
        (coroutine)

    Args:
        title (str): The title. Max 100 chars.
        address (str): The address. Max 100 chars. example:
            ``1-6-1 Yotsuya, Shinjuku-ku, Tokyo, 160-0004, Japan``
        latitude (float): The latitude. (e.g., ``35.687574``)
        longitude (float): The longitude. (e.g., ``139.72922``)
    """
    __slots__ = (
        "title",
        "address",
        "latitude",
        "longitude"
    )
    title: str
    address: str
    latitude: float
    longitude: float

    def __init__(
        self,
        title: str,
        address: str,
        latitude: float,
        longitude: float
    ):
        if len(title) > 100:
            raise ValueError("title is too long. (max 100 chars)")
        elif len(address) > 100:
            raise ValueError("address is too long. (max 100 chars)")

        self.title = title
        self.address = address
        self.latitude = latitude
        self.longitude = longitude

    def to_json(self):
        """Converts to a valid JSON payload."""
        return {
          "type": "location",
          "title": self.title,
          "address": self.address,
          "latitude": self.latitude,
          "longitude": self.longitude
        }

    @staticmethod
    async def from_name(
        name: str
    ) -> Location:
        """Gets a location from its name.

        (coroutine)

        Special thanks to `openstreetmap <https://openstreetmap.org>`_!

        Args:
            name (str): The location name. (e.g., ``Berlin``)
        """
        data: list[dict] = await get_location(name)

        if not data:
            raise NotFound(f"Location not found: {name!r}")

        place: dict = data[0]

        return Location(
            title=place['name'],
            address=place['display_name'],
            latitude=place['lat'],
            longitude=place['lon']
        )

class Imagemap(AbstractLineMessage):
    """Represents an imagemap message object.

    Use with JSON.

    .. note ::
        `Reference <https://developers.line.biz/en/reference/messaging-api/#imagemap-message>`_

    Args:
        base_url (str): Base URL of the image
            Max character limit: 2000
            HTTPS over TLS 1.2 or later
        alt_text (str): Alt text. When a user receives a message, it will appear as an
            alternative to the image in the notification or chat list of their device.
            Max character limit: 400
        base_size (dict of str: int): Should contain ``width`` and ``height`.
            See reference.
        video (dict of str: str | dict of str: int | dict of str: str): Contains
            ``originalContentUrl``, ``previewImageUrl``, ``area`` and ``externalLink``.
        actions (list of dict of str: dict of str: int): Action when tapped
            Max: 50
    """
    __slots__ = (
        "json",
    )
    json: dict[str, str | dict | list]
    def __init__(
        self,
        *,
        base_url: str,
        alt_text: str,
        base_size: dict[str, int],
        video: dict[str, str | dict[str, int] | dict[str, str]],
        actions: list[AbstractLineAction] | list[dict]
    ):
        self.json = {
          "type": "imagemap",
          "baseUrl": base_url,
          "altText": alt_text,
          "baseSize": base_size,
          "video": video,
          "actions": [
              action.to_json() for action in actions
          ] if isinstance(actions[0], AbstractLineAction) else actions
        }

    def to_json(self) -> dict[str, str | dict | list]:
        return self.json

class Templates:
    """Template messages are messages with predefined layouts which you can customize.

    For more information, check the reference.

    The following template types are available:

    * Buttons
    * Confirm
    * Carousel
    * Image carousel

    .. warning ::
        This class is neither an actual template nor a valid LineX LINE message object.
        Use this like a namespace. See attributes.

    .. note ::
        `Reference <https://developers.line.biz/en/reference/messaging-api/#template-messages>`_

    Attributes:
        Buttons (type): Template with an image, title, text, and multiple action buttons
        Confirm (type): Template with two action buttons.
        Carousel (type): Template with multiple columns which can be cycled
            like a carousel. The columns are shown in order when scrolling horizontally.
    """

    class Buttons(AbstractLineMessage):
        """Template with an image, title, text, and multiple action buttons.

        Args:
            alt_text (str): The alt text.
            text (str): The text.
                Max character limit: 160 (no image or title)
                Max character limit: 60 (message with an image or title)
            actions (list of dict): The action objects.
            thumbnail_image_url (str, optional): Image URL (Max character limit: 2,000)
            image_aspect_ratio (str, optional): Aspect ratio of the image. One of:
                ``rectangle``: 1.51:1 and
                ``square``: 1:1
            image_size (str, optional): Size of the image. One of:
                ``cover``: The image fills the entire image area. Parts of the image
                that do not fit in the area are not displayed.
                ``contain``: The entire image is displayed in the image area.
                A background is displayed in the unused areas to the left and right of
                vertical images and in the areas above and below horizontal images.
            image_background_color (str, optional): Background color of the image.
                Specify a RGB color value. Default: ``#FFFFFF`` (white)
            title (str, optional): The title. Max character limit: 40
            default_action (dict, optional): Action when image, title or text area is
                tapped.
        """
        __slots__ = (
            "json",
        )
        json: dict[str, Any]

        def __init__(
            self,
            *,
            alt_text: str,
            text: str,
            actions: list[dict],
            thumbnail_image_url: Optional[str] = None,
            image_aspect_ratio: Literal['rectangle', 'square'] = "rectangle",
            image_size: Literal['cover', 'contain'] = "cover",
            image_background_color: str = "#FFFFFF",
            title: Optional[str] = None,
            default_action: Optional[AbstractLineAction | dict] = None
        ):
            self.json = {
                "type": "template",
                "altText": alt_text,
                "template": {
                    "type": "buttons",
                    "thumbnailImageUrl": thumbnail_image_url,
                    "imageAspectRatio": image_aspect_ratio,
                    "imageSize": image_size,
                    "imageBackgroundColor": image_background_color,
                    "title": title,
                    "text": text,
                    "defaultAction": default_action.to_json() if 
                    isinstance(default_action, AbstractLineAction) else default_action,
                    "actions": [
                        action.to_json() for action in actions # type: ignore
                    ] if isinstance(actions[0], AbstractLineAction) else actions
                }
            }

        def to_json(self) -> dict[str, Any]:
            return self.json


    class Confirm(AbstractLineMessage):
        """Template with two action buttons.

        Args:
            alt_text (str): The alt text.
            text (str): The text.
                Max character limit: 160 (no image or title)
                Max character limit: 60 (message with an image or title)
            actions (list of dict): The action objects.
        """
        __slots__ = (
            "json",
        )
        json: dict[str, Any]

        def __init__(
            self,
            *,
            alt_text: str,
            text: str,
            actions: list[AbstractLineAction] | list[dict]
        ):
            self.json = {
                "type": "template",
                "altText": alt_text,
                "template": {
                    "type": "confirm",
                    "text": text,
                    "actions": [
                        action.to_json() for action in actions
                    ] if isinstance(actions[0], AbstractLineAction) else actions
                }
            }

        def to_json(self) -> dict[str, Any]:
            return self.json


    class Carousel(AbstractLineMessage):
        """Template with multiple columns which can be cycled like a carousel.

        The columns are shown in order when scrolling horizontally.

        .. note ::
            `Reference <https://developers.line.biz/en/reference/messaging-api/#template-messages>`_

        Args:
            alt_text (str): The alt text.
            columns (list): List of column objects.
            image_aspect_ratio (str, optional): Aspect ratio of the image. One of:
                ``rectangle``: 1.51:1 and
                ``square``: 1:1
            image_size (str, optional): Size of the image. One of:
                ``cover``: The image fills the entire image area. Parts of the image
                that do not fit in the area are not displayed.
                ``contain``: The entire image is displayed in the image area.
                A background is displayed in the unused areas to the left and right of
                vertical images and in the areas above and below horizontal images.
        """

        __slots__ = (
            "json",
        )
        json: dict[str, Any]

        def __init__(
            self,
            *,
            alt_text: str,
            columns: list[dict[str, str | dict[str, str] | list[dict[str, str]]]],
            image_aspect_ratio: Literal['rectangle', 'square'] = "rectangle",
            image_size: Literal['cover', 'contain'] = "cover",
        ):
            self.json = {
                "type": "template",
                "altText": alt_text,
                "template": {
                    "type": "carousel",
                    "columns": columns,
                    "imageAspectRatio": image_aspect_ratio,
                    "imageSize": image_size
                }
            }

        def to_json(self) -> dict:
            return self.json
