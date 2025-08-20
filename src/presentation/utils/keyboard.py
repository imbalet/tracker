from typing import Any, Mapping

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from src.presentation.callbacks import (
    ActionCallback,
    CancelCallback,
    FieldCallback,
    FieldTypeCallback,
    PeriodCallback,
    TrackerActionsCallback,
    TrackerCallback,
    TrackerDataActionsCallback,
)
from src.schemas import TrackerResponse

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
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    for text in ["int", "float", "enum", "string"]:
        builder.button(text, FieldTypeCallback(type=text))  # type: ignore
    builder.row_buttons_tuple(*extra_buttons)
    return builder.as_markup()


def build_action_keyboard(
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text="Добавить поле", callback_data=ActionCallback(action="add_field")
        )
        .row_buttons_tuple(
            ("Завершить", ActionCallback(action="finish")),
            ("Отменить", CancelCallback()),
        )
        .row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_trackers_keyboard(
    trackers: list[TrackerResponse],
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
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text="Получить данные",
            callback_data=TrackerActionsCallback(action="get_options"),
        ).row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_tracker_data_action_keyboard(
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(
            text="Получить CSV файл",
            callback_data=TrackerDataActionsCallback(action="csv"),
        )
        .button(
            text="Построить график",
            callback_data=TrackerDataActionsCallback(action="graph"),
        )
        .button(
            text="Статистика",
            callback_data=TrackerDataActionsCallback(action="statistics"),
        )
        .button(
            text="Таблица",
            callback_data=TrackerDataActionsCallback(action="table"),
        )
        .row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()


def build_period_keyboard(
    extra_buttons: list[tuple[str, CallbackData]] | None = None,
):
    extra_buttons = extra_buttons or []
    builder = InlineKeyboardFactory()
    (
        builder.button(text="Года", callback_data=PeriodCallback(period="years"))
        .button(text="Месяцы", callback_data=PeriodCallback(period="months"))
        .button(text="Недели", callback_data=PeriodCallback(period="weeks"))
        .button(text="Дни", callback_data=PeriodCallback(period="days"))
        .button(text="Часы", callback_data=PeriodCallback(period="hours"))
        .button(text="Минуты", callback_data=PeriodCallback(period="minutes"))
        .row_buttons_tuple(*extra_buttons)
    )
    return builder.as_markup()
