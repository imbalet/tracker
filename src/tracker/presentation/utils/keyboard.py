from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from tracker.presentation.callbacks import (
    ActionCallback,
    BackCallback,
    CancelCallback,
    ConfirmCallback,
    EnumValuesCallback,
    FieldCallback,
    FieldTypeCallback,
    PeriodCallback,
    TrackerActionsCallback,
    TrackerCallback,
    TrackerDataActionsCallback,
)
from tracker.presentation.constants.text import MsgKey
from tracker.schemas import TrackerResponse

from .translations import TFunction


class InlineKeyboardFactory:
    def __init__(self, t: TFunction, row_width: int = 2):
        self._keyboard: list[list[InlineKeyboardButton]] = []
        self._current_row: list[InlineKeyboardButton] = []
        self._t = t
        self._row_width = row_width

    def _flush_row(self) -> "InlineKeyboardFactory":
        """Flushes the current row and starts a new one."""
        if self._current_row:
            self._keyboard.append(self._current_row)
            self._current_row = []
        return self

    def buttons_tuple(
        self, *buttons: tuple[MsgKey, CallbackData]
    ) -> "InlineKeyboardFactory":
        """Adds buttons from tuples.

        Args:
            *buttons (tuple[MsgKey, CallbackData]): tuples with text and callback.

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

    def button(
        self,
        text: MsgKey,
        callback_data: CallbackData,
        **kwargs,
    ) -> "InlineKeyboardFactory":
        """Adds a single button to the current row.

        Args:
            text (MsgKey): text of the button.
            cbdata (CallbackData): callback of the button.
        """
        btn = InlineKeyboardButton(
            text=self._t(text), callback_data=callback_data.pack(), **kwargs
        )
        self._current_row.append(btn)
        if len(self._current_row) >= self._row_width:
            self._flush_row()

        return self

    def button_text(
        self,
        text: str,
        callback_data: CallbackData,
        **kwargs,
    ) -> "InlineKeyboardFactory":
        """Adds a single button with pure text to the current row.

        Args:
            text (MsgKey): text of the button.
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
        self, *buttons: tuple[MsgKey, CallbackData]
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
                    InlineKeyboardButton(
                        text=self._t(text), callback_data=callback.pack()
                    )
                    for text, callback in buttons
                ]
            )
        return self

    def as_markup(self) -> InlineKeyboardMarkup:
        """Returns the inline keyboard markup."""
        self._flush_row()
        return InlineKeyboardMarkup(inline_keyboard=self._keyboard)


class KeyboardBuilder(InlineKeyboardFactory):

    def __init__(
        self,
        t: TFunction,
        row_width: int = 2,
        add_back_button: bool = False,
        add_cancel_button: bool = False,
        add_confirm_button: bool = False,
        extra_buttons: list[tuple[MsgKey, CallbackData]] | None = None,
    ):
        super().__init__(t, row_width)
        self._back_btn = add_back_button
        self._cancel_btn = add_cancel_button
        self._confirm_btn = add_confirm_button
        self._extra_btns = extra_buttons or []

    def conf(
        self,
        row_width: int = 2,
        add_back_button: bool = False,
        add_cancel_button: bool = False,
        add_confirm_button: bool = False,
        extra_buttons: list[tuple[MsgKey, CallbackData]] | None = None,
    ):
        self._row_width = row_width
        self._back_btn = add_back_button
        self._cancel_btn = add_cancel_button
        self._confirm_btn = add_confirm_button
        self._extra_btns = extra_buttons or []
        return self

    def as_markup(self) -> InlineKeyboardMarkup:
        service_buttons: list[tuple[MsgKey, CallbackData]] = []
        if self._back_btn:
            service_buttons.append((MsgKey.BACK, BackCallback()))
        if self._cancel_btn:
            service_buttons.append((MsgKey.CANCEL, CancelCallback()))
        if self._confirm_btn:
            service_buttons.append((MsgKey.CONFIRM, ConfirmCallback()))
        self.row_buttons_tuple(*service_buttons)
        self.row_buttons_tuple(*self._extra_btns)
        return super().as_markup()

    @staticmethod
    def markup(func):
        def wrapper(self, *args, **kwargs):
            func(self, *args, **kwargs)
            return self.as_markup()

        return wrapper

    @markup
    def build_field_type_keyboard(self):
        for text in ["int", "float", "enum", "string"]:
            self.button_text(
                text,
                FieldTypeCallback(type=text),  # type: ignore
            )

    @markup
    def build_action_keyboard(self):
        (
            self.button(
                text=MsgKey.KBR_ADD_FIELD,
                callback_data=ActionCallback(action="add_field"),
            ).row_buttons_tuple(
                (MsgKey.CONFIRM, ActionCallback(action="finish")),
                (MsgKey.CANCEL, CancelCallback()),
            )
        )

    @markup
    def build_trackers_keyboard(self, trackers: list[TrackerResponse]):
        for i in trackers:
            self.button_text(text=i.name, callback_data=TrackerCallback(id=i.id))

    @markup
    def build_tracker_fields_keyboard(
        self,
        tracker: TrackerResponse,
        exclude_fields: set[str] | None = None,
        marked_fields: set[str] | None = None,
        mark: str = "",
    ):
        for name, props in tracker.structure.data.items():
            if exclude_fields and name in exclude_fields:
                continue
            value = (
                props["type"] if props["type"] != "enum" else ", ".join(props["values"])  # type: ignore
            )
            button_text = f"{name}: {value}"
            if marked_fields and name in marked_fields:
                button_text = mark + button_text
            self.button_text(
                text=button_text,
                callback_data=FieldCallback(name=name, type=props["type"]),
            )

    @markup
    def build_tracker_action_keyboard(self):
        (
            self.button(
                text=MsgKey.KBR_GET_DATA,
                callback_data=TrackerActionsCallback(action="get_options"),
            )
        )

    @markup
    def build_tracker_data_action_keyboard(self):
        (
            self.button(
                text=MsgKey.KBR_GET_CSV,
                callback_data=TrackerDataActionsCallback(action="csv"),
            )
            .button(
                text=MsgKey.KBR_PLOT_GRAPH,
                callback_data=TrackerDataActionsCallback(action="graph"),
            )
            .button(
                text=MsgKey.KBR_GET_STATISTICS,
                callback_data=TrackerDataActionsCallback(action="statistics"),
            )
            .button(
                text=MsgKey.KBR_GET_TABLE,
                callback_data=TrackerDataActionsCallback(action="table"),
            )
        )

    @markup
    def build_period_keyboard(self):
        (
            self.button(
                text=MsgKey.KBR_DATE_YEARS,
                callback_data=PeriodCallback(period="years"),
            )
            .button(
                text=MsgKey.KBR_DATE_MONTHS,
                callback_data=PeriodCallback(period="months"),
            )
            .button(
                text=MsgKey.KBR_DATE_WEEKS,
                callback_data=PeriodCallback(period="weeks"),
            )
            .button(
                text=MsgKey.KBR_DATE_DAYS,
                callback_data=PeriodCallback(period="days"),
            )
            .button(
                text=MsgKey.KBR_DATE_HOURS,
                callback_data=PeriodCallback(period="hours"),
            )
            .button(
                text=MsgKey.KBR_DATE_MINUTES,
                callback_data=PeriodCallback(period="minutes"),
            )
        )

    @markup
    def build_enum_values_keyboard(self, values: list[str]):
        for i in values:
            self.button_text(text=i, callback_data=EnumValuesCallback(value=i))
