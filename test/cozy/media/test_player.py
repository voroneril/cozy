from unittest.mock import MagicMock, call

import pytest
from peewee import SqliteDatabase

from cozy.application_settings import ApplicationSettings
from cozy.ext import inject
from cozy.media.gst_player import GstPlayer
from cozy.model.library import Library
from cozy.model.settings import Settings


@pytest.fixture(autouse=True)
def setup_inject(peewee_database):
    inject.clear_and_configure(lambda binder: binder
                               .bind(SqliteDatabase, peewee_database)
                               .bind_to_constructor("FilesystemMonitor", MagicMock())
                               .bind_to_constructor(GstPlayer, MagicMock())
                               .bind_to_constructor(ApplicationSettings, MagicMock())
                               .bind_to_constructor(Library, lambda: Library())
                               .bind_to_constructor(Settings, lambda: Settings()))

    yield
    inject.clear()


def test_initializing_player_loads_last_book(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_in_book")
    library = inject.instance(Library)
    library.last_played_book = library.books[0]

    player = Player()

    assert player._book == library.last_played_book


def test_loading_new_book_loads_chapter_and_book(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_in_book")
    library = inject.instance(Library)
    player = Player()

    book = library.books[0]
    player._continue_book(book)

    assert player._book == book
    assert player._book.current_chapter == book.current_chapter


def test_loading_new_book_emits_changed_event(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_in_book")
    library = inject.instance(Library)
    player = Player()
    spy = mocker.spy(player, "emit_event")

    book = library.books[2]
    player._continue_book(book)

    spy.assert_has_calls(calls=[call("chapter-changed", book)])


def test_loading_new_chapter_loads_chapter(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_in_book")
    library = inject.instance(Library)
    player = Player()

    book = library.books[0]
    player._load_chapter(book.current_chapter)

    assert player._book.current_chapter == book.current_chapter


def test_loading_new_chapter_sets_playback_speed(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_in_book")
    library = inject.instance(Library)
    player = Player()

    book = library.books[0]
    book.playback_speed = 2.5
    player._load_chapter(book.current_chapter)
    print(player.playback_speed)

    assert player.playback_speed == book.playback_speed



def test_loading_new_chapter_emits_changed_event(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_in_book")
    library = inject.instance(Library)
    player = Player()
    spy = mocker.spy(player, "emit_event")

    book = library.books[1]
    player._book = book
    player._load_chapter(book.chapters[1])

    spy.assert_has_calls(calls=[call('chapter-changed', book)])


def test_emit_tick_does_not_emit_tick_when_nothing_is_loaded(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._load_last_book")
    player = Player()
    spy = mocker.spy(player, "emit_event_main_thread")
    player._emit_tick()

    spy.assert_not_called()


def test_emit_tick_does_emit_tick_on_startup_when_last_book_is_loaded(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._rewind_feature")
    player = Player()
    spy = mocker.spy(player, "emit_event_main_thread")
    player._emit_tick()

    spy.assert_has_calls(calls=[call('position', player.loaded_chapter.position)])


def test_rewind_in_book_does_not_rewind_if_no_book_is_loaded(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._load_last_book")
    player = Player()

    player._rewind_in_book()


def test_forward_in_book_does_not_forward_if_no_book_is_loaded(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._load_last_book")
    player = Player()

    player._forward_in_book()


def test_load_book_does_not_load_book_if_it_is_none(mocker):
    from cozy.media.player import Player

    mocker.patch("cozy.media.player.Player._load_last_book")
    player = Player()
    player._load_book(None)

    assert player.loaded_book is None
