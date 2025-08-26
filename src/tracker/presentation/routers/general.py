from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from tracker.presentation.constants.text import Language, MsgKey
from tracker.presentation.utils import TFunction
from tracker.services.database import UserService

router = Router(name=__name__)


@router.message(Command("start"))
async def start_tracker_creation(
    message: Message, user_service: UserService, t: TFunction, lang: Language
) -> None:
    user = await user_service.get(str(message.chat.id))
    if user is None:
        user = await user_service.create(str(message.chat.id))
    await message.answer(t(MsgKey.G_WELCOME))
