from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime
from db.models import FCI, MealRecord, AdditionalInjection, MealType


class FCIRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, date: date, value: float) -> FCI:
        fci = FCI(date=date, value=value)
        self.session.add(fci)
        await self.session.commit()
        await self.session.refresh(fci)
        return fci

    async def get_by_date(self, date: date) -> Optional[FCI]:
        result = await self.session.execute(select(FCI).where(FCI.date == date))
        return result.scalar_one_or_none()

    async def get_latest(self) -> Optional[FCI]:
        result = await self.session.execute(select(FCI).order_by(desc(FCI.date)).limit(1))
        return result.scalar_one_or_none()

    async def get_by_date_range(self, start_date: date, end_date: date) -> List[FCI]:
        result = await self.session.execute(
            select(FCI).where(and_(FCI.date >= start_date, FCI.date <= end_date)).order_by(FCI.date)
        )
        return result.scalars().all()


class MealRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, **kwargs) -> MealRecord:
        meal_record = MealRecord(**kwargs)
        self.session.add(meal_record)
        await self.session.commit()
        await self.session.refresh(meal_record)
        return meal_record

    async def get_by_date(self, date: date) -> List[MealRecord]:
        result = await self.session.execute(
            select(MealRecord).where(MealRecord.date == date).order_by(MealRecord.created_at)
        )
        return result.scalars().all()

    async def get_by_date_and_meal(self, date: date, meal_type: MealType) -> Optional[MealRecord]:
        result = await self.session.execute(
            select(MealRecord).where(and_(MealRecord.date == date, MealRecord.meal_type == meal_type))
        )
        return result.scalar_one_or_none()

    async def get_latest_by_meal_type(self, meal_type: MealType) -> Optional[MealRecord]:
        result = await self.session.execute(
            select(MealRecord).where(MealRecord.meal_type == meal_type).order_by(desc(MealRecord.date)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(self, start_date: date, end_date: date) -> List[MealRecord]:
        result = await self.session.execute(
            select(MealRecord)
            .where(and_(MealRecord.date >= start_date, MealRecord.date <= end_date))
            .order_by(MealRecord.date, MealRecord.created_at)
        )
        return result.scalars().all()


class AdditionalInjectionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self, meal_record_id: int, time_from_meal: int, dose: float, dose_corrected: float
    ) -> AdditionalInjection:
        injection = AdditionalInjection(
            meal_record_id=meal_record_id, time_from_meal=time_from_meal, dose=dose, dose_corrected=dose_corrected
        )
        self.session.add(injection)
        await self.session.commit()
        await self.session.refresh(injection)
        return injection

    async def get_by_meal_record(self, meal_record_id: int) -> List[AdditionalInjection]:
        result = await self.session.execute(
            select(AdditionalInjection).where(AdditionalInjection.meal_record_id == meal_record_id)
        )
        return result.scalars().all()
