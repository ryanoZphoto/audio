"""Test the complete subscription lifecycle."""
import pytest
from datetime import datetime, timedelta
from app.models import Customer, Subscription
from app.services.search_manager import SearchManager
from app.tasks.subscription_monitor import (
    cleanup_expired_subscriptions,
    notify_expiring_subscriptions
)


def test_complete_subscription_lifecycle(db):
    """Test a complete subscription lifecycle from creation to expiration."""
    # 1. Create a customer
    customer = Customer(
        email='lifecycle@example.com',
        name='Lifecycle Test User'
    )
    db.session.add(customer)
    db.session.commit()
    
    # 2. Initialize SearchManager
    search_mgr = SearchManager()
    
    # 3. Create a day pass subscription
    token = search_mgr.create_subscription_token('day')
    subscription = Subscription(
        customer=customer,
        plan_type='day',
        status='active',
        search_limit=50,
        start_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=1),
        access_token=token,
        is_recurring=False
    )
    db.session.add(subscription)
    db.session.commit()
    
    # 4. Verify initial subscription state
    status = search_mgr.check_subscription(token)
    assert status['valid'] is True
    assert status['remaining'] == 50
    assert status['used'] == 0
    
    # 5. Use some searches
    for _ in range(5):
        assert search_mgr.increment_subscription_usage(token) is True
    
    # 6. Check updated usage
    status = search_mgr.check_subscription(token)
    assert status['remaining'] == 45
    assert status['used'] == 5
    
    # 7. Move time forward to near expiration
    subscription.expiry_date = datetime.utcnow() + timedelta(hours=1)
    db.session.commit()
    
    # 8. Check expiration notification
    with pytest.mock.patch(
        'app.services.email_service.send_email'
    ) as mock_send:
        notify_expiring_subscriptions()
        mock_send.assert_called_once()
        
        # Verify notification details
        call_args = mock_send.call_args[1]
        assert call_args['to_email'] == 'lifecycle@example.com'
        assert 'expiring soon' in call_args['subject']
    
    # 9. Move time past expiration
    subscription.expiry_date = datetime.utcnow() - timedelta(hours=1)
    db.session.commit()
    
    # 10. Run cleanup
    cleanup_expired_subscriptions()
    
    # 11. Verify subscription is expired
    db.session.refresh(subscription)
    assert subscription.status == 'expired'
    
    # 12. Verify token is no longer valid
    status = search_mgr.check_subscription(token)
    assert status['valid'] is False
    
    # 13. Verify searches are no longer allowed
    assert search_mgr.increment_subscription_usage(token) is False


def test_subscription_renewal_flow(db):
    """Test the renewal process for a subscription."""
    # 1. Create a customer with a recurring subscription
    customer = Customer(
        email='renewal@example.com',
        name='Renewal Test User'
    )
    db.session.add(customer)
    
    search_mgr = SearchManager()
    token = search_mgr.create_subscription_token('month')
    
    subscription = Subscription(
        customer=customer,
        plan_type='month',
        status='active',
        search_limit=500,
        start_date=datetime.utcnow(),
        expiry_date=datetime.utcnow() + timedelta(days=30),
        access_token=token,
        is_recurring=True
    )
    db.session.add(subscription)
    db.session.commit()
    
    # 2. Use some searches
    for _ in range(10):
        assert search_mgr.increment_subscription_usage(token) is True
    
    # 3. Verify usage is tracked
    status = search_mgr.check_subscription(token)
    assert status['remaining'] == 490
    assert status['used'] == 10
    
    # 4. Move to expiration
    subscription.expiry_date = datetime.utcnow() - timedelta(hours=1)
    db.session.commit()
    
    # 5. Run cleanup (should trigger renewal attempt)
    with pytest.mock.patch(
        'app.services.email_service.send_email'
    ) as mock_send:
        cleanup_expired_subscriptions()
        mock_send.assert_called_once()
        
        # Should be notified of renewal attempt
        call_args = mock_send.call_args[1]
        assert call_args['to_email'] == 'renewal@example.com'
    
    # 6. Verify subscription status
    db.session.refresh(subscription)
    assert subscription.status == 'expired'  # Should be expired until renewed 