# flake8: noqa
from enum import Enum
from typing import Literal

Language = Literal["ru", "en"]


class MsgKey(str, Enum):
    DATE_YEARS = "date_years"
    DATE_MONTHS = "date_months"
    DATE_WEEKS = "date_weeks"
    DATE_DAYS = "date_days"
    DATE_HOURS = "date_hours"
    DATE_MINUTES = "date_minutes"

    KBR_ADD_FIELD = "kbr_add_field"
    KBR_GET_DATA = "kbr_get_data"
    KBR_GET_CSV = "kbr_get_csv"
    KBR_PLOT_GRAPH = "kbr_plot_graph"
    KBR_GET_STATISTICS = "kbr_get_statistics"
    KBR_GET_TABLE = "kbr_get_table"
    KBR_DATE_YEARS = "kbr_date_years"
    KBR_DATE_MONTHS = "kbr_date_months"
    KBR_DATE_WEEKS = "kbr_date_weeks"
    KBR_DATE_DAYS = "kbr_date_days"
    KBR_DATE_HOURS = "kbr_date_hours"
    KBR_DATE_MINUTES = "kbr_date_minutes"

    CANCEL = "cancel"
    BACK = "back"
    CONFIRM = "confirm"

    CR_ENTER_NAME = "cr_enter_name"
    CR_AT_LEAST_ONE_SYM = "cr_at_least_one_symbol"
    CR_CREATING = "cr_creating_tracker"
    CR_SELECTED = "cr_selected"
    CR_SELECTED_ENUM = "cr_selected_enum"
    CR_EMPTY_ENUM = "cr_empty_enum"
    CR_ENUM_WRONG_COUNT = "cr_enum_wrong_count"
    CR_SELECTED_ENUM_VALUES = "cr_selected_enum_values"
    CR_NO_FIELD_NAME = "cr_no_field_name"
    CR_FIELD_NAME_EXISTS = "cr_field_name_exists"
    CR_FIELD_NAME_EXISTS_ENUM = "cr_field_name_exists_enum"
    CR_AT_LEAST_ONE_FIELD_REQUIRED = "cr_at_least_one_field_required"
    CR_CREATED = "cr_created"
    CR_CANCELED = "cr_canceled"

    G_WELCOME = "welcome"

    DT_SELECT_ACTION = "dt_select_action"
    DT_SELECT_PERIOD_TYPE = "dt_select_period_type"
    DT_PERIOD_ENTER_NUMBER = "dt_enter_number"
    DT_WRONG_VALUE = "dt_wrong_value"
    DT_SENDING_CSV = "dt_sending_csv"
    DT_SELECT_FIELDS = "dt_select_fields"
    DT_SELECTED_FIELDS = "dt_selected_fields"

    TR_NO_TRACKERS = "tr_no_trackers"
    TR_TRACKERS = "tr_trackers"
    TR_TRACKER_NOT_FOUND = "tr_tracker_not_found"
    TR_TRACKER_NOT_ENTERED = "tr_tracker_not_entered"
    TR_TRACKER_NAME_NOT_FOUND = "tr_tracker_name_not_found"
    TR_ENTER_FIELD_VALUE = "tr_enter_field_value"
    TR_DATA_SAVED = "tr_data_saved"
    TR_ADDING_DATA_CANCELED = "tr_adding_data_canceled"


