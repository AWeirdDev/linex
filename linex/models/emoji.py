import re
from typing import Any


class Emoji:
    """Represents a LINE emoji.

    .. warning::
        The default LINE emojis sent from LINE for Android won't be included.

    Args:
        product_id (str): The product ID.
        emoji_id (str): The emoji ID.
    """
    __slots__ = (
        "product_id",
        "emoji_id",
        "format"
    )
    product_id: str
    emoji_id: str
    format: str

    def __init__(
        self,
        product_id: str,
        emoji_id: str
    ):
        self.product_id = product_id
        self.emoji_id = emoji_id
        self.format = f"[{emoji_id}]({product_id})"
        

    def to_json(self):
        """Converts to a valid JSON."""
        return {
            "productId": self.product_id,
            "emojiId": self.emoji_id
        }

    def __repr__(self) -> str:
        return (
            f"<Emoji product_id={self.product_id!r} emoji_id={self.emoji_id!r} "
            f"format={self.format!r}>"
        )
    
    @staticmethod
    def fit_on_texts(
        text: str,
        emojis: list[dict[str, str | int]]
    ) -> str:
        """Fit the emojis on the texts.

        Args:
            text (str): The text.
            emojis (list of dict of str: str | int): Emojis.

        Example:
            .. code-block :: python

                Emoji.fit_on_texts(
                    "@All @example Good Morning!! (love)",
                    [
                        {
                            "index": 29,
                            "length": 6,
                            "productId": "5ac1bfd5040ab15980c9b435",
                            "emojiId": "001"
                        }
                    ]
                )
        """
        output: str = text
    
        for emoji in emojis:
            index: int = emoji['index'] # type: ignore
            length: int = emoji['length'] # type: ignore
            format = f"[{emoji['emojiId']}]({emoji['productId']})"
            output = output[:index] + format + output[index + length:]

        return output

    @staticmethod
    def emoji_text_to_emojis(
        text: str
    ) -> tuple[str, list[dict[str, Any]]]:
        """Converts Linex LINE emoji text to a valid JSON emoji payload.

        Args:
            text (str): The text.

        Example:
            .. code-block :: python

                Emoji.emoji_text_to_emojis(
                    "@All @example Good Morning!! [001](5ac1bfd5040ab15980c9b435)"
                )
                # returns:
                # "@All @example Good Morning!!", {
                #     "emojiId": "001",
                #     "productId": "5ac1bfd5040ab15980c9b435"
                # }
        """
        matches = re.finditer(r"\[(\d+?)\]\(([\d\w]+?)\)", text)
        replacement = "$"
        
        result = ""
        prev_end = 0
        emojis: list[dict[str, str | int]] = []
        
        for match in matches:
            emoji_id, product_id = match.groups()

            start, end = match.start(), match.end()
            result += text[prev_end:start] + replacement
            prev_end = end
            emojis.append({
                "index": len(result) - 1,
                "emojiId": emoji_id,
                "productId": product_id
            })
        
        result += text[prev_end:]
        
        return result, emojis
