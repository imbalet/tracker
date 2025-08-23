from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from src.presentation.constants.text import Language, MsgKey
from src.presentation.middleware import CallbackMessageMiddleware
from src.presentation.utils import TFunction
from src.services.database import UserService

router = Router(name=__name__)
router.callback_query.middleware(CallbackMessageMiddleware())


@router.message(Command("start"))
async def start_tracker_creation(
    message: Message, user_service: UserService, t: TFunction, lang: Language
) -> None:
    user = await user_service.get(str(message.chat.id))
    if user is None:
        user = await user_service.create(str(message.chat.id))
    await message.answer(t(MsgKey.G_WELCOME))
