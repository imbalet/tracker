from typing import Self

from aiogram.fsm.context import FSMContext
from pydantic import BaseModel


class StateModel(BaseModel):
    async def save(self, state: FSMContext):
        await state.update_data(self.model_dump(exclude_unset=True, exclude_none=False))

    @classmethod
    async def load(cls, state: FSMContext) -> Self:
        data = await state.get_data()
        return cls.model_validate(data)
