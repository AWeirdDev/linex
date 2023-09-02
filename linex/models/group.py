from ..http import get_group_member_count


class Group:
    """Represents a LINE group.

    Args:
        data (dict[str, str]): The group data.
        headers (dict): The authorization headers.
    """
    __slots__ = (
        '_group_id',
        '_group_name',
        '_picture_url',
        '_headers'
    )
    
    def __init__(
        self,
        data: dict[str, str],
        headers: dict
    ):
        self._group_id = data['groupId']
        self._group_name = data['groupName']
        self._picture_url = data['pictureUrl']
        self._headers = headers

    @property
    def id(self) -> str:
        """The group ID."""
        return self._group_id

    @property
    def name(self) -> str:
        """The group name."""
        return self._group_name

    @property
    def picture_url(self) -> str:
        """The group picture (icon) URL."""
        return self._picture_url

    picture = icon = icon_url = picture_url

    async def count(self):
        """Shows the group count."""
        resp = await get_group_member_count(self._headers, self.id)
        return resp['count']
