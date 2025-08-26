# multiple uses
ST_TRACKER_ID = "tracker_id"  # uuid of a selected tracker

# tracking
ST_TR_CURRENT_TRACKER = "current_tracker"  # json dump of a selected tracker
ST_TR_CURRENT_FIELD = "current_field"  # name of a selected field
ST_TR_FIELD_VALUES = "field_values"  # dict with field names and values

# getting data
ST_DT_ACTION = "action"  # data action (get csv, get statistics, ...)
ST_DT_PERIOD_TYPE = "period_type"  # type of time period (minutes, days, ...)
ST_DT_PERIOD_VALUE = "period_value"  # value of time period, int
ST_DT_SELECTED_FIELDS = "selected_fields"  # list of selected fields for getting data

# creating tracker
ST_CR_TRACKER = "tracker"  # structure of a tracker
ST_CR_CUR_FIELD_TYPE = "current_field_type"  # type of a current field (int, enum, ...)
ST_CR_CUR_ENUM_VALUES = (
    "current_enum_values"  # enum values for a current enum type (ONLY FOR ENUM TYPE)
)
