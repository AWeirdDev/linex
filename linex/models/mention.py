# ruff: noqa: E501

from __future__ import annotations

from typing import Literal, Optional

from .user import BotUser, User


class Mention:
    """Represents a LINE user mention.

    Args:
        type (str): The mention type.
        user (:obj:`User` | dict, optional): The user. Required when ``type`` is `user`.
    """
    __slots__ = (
        'type',
        'user_id'
    )
    type: Literal['all', 'user']
    user_id: Optional[str]

    def __init__(
        self,
        type: Literal['all', 'user'] = "user",
        *,
        user: Optional[User | dict] = None
    ):
        if type == "all" and user:
            raise TypeError("When `type` is set to `all`, `user` should remain None.")

        if type == "user" and not user:
            raise TypeError("Keyword-only argument `user` was not given.")
    
        self.type = type
        if type == 'user' and user:
            # pass type check
            if isinstance(user, dict):
                self.user_id = user['id']
            else:
                self.user_id = user.id


    def to_json(self) -> dict:
        """Converts to a valid JSON."""
        return {
            "type": self.type,
            "userId": self.user_id
        }

    def __repr__(self) -> str:
        return f"<Mention of {self.user_id!r}>"

    @staticmethod
    def all() -> Mention:
        """Shortcut for an ``@All`` mention."""
        return Mention("all")

    @staticmethod
    def user(user: User) -> Mention:
        """Shortcut for a user mention.

        Args:
            user (:obj:`User`): The user.
        """
        return Mention("user", user=user)

    @staticmethod
    def from_user_id(id: str) -> Mention:
        """Mention a user from its ID, instead of a complete user object.

        Args:
            id (str): The user ID.
        """
        return Mention(
            "user",
            user={
                "id": id
            }
        )

    @staticmethod
    def includes_mention(
        mentionees: list[dict[str, int | str]], 
        user: BotUser | User | str
    ) -> bool:
        """Check whether a user / the bot is being mentioned in a message or not.

        Args:
            mentionees (list of dict of str: int | str): The mentionees of the message.
            user (:obj:`BotUser` | :obj:`User` | str): The user to check for. Could be a user ID or object.

        Example:
            .. code-block :: python

                Mention.includes_mention([
                    {
                        "index": 0,
                        "length": 4,
                        "type": "user",
                        "userId": "U49585cd0d5..."
                    },
                    user # user object
                ])
        """
        mentions = []
        
        for mention in mentionees:
            if mention['type'] == 'all':
                return True
    
            mentions.append(mention['userId'])
            
        if isinstance(user, str):
            return user in mentions
        else:
            return user.id in mentions