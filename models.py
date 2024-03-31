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
    username = Column(String(100))
    primary_phone = Column(Integer)
    secondary_phone = Column(Integer, nullable=True)
    order_details = Column(String(255))
    timeline = Column(String(20))
    budget = Column(DECIMAL(6, 2))
    order_count = Column(Integer)
    language = Column(String(10), default='English')
    subscription = Column(String(10), default='No')
    subscription_date = Column(DATE, default=datetime.now(tz=aa).date())

    def __init__(self, userid, username, name, primary_phone, order_details, lang, subscription_type):
        self.id = self.generate_id()
        self.userid = userid
        self.username = username
        self.name = name
        self.primary_phone = primary_phone
        self.order_details = order_details
        self.order_count = 1
        self.language = lang
        self.subscription = subscription_type

    @staticmethod
    def generate_id():
        # Generate a unique 6-digit numeric id without preceding zeros
        return str(uuid.uuid4().int % 90000 + 10000)

    def add_order(self):
        self.order_count += 1

    def change_lang(self, lang):
        self.language = lang

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
