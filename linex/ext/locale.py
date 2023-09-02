from __future__ import annotations

import json
import os
from typing import Any, Literal

from ..models import BaseContext

NO_KWARGS: dict = {}

class Locale:
    """Locale strings manager, used for i18n translations.

    .. warning ::

        Use the ``sorted_by`` arg as an keyword-only arg.

    Args:
        directory (str): The directory that contains files for i18n locale strings.
        sorted_by (str, optional): How the files are sorted.
            If they're sorted by "categories" (default option), then each file contains
            various language translations of a specific topic, such as "food.json"
            would contain locale strings related to food in various languages.
            As for "locales," it means that each file would represent a locale, and
            consist of different categories all in one singular locale file.

    Example:
        .. code-block ::

            locale = Locale("loc-dir/")
            @client.event
            async def on_text(ctx):
                loc = await locale(ctx)
                await ctx.reply(
                    loc("my-locale-string")
                )
    """
    __slots__ = (
        "directory",
        "sorted_by"
    )
    directory: str
    sorted_by: Literal['categories', 'locales']

    def __init__(
        self, 
        directory: str,
        *,
        sorted_by: Literal['categories', 'locales'] = "categories"
    ):
        if not os.path.exists(directory):
            raise NotADirectoryError(
                f"Directory does not exist: {directory!r}"
            )

        self.directory = directory.replace("\\", "/") # uwu
        self.sorted_by = sorted_by

    @property
    def metapos(self):
        """The ``_meta.json`` file path."""
        return self.basedir + "_meta.json"

    @property
    def basedir(self):
        """Get base directory that ends with a slash."""
        return self.directory + ("" if self.directory.endswith('/') else "/")

    async def __call__(
        self,
        target: BaseContext
    ) -> loc:
        """Retrieves the desired locale for the user.

        Args:
            target (:obj:`BaseContext`): The target context.
        """
        author = await target.author()
        contents: dict[str, dict[str, Any]] = {}

        if os.path.exists(self.metapos):
            with open(self.metapos, "rb") as f:
                meta = json.load(f)
                contents = {
                    k: {} for k in meta['locales']
                }
        else:
            if self.sorted_by == "categories":
                raise ValueError(
                    "If `sorted_by` categories, should include `_meta.json`:\n"
                    "{\n"
                    '    "locales": ["en-US", "locale1", "..."]\n'
                    "}"
                )

            for fn in os.listdir(self.directory):
                if not fn.endswith('.json'):
                    continue

                contents[
                    fn[:-len('.json')]
                ] = {}
        
        if self.sorted_by == "locales":
            for locale in list(contents):
                with open(self.basedir + locale + ".json", "rb") as f:
                    data = json.load(f)
                    contents[locale] |= data
        else:
            for categoryFn in os.listdir(self.directory):
                if not categoryFn.endswith('.json')\
                or categoryFn == "_meta.json":
                    continue

                category = categoryFn[:-len('.json')]
                with open(self.basedir + categoryFn, "rb") as f:
                    for KEY, localeDicts in json.load(f).items():
                        for locale, translation in localeDicts.items():
                            contents[locale] |= {
                                f"{category}/{KEY}": translation
                            }

        return loc(
            author.language,
            contents
        )

    locale_for = __call__

class loc:
    """Represents a target-locked locale string manager.

    Args:
        target_locale (str): The target locale.

    Attributes:
        tl (str): Target locale.
        contents (dict of str: dict of str: Any): Contents.
    """
    __slots__ = (
        "tl",
        "contents"
    )

    tl: str
    contents: dict[str, dict[str, Any]]

    def __init__(
        self,
        target_locale: str,
        contents: dict[str, dict[str, Any]]
    ):
        self.tl = target_locale
        self.contents = contents

    def __call__(
        self,
        key: str,
        kwargs: dict[str, str] = NO_KWARGS,
        **kwargs_common
    ) -> Any:
        """Finds a locale string or data.

        Args:
            key (str): The key. If using ``categories`` as for the file-sorting method,
                use ``{category}/{key name}`` instead of just the key name.
            kwargs (dict of str: str, optional): A dictionary containing keyword-only
                arguments (surrounded by ``{}`` within a string in a JSON file)

            **kwargs_common (dict of str: str, optional): easier method for replacing
                keyword-only arguments than the previous one (``kwarg``).
        """
        _kwargs = kwargs | kwargs_common

        locale: str = self.tl if self.tl in self.contents else list(self.contents)[0]

        desired_content: Any = self.contents[locale][key]

        if _kwargs:
            if not isinstance(desired_content, str):
                raise ValueError(
                    f"Key {key!r} for locale {locale!r} is paired to "
                    f"{type(desired_content)} (not str), which cannot be "
                    "used with 'kwargs' or '**kwargs_common'"
                )

            else:
                for target, replacement in _kwargs.items():
                    desired_content = desired_content.replace(
                        "{" + target + "}",
                        str(replacement)
                    )

        return desired_content

    _ = __call__ # alias