TRANSLATIONS: dict[Language, dict[MsgKey, str]] = {
    "ru": {
        MsgKey.DATE_YEARS: "лет",
        MsgKey.DATE_MONTHS: "месяцев",
        MsgKey.DATE_WEEKS: "недель",
        MsgKey.DATE_DAYS: "дней",
        MsgKey.DATE_HOURS: "часов",
        MsgKey.DATE_MINUTES: "минут",
        MsgKey.KBR_ADD_FIELD: "Добавить поле",
        MsgKey.KBR_GET_DATA: "Получить данные",
        MsgKey.KBR_GET_CSV: "Получить CSV файл",
        MsgKey.KBR_PLOT_GRAPH: "Построить график",
        MsgKey.KBR_GET_STATISTICS: "Статистика",
        MsgKey.KBR_GET_TABLE: "Таблица",
        MsgKey.KBR_DATE_YEARS: "Года",
        MsgKey.KBR_DATE_MONTHS: "Месяцы",
        MsgKey.KBR_DATE_WEEKS: "Недели",
        MsgKey.KBR_DATE_DAYS: "Дни",
        MsgKey.KBR_DATE_HOURS: "Часы",
        MsgKey.KBR_DATE_MINUTES: "Минуты",
        MsgKey.CANCEL: "Отмена",
        MsgKey.BACK: "Назад",
        MsgKey.CONFIRM: "Готово",
        MsgKey.CR_ENTER_NAME: "Введите название трекера:",
        MsgKey.CR_AT_LEAST_ONE_SYM: "Имя должно состоять хотя бы из одного символа",
        MsgKey.CR_CREATING: "Создание трекера",
        MsgKey.CR_SELECTED: "Выбран тип: {type}\nВведите название поля:",
        MsgKey.CR_SELECTED_ENUM: "Выбран тип: {type}\nВведите значения поля через слеш `/`:",
        MsgKey.CR_EMPTY_ENUM: "Сообщение должно включать значения поля enum",
        MsgKey.CR_ENUM_WRONG_COUNT: "Значений enum должно быть более 1, получено {count}",
        MsgKey.CR_SELECTED_ENUM_VALUES: "Выбраны следующие значения enum: {enum_values}\nВведите название поля:",
        MsgKey.CR_NO_FIELD_NAME: "Сообщение должно включать название поля",
        MsgKey.CR_FIELD_NAME_EXISTS: "Имя '{name}' уже существует, выберите другое имя для поля {field_name}",
        MsgKey.CR_FIELD_NAME_EXISTS_ENUM: "Имя '{name}' уже существует, выберите другое имя для поля {field_name} со значениями {values}",
        MsgKey.CR_AT_LEAST_ONE_FIELD_REQUIRED: "Для сохранения в трекере должно быть хотя бы одно поле",
        MsgKey.CR_CREATED: "Трекер создан!\n\n{description}",
        MsgKey.CR_CANCELED: "Создание трекера отменено",
        MsgKey.G_WELCOME: "Привет. Это бот для трекинга",
        MsgKey.DT_SELECT_ACTION: "Выберите действие",
        MsgKey.DT_SELECT_PERIOD_TYPE: "Выберите единицу измерения периода",
        MsgKey.DT_PERIOD_ENTER_NUMBER: "Введите число {period_word}",
        MsgKey.DT_WRONG_VALUE: "Ошибочное значение",
        MsgKey.DT_SENDING_CSV: "Вам будет отправлен CSV файл с данными",
        MsgKey.DT_SELECT_FIELDS: "Выберите поля",
        MsgKey.DT_SELECTED_FIELDS: "Выбранные поля: {selected_fields}",
        MsgKey.TR_NO_TRACKERS: "У вас пока нет трекеров",
        MsgKey.TR_TRACKERS: "Трекеры:",
        MsgKey.TR_TRACKER_NOT_FOUND: "Трекер не найден",
        MsgKey.TR_TRACKER_NOT_ENTERED: "Ошибка: Не указан трекер!",
        MsgKey.TR_TRACKER_NAME_NOT_FOUND: "Трекер '{tracker_name}' не найден",
        MsgKey.TR_ENTER_FIELD_VALUE: "Введите значение поля {field_name}",
        MsgKey.TR_DATA_SAVED: "Все данные сохранены!",
        MsgKey.TR_ADDING_DATA_CANCELED: "Добавление данных отменено",
    },
    "en": {
        MsgKey.DATE_YEARS: "years",
        MsgKey.DATE_MONTHS: "months",
        MsgKey.DATE_WEEKS: "weeks",
        MsgKey.DATE_DAYS: "days",
        MsgKey.DATE_HOURS: "hours",
        MsgKey.DATE_MINUTES: "minutes",
        MsgKey.KBR_ADD_FIELD: "Add field",
        MsgKey.KBR_GET_DATA: "Get data",
        MsgKey.KBR_GET_CSV: "Get CSV file",
        MsgKey.KBR_PLOT_GRAPH: "Plot the graph",
        MsgKey.KBR_GET_STATISTICS: "Get statistics",
        MsgKey.KBR_GET_TABLE: "Get table",
        MsgKey.KBR_DATE_YEARS: "years",
        MsgKey.KBR_DATE_MONTHS: "months",
        MsgKey.KBR_DATE_WEEKS: "weeks",
        MsgKey.KBR_DATE_DAYS: "days",
        MsgKey.KBR_DATE_HOURS: "hours",
        MsgKey.KBR_DATE_MINUTES: "minutes",
        MsgKey.CANCEL: "Cancel",
        MsgKey.BACK: "Back",
        MsgKey.CONFIRM: "Done",
        MsgKey.CR_ENTER_NAME: "Enter tracker name:",
        MsgKey.CR_AT_LEAST_ONE_SYM: "The name must contain at least one character",
        MsgKey.CR_CREATING: "Creating tracker",
        MsgKey.CR_SELECTED: "Selected type: {type}\nEnter field name:",
        MsgKey.CR_SELECTED_ENUM: "Selected type: {type}\nEnter field values separated by `/`:",
        MsgKey.CR_EMPTY_ENUM: "The message must include enum field values",
        MsgKey.CR_ENUM_WRONG_COUNT: "Enum must contain more than 1 value, got {count}",
        MsgKey.CR_SELECTED_ENUM_VALUES: "The following enum values were selected: {enum_values}\nEnter field name:",
        MsgKey.CR_NO_FIELD_NAME: "The message must include a field name",
        MsgKey.CR_FIELD_NAME_EXISTS: "The name '{name}' already exists, choose another name for field {field_name}",
        MsgKey.CR_FIELD_NAME_EXISTS_ENUM: "The name '{name}' already exists, choose another name for field {field_name} with values {values}",
        MsgKey.CR_AT_LEAST_ONE_FIELD_REQUIRED: "At least one field is required to save the tracker",
        MsgKey.CR_CREATED: "Tracker created!\n\n{description}",
        MsgKey.CR_CANCELED: "Tracker creation canceled",
        MsgKey.G_WELCOME: "Hi. This is a tracking bot",
        MsgKey.DT_SELECT_ACTION: "Select an action",
        MsgKey.DT_SELECT_PERIOD_TYPE: "Select a period unit",
        MsgKey.DT_PERIOD_ENTER_NUMBER: "Enter the number of {period_word}",
        MsgKey.DT_WRONG_VALUE: "Invalid value",
        MsgKey.DT_SENDING_CSV: "You will be sent a CSV file with the data",
        MsgKey.DT_SELECT_FIELDS: "Select fields",
        MsgKey.DT_SELECTED_FIELDS: "Selected fields: {selected_fields}",
        MsgKey.TR_NO_TRACKERS: "You don’t have any trackers yet",
        MsgKey.TR_TRACKERS: "Trackers:",
        MsgKey.TR_TRACKER_NOT_FOUND: "Tracker not found",
        MsgKey.TR_TRACKER_NOT_ENTERED: "Error: Tracker not specified!",
        MsgKey.TR_TRACKER_NAME_NOT_FOUND: "Tracker '{tracker_name}' not found",
        MsgKey.TR_ENTER_FIELD_VALUE: "Enter a value for field {field_name}",
        MsgKey.TR_DATA_SAVED: "All data has been saved!",
        MsgKey.TR_ADDING_DATA_CANCELED: "Data entry canceled",
    },
}
