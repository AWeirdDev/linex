from datetime import datetime
from typing import Any, Literal, Optional

from ..abc import AbstractLineAction


class Action:
    """These are types of actions for your bot to take when a user taps a button or an.

        image in a message.

    .. warning ::
        This class is neither an actual action nor a valid LineX LINE object.
        Use this like a namespace. See attributes.

    * Postback action
    * Message action
    * URI action
    * Datetime picker action
    * Camera action
    * Camera roll action
    * Location action
    * Richmenu Switch Action
    """

    class Postback(AbstractLineAction):
        """When a control associated with this action is tapped, a postback event is.

            returned via webhook with the specified string in the ``data`` property.

        `Specifications of the label <https://developers.line.biz/en/reference/messaging-api/#action-object-label-spec>`_

        Args:
            data (str): String returned via webhook in the ``data`` property of the
                postback event. Max character limit: 300
            label (str, optional): Label for the action. The specification depends
                on which object the action is set to. For more information, see the
                Specifications of the label above.
            display_text (str, optional): Text displayed in the chat as a message
                sent by the user when the action is performed. Required for
                quick reply buttons.
                Optional for the other message types. Max character limit: 300
            input_option (str, optional): The display method of such as rich menu
                based on user action. Specify one of the following values:
                * ``closeRichMenu``: Close rich menu
                * ``openRichMenu``: Open rich menu
                * ``openKeyboard``: Open keyboard
                * ``openVoice``: Open voice message input mode
            fill_in_text (str, optional): String to be pre-filled in the input field
                when the keyboard is opened. Valid only when ``input_option`` is set to
                ``openKeyboard``. The string can be broken by a newline character.
                Max character limit: 300
        """
        __slots__ = (
            'json',
        )
        json: dict[str, Any]

        def __init__(
            self,
            data: str,
            label: Optional[str] = None,
            display_text: Optional[str] = None,
            input_option: Optional[
                Literal[
                    'closeRichMenu', 
                    'openRichMenu', 
                    'openKeyboard', 
                    'openVoice'
                ]
            ] = None,
            fill_in_text: Optional[str] = None
        ):
            if fill_in_text and input_option != "openKeyboard":
                raise ValueError(
                    "`fill_in_text` is only usable when `input_option`"
                    "is `openKeyboard`"
                )
    
            self.json = {
                "type": "postback",
                "label": label,
                "data": data,
                "displayText": display_text,
                "inputOption": input_option,
                "fillInText": fill_in_text
            }

        def to_json(self) -> dict[str, Any]:
            return self.json

    class Message(AbstractLineAction):
        """When a control associated with this action is tapped, the string in ``text``.

        is sent as a message from the user.

        `Specification of the label <https://developers.line.biz/en/reference/messaging-api/#action-object-label-spec>`_

        Args:
            text (str): Text sent when the action is performed. Max character limit: 300
            label (str, optional): Label for the action.
                The specification depends on which object the action is set to.
                For more information, see Specifications of the label above.
        """

        __slots__ = (
            'json',
        )
        json: dict[str, Optional[str]]

        def __init__(
            self,
            text: str,
            label: Optional[str] = None
        ):
            self.json = {
                "type": "message",
                "label": label,
                "text": text
            }

        def to_json(self) -> dict[str, Optional[str]]:
            return self.json

    class URI(AbstractLineAction):
        """When a control associated with this action is tapped, the URI specified.

        in ``uri`` is opened in LINE's in-app browser.

        `Specifications of the label <https://developers.line.biz/en/reference/messaging-api/#action-object-label-spec>`_

        `Using the LINE URI scheme <https://developers.line.biz/en/docs/messaging-api/using-line-url-scheme/>`_

        Args:
            uri (str): URI opened when the action is performed.
                (Max character limit: 1000)
                The available schemes are ``http``, ``https``, ``line``, and ``tel``.
                For more information about the LINE URL scheme, see Using the LINE
                URL scheme above.
            label (str, optional): Label for the action. The specification depends on
                which object the action is set to.
                For more information, see Specifications of the label above.
            desktop_uri (str, optional): URI opened on LINE for macOS and Windows when
                the action is performed (Max character limit: 1000)
                This property is supported on 5.12.0 or later
                for both LINE for macOS and LINE for Windows.
        """
        __slots__ = (
            'json',
        )
        json: dict[str, Optional[str] | dict[str, Optional[str]]]

        def __init__(
            self,
            uri: str,
            label: Optional[str] = None,
            desktop_uri: Optional[str] = None
        ):
            self.json = {
                "type": "uri",
                "label": label,
                "uri": uri,
                "altUri": {
                    "desktop": desktop_uri
                }
            }

        def to_json(self) -> dict[str, Optional[str] | dict[str, Optional[str]]]:
            return self.json

    class DatetimePicker(AbstractLineAction):
        """When a control associated with this action is tapped, a postback event is.

        returned via webhook with the date and time selected by the user from the
        date and time selection dialog. The datetime picker action does not support
        time zones.

        `Specifications of the label <https://developers.line.biz/en/reference/messaging-api/#action-object-label-spec>`_

        `Date and time format <https://developers.line.biz/en/reference/messaging-api/#date-and-time-format>`_

        Args:
            data (str): String returned via webhook in the property of
                the postback event. Max character limit: 300
            mode (str): Action mode.
                * ``date``: Pick date
                * ``time``: Pick time
                * ``datetime``: Pick date and time
            label (str, optional): Label for the action. The specification depends on
                which object the action is set to.
                For more information, see Specifications of the label above.
            initial (str, optional): Initial (default) value of date or time.
            _max (str, optional): Largest date or time value that can be selected.
                Must be greater than the min value.
            _min (str, optional): Smallest date or time value that can be selected.
                Must be less than the max value.
        """
        __slots__ = (
            'json',
        )
        patterns = {
            "date": ["%Y-%m-%d"],
            "time": ["%H:%M"],
            "datetime": ["%Y-%m-%dT%H:%M", "%Y-%m-%dt%H:%M"]
        }
        json: dict[str, Optional[str]]

        def __init__(
            self,
            data: str,
            mode: Literal['date', 'time', 'datetime'],
            label: Optional[str] = None,
            initial: Optional[str] = None,
            _max: Optional[str] = None,
            _min: Optional[str] = None
        ):
            self.json = {
                "type": "datetimepicker",
                "label": label,
                "data": data,
                "mode": mode,
                "initial": Action.DatetimePicker.validate(mode, initial),
                "max": Action.DatetimePicker.validate(mode, _max),
                "min": Action.DatetimePicker.validate(mode, _min)
            }

        def to_json(self) -> dict[str, Optional[str]]:
            return self.json

        @staticmethod
        def validate(
            mode: Literal['date', 'time', 'datetime'],
            string: Optional[str] = None
        ) -> Optional[str]:
            """Validates a string based on a specific datetime picker mode.

            Args:
                mode (str): The mode.
                string (str, optional): The test string. Returns None if not given.

            Returns:
                str: Returns the original string.

            Raises:
                ValueError: The string did not match the format.
            """
            if not string:
                return string

            patterns: list[str] = Action.DatetimePicker.patterns[mode]

            try:
                for pattern in patterns:
                    datetime.strptime(string, pattern)
            except ValueError as err:
                acceptances = "\n- ".join(patterns)
                raise ValueError(
                    f"Mode {mode!r} only accepts formats:\n- {acceptances}"
                ) from err

            return string

        @staticmethod
        def convert(
            mode: Literal['date', 'time', 'datetime'],
            obj: datetime
        ) -> str:
            """Converts a datetime object to a valid LINE datetime string.

            Args:
                mode (str): The target mode.
                obj (:obj:`datetime`): The datetime object from module ``datetime``.
            """
            pattern: str = Action.DatetimePicker.patterns[mode][0]
            return obj.strftime(pattern)

    class Camera(AbstractLineAction):
        """This action can be configured only with quick reply buttons.

        When a button
        associated with this action is tapped, the camera screen in LINE is opened.

        Args:
            label (str): Label for the action. Max character limit: 20
        """
        __slots__ = (
            'json',
        )
        json: dict[str, str]

        def __init__(
            self,
            label: str
        ):
            self.json = {
                "type": "camera",
                "label": label
            }

        def to_json(self) -> dict[str, str]:
            return self.json

    class CameraRoll(AbstractLineAction):
        """This action can be configured only with quick reply buttons.

        When a button
        associated with this action is tapped, the camera roll screen in LINE is opened.

        Args:
            label (str): Label for the action. Max character limit: 20
        """
        __slots__ = (
            'json',
        )
        json: dict[str, str]

        def __init__(
            self,
            label: str
        ):
            self.json = {
                "type": "cameraRoll",
                "label": label
            }

        def to_json(self) -> dict[str, str]:
            return self.json

    class Location(AbstractLineAction):
        """This action can be configured only with quick reply buttons.

        When a button
        associated with this action is tapped, the location screen in LINE is opened.

        Args:
            label (str): Label for the action. Max character limit: 20
        """
        __slots__ = (
            'json',
        )
        json: dict[str, str]

        def __init__(
            self,
            label: str
        ):
            self.json = {
                "type": "location",
                "label": label
            }

        def to_json(self) -> dict[str, str]:
            return self.json

    class RichMenuSwitch(AbstractLineAction):
        """This action can be configured only with rich menus.

        It can't be used for Flex Messages or quick replies. When you tap a rich menu
        associated with this action, you can switch between rich menus, and a postback
        event including the rich menu alias ID selected by the user is returned via
        a webhook. For more information, see Switching between multiple rich menus in
        the `Messaging API documentation <https://developers.line.biz/en/docs/messaging-api/using-rich-menus/#switching-between-multiple-rich-menus>`_.

        Args:
            rich_menu_alias_id (str): Rich menu alias ID to switch to.
            data (str): String returned by the ``data`` property of the postback event
                via a webhook. (Max: 30 characters)
            label (str, optional): Action label. Optional for rich menus. Read when the
                user's device accessibility feature is enabled.
                Max character limit: 20
        """
        __slots__ = (
            'json',
        )
        json: dict[str, Optional[str]]

        def __init__(
            self,
            rich_menu_alias_id: str,
            data: str,
            label: Optional[str] = None
        ):
            self.json = {
                "type": "richmenuswitch",
                "richMenuAliasId": rich_menu_alias_id,
                "data": data,
                "label": label
            }

        def to_json(self) -> dict[str, Optional[str]]:
            return self.json
