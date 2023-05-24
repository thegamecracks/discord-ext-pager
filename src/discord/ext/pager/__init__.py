#  Copyright (C) 2023 thegamecracks
#  This Source Code Form is subject to the terms of the Mozilla Public
#  License, v. 2.0. If a copy of the MPL was not distributed with this
#  file, You can obtain one at http://mozilla.org/MPL/2.0/.
import functools
import math
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import (
    Any,
    AsyncIterator,
    Collection,
    Coroutine,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    TypedDict,
    TypeVar,
    Union,
    cast,
)

import discord
from typing_extensions import TypeAlias

__version__ = "1.1.1b"

__all__ = (
    "PageOption",
    "PageSource",
    "ListPageSource",
    "AsyncIteratorPageSource",
    "StopAction",
    "TimeoutAction",
    "PaginatorView",
)

E = TypeVar("E")
T = TypeVar("T")
S_co = TypeVar("S_co", bound="PageSource", covariant=True)
V_contra = TypeVar("V_contra", bound="PaginatorView", contravariant=True)
FP: TypeAlias = "Union[_PageParams, str, discord.Embed]"
PO: TypeAlias = "Sequence[PageOption[S_co]]"


class _PageParams(TypedDict, total=False):
    content: str
    embed: discord.Embed


class PageOption(discord.SelectOption, Generic[S_co]):
    """A select option that can store a nested page
    through the added `source=` kwarg.
    """

    def __init__(self, *args, source: S_co, **kwargs):
        super().__init__(*args, **kwargs)
        self.source = source


class PageSource(ABC, Generic[T, S_co, V_contra]):
    """The base page source class."""

    def __init__(self, *, current_index: int = 0):
        self.current_index = current_index

    @abstractmethod
    def get_page(self, index: int) -> Union[T, Coroutine[None, None, T]]:
        """Returns a page based on the given index.

        This method may be asynchronous.

        """

    @property
    def max_pages(self) -> int:
        """The max number of pages the page source can return.

        Can return 0 to disable the view entirely.

        """
        return 1

    def get_page_options(
        self,
        view: V_contra,
        page: T,
    ) -> Union[PO, Coroutine[None, None, PO]]:
        """Returns a list of page options for the user to select.

        This method may be asynchronous.

        """
        return []

    @abstractmethod
    def format_page(
        self,
        view: V_contra,
        page: T,
    ) -> Union[FP, Coroutine[None, None, FP]]:
        """Returns a dictionary presenting the items in the page.

        This method may be asynchronous.

        """


