# ruff: noqa: E501

from typing import Literal, Optional


class BotUser:
    """Represents a LINE bot user.

    Args:
        data (dict of str: str): The data in JSON, or dictionary.
    """
    __slots__ = (
        "_user_id", 
        "_basic_id",
        "_display_name",
        "_picture_url",
        "_chat_mode",
        "_mark_as_read_mode"
    )
    
    def __init__(
        self,
        data: dict[str, str]
    ):
        self._user_id = data['userId']
        self._basic_id = data['basicId']
        self._display_name = data['displayName']
        self._picture_url = data.get('pictureUrl')
        self._chat_mode = data['chatMode']
        self._mark_as_read_mode = data['markAsReadMode']

    @property
    def id(self) -> str:
        """Represents the bot ID."""
        return self._user_id

    @property
    def basic_id(self) -> str:
        """Represents the bot's basic ID (@handle)."""
        return self._basic_id

    handle = basic_id

    @property
    def display_name(self) -> str:
        """The bot's display name."""
        return self._display_name

    name = display_name

    @property
    def picture_url(self) -> Optional[str]:
        """The bot's picture URL, or avatar.

        May be none.
        """
        return self._picture_url

    avatar = picture = avatar_url = picture_url

    @property
    def chat_mode(self) -> Literal['chat', 'bot']:
        """The chat mode.

        One of:
        * ``chat``: Chat is set to "On."
        * ``bot``: Chat is set to "Off."
        """
        return self._chat_mode # type: ignore

    @property
    def mark_as_read_mode(self) -> Literal['auto', 'manual']:
        """Automatic read settings for messages.

        If the "chat" feature is set to "Off", ``auto`` is returned;
        if the "chat" feature is set to "On", ``manual`` is returned.
        """
        return self._mark_as_read_mode # type: ignore

    def __repr__(self) -> str:
        return (
            f'<BotUser id={self.id!r} basic_id={self.basic_id!r} '
            f'display_name={self.display_name!r} picture_url={self.picture_url!r} '
            f'chat_mode={self.chat_mode!r} mark_as_read_mode={self.mark_as_read_mode!r}>'
        )

class User:
    """Represents a regular LINE user.

    Args:
        data (dict of str: str): The data in JSON, or dictionary.
    """
    __slots__ = (
        "_user_id", 
        "_display_name",
        "_language",
        "_picture_url",
        "_status_message"
    )
    
    def __init__(
        self,
        data: dict[str, str]
    ):
        self._user_id = data['userId']
        self._display_name = data['displayName']
        self._language = data.get('language', 'en')
        self._picture_url = data.get('pictureUrl')
        self._status_message = data.get('statusMessage')

    @property
    def id(self) -> str:
        """Represents the user ID."""
        return self._user_id

    @property
    def display_name(self) -> str:
        """The user's display name."""
        return self._display_name

    name = display_name

    @property
    def language(self) -> str:
        """User's language, as a `BCP 47 <https://www.rfc-editor.org/info/bcp47>`_ language tag.

        If the user hasn't yet consented to the LINE Privacy Policy, returns ``en``.
        e.g. ``en`` for English.
        """
        return self._language

    @property
    def picture_url(self) -> Optional[str]:
        """The user's picture URL, or avatar.

        May be none.
        """
        return self._picture_url

    avatar = picture = avatar_url = picture_url

    @property
    def status_message(self) -> Optional[str]:
        """The user's status message.

        May be none.
        """
        return self._status_message

    status = status_message

    def __repr__(self) -> str:
        return (
            f'<User id={self.id!r} display_name={self.display_name!r} '
            f'picture_url={self.picture_url!r} '
            f'language={self.language!r} status={self.status!r}>'
        )
