# discord-ext-pager

A simple view-based paginator library for discord.py 2.0.

## Installation

This package is available on pip as `discord-ext-pager`.
If you have Git, you may also choose to install the latest version
using `pip install git+https://github.com/thegamecracks/discord-ext-pager`.

## Basic Usage

Prior users of Danny's [`discord-ext-menus`] will find some familiarity
in this library. Provided are the following classes:

- PaginatorView:
  The view class that manages the paginator.
- PageSource:
  The base class for sources the paginator view can accept.
- ListPageSource:
  The base class for formatting a list of items.
- AsyncIteratorPageSource:
  The base class for formatting an asynchronous iterator of items.
- PageOption:
  A subclass of `discord.SelectOption` that also stores a `PageSource` instance.
  Used for the navigation select menu.
- TimeoutAction:
  An enum for customizing PaginatorView's timeout behaviour.

The `PaginatorView` can be instantiated and used by itself, but page formatting
is handled by subclassing one of the `PageSource` base classes.

```py
from typing import Any, List
from discord.ext.pager import ListPageSource, PaginatorView

class EmbedListPageSource(ListPageSource[Any, None, PaginatorView]):
    """Takes a list of items and formats it in an embed."""

    def format_page(self, view: PaginatorView, page: List[Any]):
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
from discord.ext.pager import ListPageSource, PageOption, PaginatorView, PageSource

class MessageSource(PageSource[str, None, PaginatorView]):
    """A single page for displaying a string."""

    def __init__(self, message: str, *, current_index: int = 0):
        super().__init__(current_index=current_index)
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

[`discord-ext-menus`]: https://github.com/Rapptz/discord-ext-menus

## Examples

Click on each example to see the source code:

[![Tag leaderboard](https://github.com/thegamecracks/discord-ext-pager/blob/main/docs/images/thegamebot_tags.png?raw=true)](https://github.com/thegamecracks/thegamebot/blob/04d9909877685acd24654a911b1853e2143fc316/bot/cogs/tags/__init__.py#L123-L162)

[![Help command](https://github.com/thegamecracks/discord-ext-pager/blob/main/docs/images/thegamebot_help.png?raw=true)](https://github.com/thegamecracks/thegamebot/blob/04d9909877685acd24654a911b1853e2143fc316/bot/cogs/helpcommand.py#L26-L249)
