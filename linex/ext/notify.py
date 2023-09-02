import asyncio
import os
from typing import Literal, Optional
from urllib.parse import quote_plus

import httpx
from pydantic import BaseModel

from ..models import Sticker


class NotifyResponse(BaseModel):
    status: Literal[200, 400, 401]
    message: str # message visible to end-user

class NotifyStatus(BaseModel):
    status: Literal[200, 401]
    message: str # message visible to end-user
    target_type: Literal["USER", "GROUP"]
    target: Optional[str] # username / group name

class Notify:
    """Represents LINE notify.

    Args:
        access_token (str): The access token. If not given, reads environment var: 
            ``LINEX_NOTIFY_ACCESS_TOKEN``.
    """
    __slots__ = (
        'headers',
        'access_token'
    )
    headers: dict[str, str]
    access_token: str

    def __init__(
        self,
        access_token: Optional[str] = None
    ):
        self.access_token = access_token or os.environ['LINEX_NOTIFY_ACCESS_TOKEN']
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    async def notify(
        self,
        message: str,
        *,
        image_thumbnail: Optional[str] = None,
        image_full_size: Optional[str] = None,
        image_file: Optional[str | bytes] = None,
        sticker: Optional[Sticker] = None,
        notification_disabled: Optional[bool] = False
    ):
        """Sends notifications to users or groups that are related to the access token.

        Args:
            message (str): The message.
            image_thumbnail (str, optional): Image thumbnail URL. (Max 240x240)
            image_full_size (str, optional): Full-size image URL. (Max 2048x2048)
            image_file (str | bytes, optional): Upload a image file to the LINE server.
                If :obj:`str` is given, reads a file; if :obj:`bytes` are given,
                uses directly. The supported image formats are png and jpeg.
            sticker (:obj:`Sticker`, optional): The sticker.
            notification_disabled (bool, optional): If set to ``True``, the user will
                not receive a push notification, vice versa. Default to ``False``.
        """
        sticker_meta: dict[str, str] = sticker.to_json() if sticker else {}

        file_content = None

        if isinstance(image_file, bytes):
            file_content = image_file
    
        elif image_file: # ensure
            with open(image_file, "rb") as file:
                file_content = file.read()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://notify-api.line.me/api/notify",
                params={
                    "message": message,
                    "imageThumbnail": image_thumbnail,
                    "imageFullsize": image_full_size,
                    "stickerPackageId": sticker_meta.get("stickerPackageId"),
                    "stickerId": sticker_meta.get("stickerId"),
                    "notificationDisabled": notification_disabled,
                },
                files={
                    "imageFile": file_content
                } if file_content else {},
                headers=self.headers
            )

            resp.raise_for_status()

            return NotifyResponse(**resp.json())

    def notify_sync(
        self,
        message: str,
        *,
        image_thumbnail: Optional[str] = None,
        image_full_size: Optional[str] = None,
        image_file: Optional[str | bytes] = None,
        sticker: Optional[Sticker] = None,
        notification_disabled: Optional[bool] = False
    ) -> NotifyResponse:
        """Sends notifications to users or groups that are related to the access token.

        (no coro, used ``asyncio.run``)

        Args:
            message (str): The message.
            image_thumbnail (str, optional): Image thumbnail URL. (Max 240x240)
            image_full_size (str, optional): Full-size image URL. (Max 2048x2048)
            image_file (str | bytes, optional): Upload a image file to the LINE server.
                If :obj:`str` is given, reads a file; if :obj:`bytes` are given,
                uses directly. The supported image formats are png and jpeg.
            sticker (:obj:`Sticker`, optional): The sticker.
            notification_disabled (bool, optional): If set to ``True``, the user will
                not receive a push notification, vice versa. Default to ``False``.
        """
        return asyncio.run(self.notify(
            message,
            image_thumbnail=image_thumbnail,
            image_full_size=image_full_size,
            image_file=image_file,
            sticker=sticker,
            notification_disabled=notification_disabled
        ))

    async def get_status(self) -> NotifyStatus:
        """An API for checking connection status.
        
        You can use this API to check the validity of an access token.
        
        Acquires the names of related users or groups if acquiring them is possible.

        Returns:
            NotifyStatus: The notify client status.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://notify-api.line.me/api/status",
                headers=self.headers
            )
            resp.raise_for_status()
            data = resp.json()

            return NotifyStatus(
                status=data['status'],
                message=data['message'],
                target_type=data['targetType'],
                target=data['target']
            )

    def get_status_sync(self) -> NotifyStatus:
        """An API for checking connection status.
        
        You can use this API to check the validity of an access token.
        
        Acquires the names of related users or groups if acquiring them is possible.

        (no coro, used ``asyncio.run``)

        Returns:
            NotifyStatus: The notify client status.
        """
        return asyncio.run(self.get_status())

class NotifyAuthorize:
    """Becomes a provider based on OAuth2 (https://tools.ietf.org/html/rfc6749)

    Args:
        client_id (str): The client ID.
        client_secret (str): The client secret.
        redirect_uri (str): The redirect URI.
    """
    __slots__ = (
        "client_id",
        "client_secret",
        "redirect_uri"
    )
    client_id: str
    client_secret: str
    redirect_uri: str

    def __init__(
        self,
        *,
        client_id: str,
        client_secret: str,
        redirect_uri: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = quote_plus(redirect_uri)

    def authorize_uri(
        self,
        *,
        state: str,
        post_response_mode: bool = False,
        return_dict: bool = False,
    ) -> str | dict:
        """Gets the notify authorization endpoint URI.

        Args:
            state (str): Assigns a token (custom) that can be used for responding
                to CSRF attacks.
            post_response_mode (bool, optional): Sends POST request to redirect_uri by
                form post instead of redirecting.
            return_dict (bool, optional): Whether to return ``dict`` instead of ``str``
                or not.
        """
        data = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "notify",
            "state": state,
            **({
                "response_mode": 'form_post'
               } if post_response_mode else {}
            )
        }

        if return_dict:
            return data | {"BASE_URL": "https://notify-bot.line.me/oauth/authorize"}
    
        return "https://notify-bot.line.me/oauth/authorize?" + "&".join(
            f"{k}={v}" for k, v in data.items()
        )

    get_authorize_uri = authorize_uri

    async def get_token(self, code: str) -> str:
        """The OAuth2 token endpoint. Gets the auth (access) token.

        Args:
            code (str): The code in the URL param or body.

        Returns:
            str: The access token.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://notify-bot.line.me/oauth/token",
                params={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": self.redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret
                }
            )
            resp.raise_for_status()

            return resp.json()['access_token']

    get_access_token = get_token

    def get_token_sync(self, code: str) -> str:
        """The OAuth2 token endpoint. Gets the auth (access) token.

        (no coro, used ``asyncio.run``)

        Args:
            code (str): The code in the URL param or body.

        Returns:
            str: The access token.
        """
        return asyncio.run(
            self.get_token(code)
        )

    get_access_token_sync = get_token_sync
