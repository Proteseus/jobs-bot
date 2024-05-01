import enum
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Enum, False_, Integer, String, DECIMAL, DATE, DATETIME, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
aa = timezone(timedelta(hours=3))

class Order(Base):
    __tablename__ = 'order'

    id = Column(String, primary_key=True)
    userid = Column(String(100))
    name = Column(String(100))
    primary_phone = Column(Integer)
    description = Column(String(255))
    timeline = Column(String(20))
    budget = Column(DECIMAL(6, 2))
    order_count = Column(Integer)
    subscription = Column(String(10), default='No')
    subscription_date = Column(DATE, default=datetime.now(tz=aa).date())

    def __init__(self, userid, name, primary_phone, description, timeline, budget, subscription_type):
        self.id = self.generate_id()
        self.userid = userid
        self.name = name
        self.primary_phone = primary_phone
        self.description = description
        self.timeline = timeline
        self.budget = budget
        self.order_count = 1
        self.subscription = subscription_type

    @staticmethod
    def generate_id():
        # Generate a unique 6-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 900000 + 100000)

    def add_order(self):
        self.order_count += 1

class StatusEnum(enum.Enum):
    active = 'active'
    inactive = 'inactive'

class Trackable(Base):
    __tablename__ = 'trackable'
    id = Column(Integer, primary_key=True)
    order_id = Column(String, ForeignKey('order.id'))
    date = Column(DATETIME, default=datetime.now(tz=aa))
    status = Column(Enum(StatusEnum), nullable=False)

    def __init__(self, order_id):
        self.id = self.generate_id()
        self.order_id = order_id

    def set_status(self, value):
        if not isinstance(value, StatusEnum):
            raise ValueError("Invalid status value")
        self.status = value

    @staticmethod
    def generate_id():
        # Generate a unique 6-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 900000 + 100000)

class Client(Base):
    __tablename__='client'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone_number = Column(Integer, nullable=False)

    @staticmethod
    def generate_id():
        # Generate a unique 6-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 900000 + 100000)