class ListPageSource(
    PageSource[List[E], S_co, V_contra],
    ABC,
    Generic[E, S_co, V_contra],
):
    """Paginates a list of elements."""

    def __init__(self, items: List[E], *args, page_size: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items
        self.page_size = page_size

    def get_page(self, index: int) -> List[E]:
        start = index * self.page_size
        return self.items[start : start + self.page_size]

    @functools.cached_property
    def max_pages(self) -> int:
        pages, remainder = divmod(len(self.items), self.page_size)
        return pages + bool(remainder)


class AsyncIteratorPageSource(
    PageSource[List[E], S_co, V_contra],
    ABC,
    Generic[E, S_co, V_contra],
):
    """Paginates an async iterator."""

    def __init__(self, iterator: AsyncIterator[E], *args, page_size: int, **kwargs):
        super().__init__(*args, **kwargs)
        self._cache: list[E] = []
        self._iterator = iterator
        self._max_index = 0
        self._exhausted = False
        self.page_size = page_size

    async def get_page(self, index: int) -> List[E]:
        start = index * self.page_size
        end = start + self.page_size
        if self._exhausted:
            return self._cache[start:end]

        # Get enough items to have at least one extra page
        # so paginator knows if next/last buttons should turn off
        required = end + self.page_size - len(self._cache)
        if required > 0:
            new_items = []
            max_index = index + 1
            for i in range(required):
                try:
                    new_items.append(await self._iterator.__anext__())
                except StopAsyncIteration:
                    max_index = math.ceil((len(self._cache) + i) / self.page_size)
                    self._exhausted = True
                    break
            self._cache.extend(new_items)
            self._max_index = max_index

        return self._cache[start:end]

    @property
    def max_pages(self) -> int:
        return self._max_index + (not self._exhausted)


class StopAction(Enum):
    """Specifies the action to take when the view is stopped."""

    NONE = auto()
    """On stop, no action will occur on the message."""
    DISABLE = auto()
    """On stop, all components will be disabled."""
    CLEAR = auto()
    """On stop, all components will be removed from the message."""
    DELETE = auto()
    """On stop, the message will be deleted."""


class TimeoutAction(Enum):
    """Specifies the action to take when the view times out."""

    NONE = auto()
    """On timeout, no action will occur on the message."""
    DISABLE = auto()
    """On timeout, all components will be disabled."""
    CLEAR = auto()
    """On timeout, all components will be removed from the message."""
    DELETE = auto()
    """On timeout, the message will be deleted."""


class PaginatorView(discord.ui.View, Generic[T, S_co, V_contra]):
    """A view that handles pagination and recursive levels of pages.

    To use this view, pass a PageSource or list of PageSources
    (the last one will be displayed first) to the `sources=` kwarg,
    then begin the paginator using `await view.start(channel)`.

    If adding the view to another message is desired,
    `view.message` must be manually set for it to be accessible.
    The initial page is not rendered until the user interacts
    with the paginator or is explicitly done with `await view.show_page()`.

    `interaction_check` by default will return True if `allowed_users`
    is None, or the interaction user is one of the allowed users.
    This may be extended to include an interaction response, or use
    different behavior entirely.

    Parameters
    ----------
    :param sources: The current stack of page sources.
    :param allowed_users: A collection of user IDs that are allowed
        to interact with this paginator. If None, any user can interact.
    :param stop_action:
        The action to do when the user clicks the stop button. This may
        not have any effect if a subclass overrides the `stop_button()`
        component.
    :param timeout_action:
        The action to do when the view times out. This may not have any
        effect if a subclass overrides the `on_timeout()` method.

    """

    def __init__(
        self,
        *args,
        sources: Union[
            Iterable[PageSource[T, S_co, V_contra]],
            PageSource[T, S_co, V_contra],
        ],
        allowed_users: Optional[Collection[int]] = None,
        stop_action: StopAction = StopAction.DELETE,
        timeout_action: TimeoutAction = TimeoutAction.CLEAR,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if isinstance(sources, PageSource):
            self.sources = [sources]
        else:
            self.sources = list(sources)
            if len(self.sources) == 0:
                raise ValueError("must provide at least one page source")
        self.allowed_users = allowed_users
        self.stop_action = stop_action
        self.timeout_action = timeout_action

        self.message: Optional[discord.Message] = None
        self.page: _PageParams = {}
        self.options: Sequence[PageOption[S_co]] = []
        self.option_sources: dict[str, PageSource] = {}

    @property
    def current_source(self) -> PageSource[T, S_co, V_contra]:
        return self.sources[-1]

    @property
    def current_index(self) -> int:
        return self.current_source.current_index

    @current_index.setter
    def current_index(self, index: int):
        self.current_source.current_index = index

    @property
    def can_navigate(self) -> bool:
        return len(self.options) > 0

    @property
    def can_paginate(self) -> bool:
        return self.current_source.max_pages > 1

    @property
    def can_go_back(self) -> bool:
        return len(self.sources) > 1

    @functools.cached_property
    def _pagination_buttons(self) -> Tuple[discord.ui.Button, ...]:
        return self.first_page, self.prev_page, self.next_page, self.last_page

    async def show_page(self, index: int) -> None:
        self.current_index = index
        maybe_coro = discord.utils.maybe_coroutine

        page = await maybe_coro(self.current_source.get_page, index)
        params = await maybe_coro(self.current_source.format_page, self, page)  # type: ignore
        if isinstance(params, str):
            params = {"content": params}
        elif isinstance(params, discord.Embed):
            params = {"embed": params}
        elif not isinstance(params, dict):
            raise TypeError("format_page() must return a dict, str, or Embed")
        self.page = cast(_PageParams, params)

        options: Sequence[PageOption[S_co]] = await maybe_coro(
            self.current_source.get_page_options, self, page  # type: ignore
        )
        option_sources = {}
        for i, option in enumerate(options):
            option.value = str(i)
            option_sources[option.value] = option.source
        self.options = options
        self.option_sources = option_sources

        self._refresh_components()

    async def start(
        self,
        channel: Union[discord.abc.Messageable, discord.Interaction],
        ephemeral: bool = True,
    ) -> None:
        await self.show_page(self.current_source.current_index)
        if isinstance(channel, discord.Interaction):
            kwargs = self._get_message_kwargs(initial_response=True)

            if channel.response.is_done():
                self.message = await channel.followup.send(
                    ephemeral=ephemeral,
                    wait=True,
                    **kwargs,
                )
            else:
                await channel.response.send_message(ephemeral=ephemeral, **kwargs)
                self.message = await channel.original_response()
        else:
            self.message = await channel.send(**self._get_message_kwargs())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.allowed_users is not None:
            return interaction.user.id in self.allowed_users
        return True

    async def on_timeout(self) -> None:
        action = self.timeout_action
        if self.message is None or action is TimeoutAction.NONE:
            return

        if action is TimeoutAction.CLEAR:
            await self.message.edit(view=None)
        elif action is TimeoutAction.DELETE:
            await self.message.delete()
        elif action is TimeoutAction.DISABLE:
            self._disable_components()
            await self.message.edit(view=self)
        else:
            raise TypeError(f"unknown timeout action: {action!r}")

    def _disable_components(self) -> None:
        for item in self.children:
            if hasattr(item, "disabled"):
                item.disabled = True  # type: ignore

    def _get_message_kwargs(self, *, initial_response: bool = False) -> Dict[str, Any]:
        # initial_response indicates if we can use view=None, necessary as
        # InteractionResponse.send_message() does not accept view=None
        kwargs = dict(self.page)
        max_pages = self.current_source.max_pages
        can_interact = self.can_navigate or self.can_paginate or self.can_go_back

        if max_pages > 0 and can_interact:
            kwargs["view"] = self
        else:
            self.stop()
            if not initial_response:
                kwargs["view"] = None

        return kwargs

    async def _respond(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(**self._get_message_kwargs())

    # noinspection PyUnresolvedReferences
    def _refresh_components(self) -> None:
        """Update the state of each component in this view according to
        the current source and page.

        The pagination and back/stop buttons will be organized one of four ways:

        1. No pagination, no previous source::
            STOP
        2. No pagination, previous source::
            BACK STOP
        3. Pagination, no previous source::
            FIRST PREV NEXT LAST STOP
        4. Pagination, previous source::
            FIRST PREV NEXT LAST STOP
            BACK

        This applies the same when navigation is enabled.

        """
        self.clear_items()

        # Navigation (select menu)
        if self.can_navigate:
            self.add_item(self.navigate)
            self.navigate.options = list(self.options)

        # Pagination (left/right)
        if self.can_paginate:
            for button in self._pagination_buttons:
                self.add_item(button)

        on_first_page = self.current_index == 0
        on_last_page = self.current_index + 1 >= self.current_source.max_pages
        self.first_page.disabled = on_first_page
        self.prev_page.disabled = on_first_page
        self.next_page.disabled = on_last_page
        self.last_page.disabled = on_last_page

        # Back and stop buttons
        if self.can_go_back:
            self.back_button.row = 1 + self.can_paginate
            self.add_item(self.back_button)
        self.add_item(self.stop_button)

    @discord.ui.select(options=[], placeholder="Navigate...", row=0)
    async def navigate(
        self,
        interaction: discord.Interaction,
        select: discord.ui.Select,
    ) -> None:
        source = self.option_sources[select.values[0]]
        self.sources.append(source)
        await self.show_page(self.current_index)
        await self._respond(interaction)

    @discord.ui.button(
        emoji="\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def first_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.show_page(0)
        await self._respond(interaction)

    @discord.ui.button(
        emoji="\N{BLACK LEFT-POINTING TRIANGLE}",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def prev_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.show_page(self.current_index - 1)
        await self._respond(interaction)

    @discord.ui.button(
        emoji="\N{BLACK RIGHT-POINTING TRIANGLE}",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def next_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.show_page(self.current_index + 1)
        await self._respond(interaction)

    @discord.ui.button(
        emoji="\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}",
        style=discord.ButtonStyle.blurple,
        row=1,
    )
    async def last_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.show_page(self.current_source.max_pages - 1)
        await self._respond(interaction)

    @discord.ui.button(
        emoji="\N{THUMBS UP SIGN}",
        style=discord.ButtonStyle.success,
        row=1,
    )
    async def stop_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        action = self.stop_action
        self.stop()

        if action is StopAction.NONE:
            return
        elif action is StopAction.CLEAR:
            await interaction.response.edit_message(view=None)
        elif action is StopAction.DELETE:
            await interaction.response.defer()
            await interaction.delete_original_response()
        elif action is StopAction.DISABLE:
            self._disable_components()
            await interaction.response.edit_message(view=self)
        else:
            raise TypeError(f"unknown stop action: {action!r}")

    @discord.ui.button(
        emoji="\N{LEFTWARDS ARROW WITH HOOK}",
        style=discord.ButtonStyle.blurple,
        row=2,
    )
    async def back_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        self.sources.pop()
        await self.show_page(self.current_index)
        await self._respond(interaction)
