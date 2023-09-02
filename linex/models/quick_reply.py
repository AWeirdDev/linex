from typing import Any, Optional

from ..abc import AbstractLineAction


class QuickReplyButton:
    """This is a quick reply option that is displayed as a button.

    Args:
        action (:obj:`AbstractLineAction`): Action performed when this button is tapped.
            Specify an action object. The following is a list of the available actions:
            * Postback action
            * Message action
            * URI action
            * Datetime picker action
            * Camera action
            * Camera roll action
            * Location action
        image_url (str, optional): URL of the icon that is displayed at the
            beginning of the button
            Max character limit: 2000
            URL scheme: ``https``
            Image format: PNG
            Aspect ratio: ``1:1`` (width : height)
            Data size: Up to 1 MB
            There is no limit on the image size.
            If the action property has a camera action, camera roll action, or
            location action, and ``image_url`` is not set, the default icon is
            displayed. The URL should be percent-encoded using UTF-8.
    """
    __slots__ = (
        'json',
    )
    json: dict[str, Any]

    def __init__(
        self,
        action: AbstractLineAction | dict,
        image_url: Optional[str] = None
    ):
        self.json = {
            "type": "action",
            "action": action.to_json() # type: ignore
            if isinstance(action, AbstractLineAction) else action,
            "imageUrl": image_url
        }

    def to_json(self) -> dict[str, Any]:
        return self.json
