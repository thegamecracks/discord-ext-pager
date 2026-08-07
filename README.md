# discord-ext-pager

[![PyPI](https://img.shields.io/pypi/v/discord-ext-pager?label=View%20on%20pypi&style=flat-square)](https://pypi.org/project/discord-ext-pager/)

A simple view-based paginator library for discord.py 2.0. Works with Python 3.8+.

> [!NOTE]
>
> This library was written before Discord introduced
> [Components v2](https://docs.discord.com/developers/components/overview).
> You can still use this library, but if you want the
> *latest-and-greatest Discord UI design*,
> I suggest writing your own paginator with the new
> [LayoutView](https://discordpy.readthedocs.io/en/stable/interactions/api.html#layoutview)
> components.
>
> Not sure how to get started with Components v2 in discord.py?
> - See Discord's [official documentation](https://docs.discord.com/developers/components/reference),
>   for an idea of what components are available
> - See discord.py's [API reference](https://discordpy.readthedocs.io/en/stable/interactions/api.html#layoutview)
>   for the corresponding components
> - See discord.py's [examples](https://github.com/Rapptz/discord.py/tree/master/examples/views)
>   (look for files using the `LayoutView` class, not `View`)
> - See the unofficial [discord.py masterclass](https://fallendeity.github.io/discord.py-masterclass/components-v2/)
>   guide
> - See an example of layout views in my other project, [ministatus](https://github.com/thegamecracks/ministatus)
>
>   This includes stack-based navigation in the form of
>   [`Book`](https://github.com/thegamecracks/ministatus/blob/main/src/ministatus/bot/cogs/status/views/book.py)s
>   and `Page`s, inspired by nested PageOptions from this library.
>   The UI does not showcase pagination specifically, but hopefully you can
>   get an idea of how to design complex UIs with LayoutViews.
>   And yes, the book-and-page terminology doesn't make sense 🙃

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

While the `PaginatorView` can be instantiated and used by itself, page formatting
is handled by subclassing one of the `PageSource` base classes:

```py
from typing import List
from discord.ext.pager import ListPageSource, PageSource, PaginatorView


class EmbedListPageSource(ListPageSource):
    """Takes a list of items and formats it in an embed."""

    def format_page(self, view: PaginatorView, page: List[object]):
        index = self.current_index * self.page_size
        description = "\n".join(
            f"{i}. {x}" for i, x in enumerate(page, start=index + 1)
        )
        return discord.Embed(description=description)


# Anywhere a channel or interaction is available:
fruits = ["🍎 Apple", "🍊 Orange", "🍋 Lemon"]
source = EmbedListPageSource(fruits, page_size=2)
view = PaginatorView(sources=source, timeout=180)
await view.start(interaction)
```

A navigation select menu for sub-pages can be added by overriding the
`get_page_options()` method to return a list of `PageOption` objects:

```py
from typing import List
from discord.ext.pager import ListPageSource, PageOption, PageSource, PaginatorView


class MessageSource(PageSource):
    """A page source that simply displays a string in the message content."""

    def __init__(self, message: str):
        super().__init__(current_index=0)
        self.message = message

    def get_page(self, index: int):
        return self.message

    def format_page(self, view: PaginatorView, page: str):
        return {"content": page, "embed": None}


class MessageNavigator(ListPageSource):
    """A list of messages that the user can select to view."""

    def get_page_options(self, view: PaginatorView, page: List[MessageSource]):
        # PageOption() takes the same arguments as discord.SelectOption
        # plus a source= argument
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

Once an option is selected, the `PageSource` contained within that option
is appended to `PaginatorView.sources`, causing that source to be displayed.
Another button is automatically provided for users to back out to the last
page source. This can be manually triggered by passing a list of page sources
to the `PaginatorView(sources=)` argument.

## Examples

Click on an example below to see its source code:

[![Tag leaderboard](https://github.com/thegamecracks/discord-ext-pager/blob/main/docs/images/thegamebot_tags.png?raw=true)](https://github.com/thegamecracks/thegamebot/blob/04d9909877685acd24654a911b1853e2143fc316/bot/cogs/tags/__init__.py#L123-L162)

[![Help command](https://github.com/thegamecracks/discord-ext-pager/blob/main/docs/images/thegamebot_help.png?raw=true)](https://github.com/thegamecracks/thegamebot/blob/04d9909877685acd24654a911b1853e2143fc316/bot/cogs/helpcommand.py#L26-L249)
