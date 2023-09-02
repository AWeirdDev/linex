from typing import Optional


class Sender:
    """Represents a sender.

    Args:
        name (str): Sender name. Max character limit: 20.
            Certain words such as ``LINE`` may not be used.
        icon_url (str, optional): URL of the image to display as an icon when sending
            a message
    """
    __slots__ = (
        'name',
        'icon_url'
    )
    name: Optional[str]
    icon_url: Optional[str]

    def __init__(
        self,
        *,
        name: Optional[str],
        icon_url: Optional[str]
    ):
        if not name and not icon_url:
            raise ValueError(
                "Must provide either the name or the icon URL, or both."
            )

        if name and "line" in name.lower():
            raise ValueError(
                "The word 'LINE' shouldn't be in a name. Would be rejected."
            )

        self.name = name
        self.icon_url = icon_url

    def to_json(self):
        """Converts to a valid JSON payload."""
        return {
            "name": self.name,
            "iconUrl": self.icon_url
        }
