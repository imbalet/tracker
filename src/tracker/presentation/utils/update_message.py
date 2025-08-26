from aiogram.fsm.context import FSMContext
from aiogram.types import InaccessibleMessage, MaybeInaccessibleMessageUnion


async def update_main_message(
    state: FSMContext,
    message: MaybeInaccessibleMessageUnion,
    text: str,
    reply_markup=None,
    create_new: bool = False,
    **kwargs,
) -> None:
    if isinstance(message, InaccessibleMessage):
        bot = message.bot
        if bot:
            await bot.send_message(
                chat_id=message.chat.id,
                text="Сообщение недоступно",
            )
        return

    data = await state.get_data()
    main_message_id = data.get("main_message_id")

    if main_message_id and message.bot and not create_new:
        try:
            await message.bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=main_message_id,
                text=text,
                reply_markup=reply_markup,
                **kwargs,
            )
            if main_message_id != message.message_id:
                await message.delete()
            return
        except Exception:
            pass

    msg = await message.answer(text=text, reply_markup=reply_markup, **kwargs)
    await state.update_data(main_message_id=msg.message_id)
