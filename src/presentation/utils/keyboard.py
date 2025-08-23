from typing import Any, Mapping

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from src.presentation.callbacks import (
    ActionCallback,
    CancelCallback,
    EnumValuesCallback,
    FieldCallback,
    FieldTypeCallback,
    PeriodCallback,
    TrackerActionsCallback,
    TrackerCallback,
    TrackerDataActionsCallback,
)
from src.presentation.constants.text import Language, MsgKey
from src.schemas import TrackerResponse

from .translations import _t

__all__ = [
    "build_field_type_keyboard",
    "build_action_keyboard",
    "build_trackers_keyboard",
    "build_tracker_fields_keyboard",
    "build_tracker_action_keyboard",
    "build_tracker_data_action_keyboard",
    "build_period_keyboard",
]


class InlineKeyboardFactory:
    def __init__(self, row_width: int = 2):
        self._keyboard: list[list[InlineKeyboardButton]] = []
        self._current_row: list[InlineKeyboardButton] = []
        self._row_width = row_width

    def _flush_row(self) -> "InlineKeyboardFactory":
        """Flushes the current row and starts a new one."""
        if self._current_row:
            self._keyboard.append(self._current_row)
            self._current_row = []
        return self

    def buttons_tuple(
        self, *buttons: tuple[str, CallbackData]
    ) -> "InlineKeyboardFactory":
        """Adds buttons from tuples.

        Args:
            *buttons (tuple[str, CallbackData]): tuples with text and callback.

        """
        for text, callback in buttons:
            self.button(text=text, callback_data=callback)
        return self

    def buttons(self, *buttons: InlineKeyboardButton) -> "InlineKeyboardFactory":
        """Adds buttons.

        Args:
            *buttons (InlineKeyboardButton): button objects.
        """
        for btn in buttons:
            self._current_row.append(btn)
            if len(self._current_row) >= self._row_width:
                self._flush_row()
        return self

    def same_callback_buttons_with_data(
        self,
        callback_type: type[CallbackData],
        **buttons: Mapping[str, dict[str, Any]],
    ) -> "InlineKeyboardFactory":
        """Adds multiple buttons with the same callback type.

        Args:
            callback_type: CallbackData class.
            **text_to_data: dict with button text key and callback parameters dict value.
        """
        for text, data in buttons.items():
            cbdata = callback_type(**data)
            self.button(text=text, callback_data=cbdata)
        return self

    def button(
        self,
        text: str,
        callback_data: CallbackData,
        **kwargs,
    ) -> "InlineKeyboardFactory":
        """Adds a single button to the current row.

        Args:
            text (str): text of the button.
            cbdata (CallbackData): callback of the button.
        """
        btn = InlineKeyboardButton(
            text=text, callback_data=callback_data.pack(), **kwargs
        )
        self._current_row.append(btn)
        if len(self._current_row) >= self._row_width:
            self._flush_row()

        return self

    def row_buttons(self, *buttons: InlineKeyboardButton) -> "InlineKeyboardFactory":
        """Flushes the current row and adds a new row of buttons.

        Args:
            *buttons (InlineKeyboardButton): button objects.
        """
        if self._current_row:
            self._flush_row()

        if buttons:
            self._keyboard.append(list(buttons))
        return self

    def row_buttons_tuple(
        self, *buttons: tuple[str, CallbackData]
    ) -> "InlineKeyboardFactory":
        """Flushes the current row and adds a new row of buttons from tuples.

        Args:
            *buttons (tuple[str, CallbackData]): tuples with text and callback.
        """
        if self._current_row:
            self._flush_row()

        if buttons:
            self._keyboard.append(
                [
                    InlineKeyboardButton(text=text, callback_data=callback.pack())
                    for text, callback in buttons
                ]
            )
        return self

    def as_markup(self) -> InlineKeyboardMarkup:
        """Returns the inline keyboard markup."""
        self._flush_row()
        return InlineKeyboardMarkup(inline_keyboard=self._keyboard)


def build_field_type_keyboard(
    lang: Language,
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    for text in ["int", "float", "enum", "string"]:
        builder.button(text, FieldTypeCallback(type=text))  # type: ignore
    builder.row_buttons_tuple(*extra_buttons)
    return builder.as_markup()


def build_action_keyboard(
    lang: Language, extra_buttons: list[tuple[str, CallbackData]] | None = None
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text=_t(lang, MsgKey.KBR_ADD_FIELD),
            callback_data=ActionCallback(action="add_field"),
        )
        .row_buttons_tuple(
            (_t(lang, MsgKey.CONFIRM), ActionCallback(action="finish")),
            (_t(lang, MsgKey.CANCEL), CancelCallback()),
        )
        .row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_trackers_keyboard(
    trackers: list[TrackerResponse],
    lang: Language,
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    for i in trackers:
        builder.button(text=i.name, callback_data=TrackerCallback(id=i.id))
    builder.row_buttons_tuple(*extra_buttons)
    return builder.as_markup()


def build_tracker_fields_keyboard(
    tracker: TrackerResponse,
    lang: Language,
    exclude_fields: set[str] | None = None,
    marked_fields: set[str] | None = None,
    mark: str = "",
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    for name, props in tracker.structure.data.items():
        if exclude_fields and name in exclude_fields:
            continue
        button_text = f"{name}: {props['type'] if props['type'] != 'enum' else props['values']}"  # type: ignore
        if marked_fields and name in marked_fields:
            button_text = mark + button_text
        builder.button(
            text=button_text,
            callback_data=FieldCallback(name=name, type=props["type"]),
        )
    builder.row_buttons_tuple(*extra_buttons)
    return builder.as_markup()


def build_tracker_action_keyboard(
    lang: Language, extra_buttons: list[tuple[str, CallbackData]] | None = None
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text=_t(lang, MsgKey.KBR_GET_DATA),
            callback_data=TrackerActionsCallback(action="get_options"),
        ).row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_tracker_data_action_keyboard(
    lang: Language, extra_buttons: list[tuple[str, CallbackData]] | None = None
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text=_t(lang, MsgKey.KBR_GET_CSV),
            callback_data=TrackerDataActionsCallback(action="csv"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_PLOT_GRAPH),
            callback_data=TrackerDataActionsCallback(action="graph"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_GET_STATISTICS),
            callback_data=TrackerDataActionsCallback(action="statistics"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_GET_TABLE),
            callback_data=TrackerDataActionsCallback(action="table"),
        )
        .row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_period_keyboard(
    lang: Language, extra_buttons: list[tuple[str, CallbackData]] | None = None
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text=_t(lang, MsgKey.KBR_DATE_YEARS),
            callback_data=PeriodCallback(period="years"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_DATE_MONTHS),
            callback_data=PeriodCallback(period="months"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_DATE_WEEKS),
            callback_data=PeriodCallback(period="weeks"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_DATE_DAYS),
            callback_data=PeriodCallback(period="days"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_DATE_HOURS),
            callback_data=PeriodCallback(period="hours"),
        )
        .button(
            text=_t(lang, MsgKey.KBR_DATE_MINUTES),
            callback_data=PeriodCallback(period="minutes"),
        )
        .row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_enum_values_keyboard(
    values: list[str],
    lang: Language,
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()

    for i in values:
        builder.button(text=i, callback_data=EnumValuesCallback(value=i))
    builder.row_buttons_tuple(*extra_buttons)
    return builder.as_markup()
