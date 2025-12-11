"""
Модели базы данных
"""
from datetime import datetime
from sqlalchemy import BigInteger, String, Numeric, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from backend.db.database import Base


class TransactionType(str, enum.Enum):
    """Тип транзакции"""
    INCOME = "income"  # Пополнение
    EXPENSE = "expense"  # Расход


class Family(Base):
    """Семья - общий кошелек"""
    __tablename__ = "families"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=True)  # Название семьи (опционально)
    current_balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<Family(id={self.id}, name={self.name}, balance={self.current_balance})>"


class User(Base):
    """Пользователь бота"""
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str] = mapped_column(String(255), nullable=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=True)
    family_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('families.id'), nullable=True)
    # Старое поле для обратной совместимости (больше не используется)
    current_balance: Mapped[float] = mapped_column(Numeric(15, 2), nullable=True, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, family_id={self.family_id})>"


class Transaction(Base):
    """Транзакция (пополнение или расход)"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    family_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('families.id'), nullable=False, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)  # Кто добавил
    user_name: Mapped[str] = mapped_column(String(255), nullable=True)  # Имя того кто добавил
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType, name="transaction_type"),
        nullable=False
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.transaction_type}, amount={self.amount}, user={self.user_name})>"





