from typing import Any, Protocol

from tracker.presentation.constants.text import TRANSLATIONS, Language, MsgKey


class TFunction(Protocol):
    def __call__(self, key: str, **kwargs: Any) -> str: ...


def _t(lang: Language, key: MsgKey, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key, key.value)
    return text.format(**kwargs) if kwargs else text
