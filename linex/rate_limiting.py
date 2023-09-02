from __future__ import annotations

import asyncio
import time


class RateLimit:
    """Represents a rate limit and prevents from exceeding it.

    Args:
        calls (int): Allowed calls.
        per (float): Per second.
    """
    __slots__ = (
        "calls",
        "per"
    )
    status: dict[str, int | float] = {
        "first_call": 0,
        "calls": 0,
        "wait_end": 0
    }
    calls: int
    per: float

    def __init__(
        self,
        calls: int,
        per: float
    ):
        self.calls = calls
        self.per = per

    async def call(self) -> None:
        """Used before sending HTTP requests, and prevents from being rate limited.

        *(coroutine)*

        .. image:: https://media.discordapp.net/attachments/1123914036535369748/1140505108971540571/1070087967294631976-44ae6597-086b-496b-b3c6-7886f6f16503-491657.60000002384.png?width=1176&height=535
            :alt: The Wumpy Request

        Raises:
            RateLimitError: The resource is probably going to be rate limited.
        """
        now = time.time()

        if (should_wait := self.status['wait_end']):
            await asyncio.sleep((now - should_wait))
            return await self.call()

        if not self.status['first_call']:
            self.status['first_call'] = now
            self.status['calls'] += 1
            return

        # already called before

        self.status['calls'] += 1

        if self.status['calls'] > self.calls\
        and now - self.status['first_call'] < self.per:
            self.status['wait_end'] = now + self.per + 0.1
            await asyncio.sleep(self.per + 0.1)
            self.status['first_call'] = 0
            self.status['calls'] = 0
            self.status['wait_end'] = 0

    @staticmethod
    def stats_and_broadcast() -> RateLimit:
        """60 requests per hour.

        * Send a narrowcast message
        * Send a broadcast message
        * Get number of sent messages
        * Get number of friends
        * Get friend demographics
        * Get user interaction statistics
        * Get statistics per unit
        * Test webhook endpoint
        """
        return RateLimit(60, 60 * 60)


    @staticmethod
    def audience_and_ads() -> RateLimit:
        """60 requests per minute.

        * Create audience for uploading user IDs (by JSON)
        * Create audience for uploading user IDs (by file)
        * Add user IDs or Identifiers for Advertisers (IFAs) to an audience for
            uploading user IDs (by JSON)
        * Add user IDs or Identifiers for Advertisers (IFAs) to an audience for
            uploading user IDs (by file)
        * Create audience for click-based retargeting
        * Create audience for impression-based retargeting
        * Rename an audience
        * Delete audience
        * Get audience data
        * Get data for multiple audiences
        * Get the authority level of the audience
        * Change the authority level of the audience
        """
        return RateLimit(60, 60)

    @staticmethod
    def webhook_endpoint() -> RateLimit:
        """1,000 requests per minute.

        * Set webhook endpoint URL
        * Get webhook endpoint information
        """
        return RateLimit(1_000, 60)

    @staticmethod
    def rich_menu() -> RateLimit:
        """100 requests per hour.

        .. note ::

            Creating and deleting rich menus using the LINE Official Account Manager
                is not subject to this restriction.

        * Create rich menu
        * Delete rich menu
        * Delete rich menu alias
        * Get the status of rich menu batch control
        """
        return RateLimit(100, 60 * 60)

    @staticmethod
    def replace_unlink_rich_menu() -> RateLimit:
        """3 requests per hour.

        * Replace or unlink the linked rich menus in batches
        """
        return RateLimit(3, 60 * 60)

    @staticmethod
    def other() -> RateLimit:
        """2,000 requests per second.

        Other API endpoints.
        """
        return RateLimit(2_000, 1)
