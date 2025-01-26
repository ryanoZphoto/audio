"""Tests for subscription monitoring system."""
import pytest
from datetime import datetime, timedelta
from app.models import Subscription, Customer
from app.tasks.subscription_monitor import (
    cleanup_expired_subscriptions,
    notify_expiring_subscriptions,
    check_subscription_health
)


@pytest.fixture
def active_subscription(db):
    """Create an active subscription for testing."""
    customer = Customer(
        email='test@example.com',
        name='Test User'
    )
    db.session.add(customer)
    
    sub = Subscription(
        customer=customer,
        plan_type='month',
        status='active',
        search_limit=500,
        start_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=30),
        access_token='test_token_123',
        is_recurring=False
    )
    db.session.add(sub)
    db.session.commit()
    return sub


@pytest.fixture
def expired_subscription(db):
    """Create an expired subscription for testing."""
    customer = Customer(
        email='expired@example.com',
        name='Expired User'
    )
    db.session.add(customer)
    
    sub = Subscription(
        customer=customer,
        plan_type='month',
        status='active',  # Still marked as active
        search_limit=500,
        start_date=datetime.utcnow() - timedelta(days=31),
        expiry_date=datetime.utcnow() - timedelta(days=1),
        access_token='expired_token_123',
        is_recurring=False
    )
    db.session.add(sub)
    db.session.commit()
    return sub


@pytest.fixture
def recurring_subscription(db):
    """Create a recurring subscription for testing."""
    customer = Customer(
        email='recurring@example.com',
        name='Recurring User'
    )
    db.session.add(customer)
    
    sub = Subscription(
        customer=customer,
        plan_type='month',
        status='active',
        search_limit=500,
        start_date=datetime.utcnow() - timedelta(days=29),
        expiry_date=datetime.utcnow() + timedelta(days=1),
        access_token='recurring_token_123',
        is_recurring=True
    )
    db.session.add(sub)
    db.session.commit()
    return sub


def test_cleanup_expired_subscriptions(db, active_subscription):
    """Test that expired subscriptions are cleaned up."""
    # Set expiration to yesterday
    active_subscription.expiry_date = datetime.utcnow() - timedelta(days=1)
    db.session.commit()

    # Run cleanup
    cleanup_expired_subscriptions()

    # Check that subscription is marked as expired
    sub = Subscription.query.get(active_subscription.id)
    assert sub.status == 'expired'


def test_notify_expiring_subscriptions(db, active_subscription, mocker):
    """Test that notifications are sent for expiring subscriptions."""
    # Set expiration to tomorrow
    active_subscription.expiry_date = datetime.utcnow() + timedelta(hours=23)
    db.session.commit()

    # Run notification check
    mock_send = mocker.patch('app.tasks.subscription_monitor.send_email')
    notify_expiring_subscriptions()
    mock_send.assert_called_once()


def test_recurring_subscription_renewal(
    db, recurring_subscription, mocker
):
    """Test that recurring subscriptions are handled properly."""
    # Set expiration to yesterday
    recurring_subscription.expiry_date = datetime.utcnow() - timedelta(days=1)
    db.session.commit()

    # Run cleanup which should trigger renewal
    mock_send = mocker.patch('app.tasks.subscription_monitor.send_email')
    cleanup_expired_subscriptions()
    mock_send.assert_called_once()


def test_subscription_health_check(
    db, active_subscription, expired_subscription, customer
):
    """Test the subscription health monitoring."""
    # Create an invalid subscription
    invalid_sub = Subscription(
        customer_id=customer.id,  # Use existing customer
        plan_type=None,  # Invalid - missing plan type
        status='active',
        search_limit=500,
        start_date=datetime.utcnow(),
        expiry_date=None  # Invalid - missing expiry
    )
    db.session.add(invalid_sub)
    db.session.commit()

    # Run health check
    issues = check_subscription_health()
    assert len(issues) > 0
    assert any(
        'missing plan type' in issue['description']
        for issue in issues
    )
    assert any(
        'missing expiry date' in issue['description']
        for issue in issues
    )


def test_multiple_expired_subscriptions(db, active_subscription):
    """Test handling multiple expired subscriptions."""
    # Set the original subscription to expired
    active_subscription.expiry_date = datetime.utcnow() - timedelta(days=1)
    db.session.commit()

    # Create additional expired subscriptions
    for i in range(3):
        sub = Subscription(
            customer_id=active_subscription.customer_id,
            plan_type='month',
            status='active',
            search_limit=100,
            expiry_date=datetime.utcnow() - timedelta(days=i + 1)
        )
        db.session.add(sub)
    db.session.commit()

    # Run cleanup
    cleanup_expired_subscriptions()

    # Check that all expired subscriptions are marked
    expired = Subscription.query.filter_by(status='expired').count()
    assert expired == 4  # Original + 3 new ones 