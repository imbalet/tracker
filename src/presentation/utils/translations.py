from src.presentation.constants.text import TRANSLATIONS, Language, MsgKey


def t(lang: Language, key: MsgKey, **kwargs) -> str:
    text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["en"].get(key, key.value)
    return text.format(**kwargs) if kwargs else text
