"""Test configuration and fixtures."""
import os
import sys
import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import scoped_session, sessionmaker

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app import create_app
from app.extensions import db as _db
from app.models import Customer, Subscription


@pytest.fixture(scope='session')
def app():
    """Create a Flask app context for tests."""
    app = create_app('testing')
    return app


@pytest.fixture(scope='session')
def db(app):
    """Create a database for tests."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(autouse=True)
def session(db):
    """Create a new database session for each test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    # Create a session factory
    session_factory = sessionmaker(bind=connection)
    session = scoped_session(session_factory)

    # Replace the default session with our test session
    db.session = session

    yield session

    # Rollback transaction and close connection
    transaction.rollback()
    connection.close()
    session.remove()


@pytest.fixture
def customer(session):
    """Create a test customer."""
    # Use a unique email for each test
    test_id = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
    customer = Customer(
        email=f'test_{test_id}@example.com',
        stripe_customer_id=f'cus_test_{test_id}'
    )
    session.add(customer)
    session.commit()
    return customer


@pytest.fixture
def subscription(session, customer):
    """Create a test subscription."""
    subscription = Subscription(
        customer_id=customer.id,
        stripe_subscription_id='sub_test123',
        status='active',
        search_limit=100,
        expiry_date=datetime.utcnow() + timedelta(days=30)
    )
    session.add(subscription)
    session.commit()
    return subscription 