import os
import json
import logging

from models import Order, Client, Base

from dotenv import load_dotenv
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

load_dotenv()

db_uri = os.getenv('SQLALCHEMY_DATABASE_URI')
engine = create_engine(db_uri)
Session = sessionmaker(bind=engine)

# Check if the database exists
# inspector = inspect(engine)
# if not inspector.has_table('order'):
#     Base.metadata.create_all(engine)

if not os.path.exists(db_uri):
    Base.metadata.create_all(engine)
    logger.info('db initiallized...')

session = Session()

def create_client_entry(userid, name, primary_phone, description, timeline, budget):
    client = Client(name, primary_phone)
    session.add(client)
    session.commit()
    logger.info('client %s registered', client.name)
    return client

def create_project_order(userid, username, name, primary_phone, description, timeline, budget):
    order = Order(userid, username, name, primary_phone, description, timeline, budget)
    session.add(order)
    session.commit()
    logger.info('order %s registered', order.id)
    return order.id

def fetch_orders():
    order = session.query(Order).all()

    # Convert the query result to a list of dictionaries
    serialized_order = [item.__dict__ for item in order]

    # Remove the internal keys from the dictionaries
    for item in serialized_order:
        item.pop('_sa_instance_state', None)

    # Serialize to JSON
    order_json = json.dumps(serialized_order)

    return order_json

def delete_order(order_id):
    order = session.query(Order).filter(Order.id == order_id).first()
    if order:
        session.delete(order)
        session.commit()
        logger.info('order %s deleted', order_id)
        return {"user": order.userid, "order": order.id}
    else:
        logger.warning('order %s failed to delete', order_id)
        return False
