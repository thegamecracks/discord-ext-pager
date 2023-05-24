# discord-ext-pager

[![PyPI](https://img.shields.io/pypi/v/discord-ext-pager?label=View%20on%20pypi&style=flat-square)](https://pypi.org/project/discord-ext-pager/)

A simple view-based paginator library for discord.py 2.0. Works with Python 3.8+.

## Usage

[discord-ext-pager] is available on PyPI, and as such can be installed using pip.

Users of Danny's [discord-ext-menus] will find some familiarity
in this library. Provided are the following classes:

- PaginatorView:
  The view class that manages pagination and navigation.
- PageSource:
  The base class for sources the paginator view can accept.
- ListPageSource:
  The base class for formatting a list of items.
- AsyncIteratorPageSource:
  The base class for formatting an asynchronous iterator of items.
- PageOption:
  A subclass of `discord.SelectOption` used for presenting navigation options.
- StopAction:
  An enum for customizing PaginatorView's stop button behaviour.
- TimeoutAction:
  An enum for customizing PaginatorView's timeout behaviour.

[discord-ext-pager]: https://pypi.org/project/discord-ext-pager/
[discord-ext-menus]: https://github.com/Rapptz/discord-ext-menus

The `PaginatorView` can be instantiated and used by itself, but page formatting
is handled by subclassing one of the `PageSource` base classes.

```py
from typing import List
from discord.ext.pager import ListPageSource, PageSource, PaginatorView

class EmbedListPageSource(ListPageSource[object, PageSource, PaginatorView]):
    #                                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    #            These type parameters denote the page item type,
    #            source type for page options (demonstrated later),
    #            and view type. Only needed for static typing.
    """Takes a list of items and formats it in an embed."""

    def format_page(self, view: PaginatorView, page: List[object]):
        index = self.current_index * self.page_size
        description = "\n".join(
            f"{i}. {x}"
            for i, x in enumerate(page, start=index + 1)
        )
        return discord.Embed(description=description)

# Anywhere a channel or interaction is available:
fruits = ["🍎 Apple", "🍊 Orange", "🍋 Lemon"]
source = EmbedListPageSource(fruits, page_size=2)
view = PaginatorView(sources=source, timeout=180)
await view.start(interaction)
```

If the navigation select menu is desired, the `get_page_options()` method
should be overridden to return a list of `PageOption` objects for the user
to select from:

```py
from typing import List
from discord.ext.pager import ListPageSource, PageOption, PageSource, PaginatorView

class MessageSource(PageSource[str, PageSource, PaginatorView]):
    """A single page for displaying a string."""

    def __init__(self, message: str):
        super().__init__(current_index=0)
        self.message = message

    def get_page(self, index: int):
        return self.message

    def format_page(self, view: PaginatorView, page: str):
        # If we don't specify both content and embed, either will
        # persist as the user clicks between options
        return {"content": page, "embed": None}

class MessageNavigator(ListPageSource[MessageSource, MessageSource, PaginatorView]):
    """A list of messages for the user to select from."""

    def get_page_options(self, view: PaginatorView, page: List[MessageSource]):
        # PageOption() takes the same arguments as discord.SelectOption,
        # except that source= is also required
        return [PageOption(source=source, label=source.message) for source in page]

    def format_page(self, view: PaginatorView, page: List[MessageSource]):
        description = "\n".join(source.message for source in page)
        embed = discord.Embed(description=description)
        return {"content": None, "embed": embed}

hands = "👈👉👆👇🫵🤞🫰🤘🤙🤛🤜✊👊👋👏🙌"
source = MessageNavigator([MessageSource(s) for s in hands], page_size=5)
view = PaginatorView(sources=source)
await view.start(ctx)
```

When an option is selected, the `PageSource` contained within that option
is appended to `PaginatorView.sources`, causing that source to be displayed.
Another button is automatically provided for users to back out to the last
page source. This can be manually triggered by passing a list of page sources
to the `PaginatorView(sources=)` argument.

## Examples

Click on an example below to see its source code:

[![Tag leaderboard](https://github.com/thegamecracks/discord-ext-pager/blob/main/docs/images/thegamebot_tags.png?raw=true)](https://github.com/thegamecracks/thegamebot/blob/04d9909877685acd24654a911b1853e2143fc316/bot/cogs/tags/__init__.py#L123-L162)

[![Help command](https://github.com/thegamecracks/discord-ext-pager/blob/main/docs/images/thegamebot_help.png?raw=true)](https://github.com/thegamecracks/thegamebot/blob/04d9909877685acd24654a911b1853e2143fc316/bot/cogs/helpcommand.py#L26-L249)
