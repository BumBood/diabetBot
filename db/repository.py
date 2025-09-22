from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime
from db.models import User, FCI, MealRecord, AdditionalInjection, MealType, InsulinRecord, InsulinType


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        """Получить или создать пользователя"""
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()

        if not user:
            user = User(telegram_id=telegram_id, username=username, first_name=first_name, last_name=last_name)
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)

        return user

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        result = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


class FCIRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, date: date, value: float) -> FCI:
        fci = FCI(user_id=user_id, date=date, value=value)
        self.session.add(fci)
        await self.session.commit()
        await self.session.refresh(fci)
        return fci

    async def get_by_date(self, user_id: int, date: date) -> Optional[FCI]:
        result = await self.session.execute(select(FCI).where(and_(FCI.user_id == user_id, FCI.date == date)))
        return result.scalar_one_or_none()

    async def get_latest(self, user_id: int) -> Optional[FCI]:
        result = await self.session.execute(
            select(FCI).where(FCI.user_id == user_id).order_by(desc(FCI.date)).limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[FCI]:
        result = await self.session.execute(
            select(FCI)
            .where(and_(FCI.user_id == user_id, FCI.date >= start_date, FCI.date <= end_date))
            .order_by(FCI.date)
        )
        return list(result.scalars().all())


class MealRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, **kwargs) -> MealRecord:
        meal_record = MealRecord(user_id=user_id, **kwargs)
        self.session.add(meal_record)
        await self.session.commit()
        await self.session.refresh(meal_record)
        return meal_record

    async def get_by_date(self, user_id: int, date: date) -> List[MealRecord]:
        result = await self.session.execute(
            select(MealRecord)
            .where(and_(MealRecord.user_id == user_id, MealRecord.date == date))
            .order_by(MealRecord.created_at)
        )
        return list(result.scalars().all())

    async def get_by_date_and_meal(self, user_id: int, date: date, meal_type: MealType) -> Optional[MealRecord]:
        result = await self.session.execute(
            select(MealRecord).where(
                and_(MealRecord.user_id == user_id, MealRecord.date == date, MealRecord.meal_type == meal_type)
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_by_meal_type(self, user_id: int, meal_type: MealType) -> Optional[MealRecord]:
        result = await self.session.execute(
            select(MealRecord)
            .where(and_(MealRecord.user_id == user_id, MealRecord.meal_type == meal_type))
            .order_by(desc(MealRecord.date))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[MealRecord]:
        result = await self.session.execute(
            select(MealRecord)
            .where(and_(MealRecord.user_id == user_id, MealRecord.date >= start_date, MealRecord.date <= end_date))
            .order_by(MealRecord.date, MealRecord.created_at)
        )
        return list(result.scalars().all())


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
        return list(result.scalars().all())


class InsulinRecordRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, date: date, insulin_type: InsulinType, amount: float) -> InsulinRecord:
        """Создать запись об инсулине"""
        record = InsulinRecord(user_id=user_id, date=date, insulin_type=insulin_type, amount=amount)
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_by_date(self, user_id: int, date: date) -> List[InsulinRecord]:
        """Получить все записи инсулина за конкретную дату"""
        result = await self.session.execute(
            select(InsulinRecord)
            .where(and_(InsulinRecord.user_id == user_id, InsulinRecord.date == date))
            .order_by(InsulinRecord.created_at)
        )
        return list(result.scalars().all())

    async def get_total_by_date(self, user_id: int, date: date) -> float:
        """Получить общее количество ультракороткого инсулина за дату (на еду + коррекции)"""
        result = await self.session.execute(
            select(InsulinRecord.amount).where(and_(InsulinRecord.user_id == user_id, InsulinRecord.date == date))
        )
        amounts = result.scalars().all()
        return sum(amounts) if amounts else 0.0

    async def get_by_date_range(self, user_id: int, start_date: date, end_date: date) -> List[InsulinRecord]:
        """Получить записи инсулина за период"""
        result = await self.session.execute(
            select(InsulinRecord)
            .where(
                and_(
                    InsulinRecord.user_id == user_id, InsulinRecord.date >= start_date, InsulinRecord.date <= end_date
                )
            )
            .order_by(InsulinRecord.date, InsulinRecord.created_at)
        )
        return list(result.scalars().all())

    async def get_total_by_date_range(self, user_id: int, start_date: date, end_date: date) -> dict[date, float]:
        """Получить общее количество инсулина по дням за период"""
        records = await self.get_by_date_range(user_id, start_date, end_date)
        totals: dict[date, float] = {}
        for record in records:
            if record.date not in totals:
                totals[record.date] = 0.0
            totals[record.date] += record.amount
        return totals
