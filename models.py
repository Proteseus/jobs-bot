import enum
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import Column, Enum, BigInteger, Integer, String, TIMESTAMP, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
aa = timezone(timedelta(hours=3))

class Order(Base):
    __tablename__ = 'order'

    id = Column(String, primary_key=True)
    userid = Column(String(100))
    username = Column(String(100))
    name = Column(String(100))
    primary_phone = Column(BigInteger)
    description = Column(String(255))
    timeline = Column(String(20))
    budget = Column(String(20))

    def __init__(self, userid, username, name, primary_phone, description, timeline, budget):
        self.id = self.generate_id()
        self.userid = userid
        self.username = username
        self.name = name
        self.primary_phone = primary_phone
        self.description = description
        self.timeline = timeline
        self.budget = budget

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
    date = Column(TIMESTAMP, default=datetime.now(tz=aa))
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
    
    def __init__(self, name, phone_number):
        self.id = self.generate_id()
        self.name = name
        self.phone_number = phone_number

    @staticmethod
    def generate_id():
        # Generate a unique 6-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 900000 + 100000)
