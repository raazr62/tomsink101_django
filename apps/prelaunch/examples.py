"""
Example Usage and Testing for Pre-Launch Waitlist System

This file demonstrates how to use the pre-launch system programmatically.
You can run this file to create test data and see examples.
"""

from apps.prelaunch.models import PrelaunchUser, PrelaunchReferral
from django.db.models import Count


def create_test_users():
    """Create some test users with referrals."""
    
    print("\n=== Creating Test Users ===\n")
    
    # Create first user (no referral)
    user1 = PrelaunchUser.objects.create(
        name="Sarah Johnson",
        email="sarah@example.com",
        ip_address="192.168.1.1"
    )
    print(f"✓ Created: {user1.name}")
    print(f"  Email: {user1.email}")
    print(f"  Referral Code: {user1.referral_code}")
    print(f"  Referral Link: {user1.referral_link}\n")
    
    # Create second user (referred by user1)
    user2 = PrelaunchUser.objects.create(
        name="John Smith",
        email="john@example.com",
        referred_by=user1.referral_code,
        ip_address="192.168.1.2"
    )
    
    # Create referral record
    PrelaunchReferral.objects.create(
        parent_referral_code=user1.referral_code,
        child_email=user2.email,
        child_user=user2,
        parent_user=user1
    )
    
    print(f"✓ Created: {user2.name}")
    print(f"  Email: {user2.email}")
    print(f"  Referral Code: {user2.referral_code}")
    print(f"  Referred By: {user2.referred_by}\n")
    
    # Create third user (referred by user1)
    user3 = PrelaunchUser.objects.create(
        name="Emily Davis",
        email="emily@example.com",
        referred_by=user1.referral_code,
        ip_address="192.168.1.3"
    )
    
    PrelaunchReferral.objects.create(
        parent_referral_code=user1.referral_code,
        child_email=user3.email,
        child_user=user3,
        parent_user=user1
    )
    
    print(f"✓ Created: {user3.name}")
    print(f"  Email: {user3.email}")
    print(f"  Referred By: {user3.referred_by}\n")
    
    # Create fourth user (referred by user2)
    user4 = PrelaunchUser.objects.create(
        name="Michael Brown",
        email="michael@example.com",
        referred_by=user2.referral_code,
        ip_address="192.168.1.4"
    )
    
    PrelaunchReferral.objects.create(
        parent_referral_code=user2.referral_code,
        child_email=user4.email,
        child_user=user4,
        parent_user=user2
    )
    
    print(f"✓ Created: {user4.name}")
    print(f"  Email: {user4.email}")
    print(f"  Referred By: {user4.referred_by}\n")
    
    return user1, user2, user3, user4


def display_statistics():
    """Display overall statistics."""
    
    print("\n=== Pre-Launch Statistics ===\n")
    
    total_users = PrelaunchUser.objects.count()
    total_referrals = PrelaunchReferral.objects.count()
    activated_users = PrelaunchUser.objects.filter(activated=True).count()
    
    print(f"Total Sign-ups: {total_users}")
    print(f"Total Referrals: {total_referrals}")
    print(f"Activated Users: {activated_users}")
    print()


def display_leaderboard():
    """Display referral leaderboard."""
    
    print("\n=== Referral Leaderboard ===\n")
    
    leaderboard = PrelaunchUser.objects.annotate(
        ref_count=Count('referrals_made')
    ).filter(
        ref_count__gt=0
    ).order_by('-ref_count')[:10]
    
    for rank, user in enumerate(leaderboard, start=1):
        print(f"{rank}. {user.name} - {user.ref_count} referrals")
        print(f"   Email: {user.email}")
        print(f"   Code: {user.referral_code}\n")


def display_user_referrals(referral_code):
    """Display all users referred by a specific user."""
    
    try:
        user = PrelaunchUser.objects.get(referral_code=referral_code)
        referrals = user.get_referrals()
        
        print(f"\n=== Referrals by {user.name} ===\n")
        print(f"Total Referrals: {user.referral_count}\n")
        
        for referred_user in referrals:
            print(f"• {referred_user.name}")
            print(f"  Email: {referred_user.email}")
            print(f"  Joined: {referred_user.created_at.strftime('%Y-%m-%d %H:%M')}\n")
            
    except PrelaunchUser.DoesNotExist:
        print(f"User with referral code '{referral_code}' not found.")


def check_fraud_by_ip(ip_address):
    """Check for potential fraud from same IP."""
    
    users = PrelaunchUser.objects.filter(ip_address=ip_address)
    
    print(f"\n=== Fraud Check: IP {ip_address} ===\n")
    
    if users.count() > 1:
        print(f"⚠️ WARNING: {users.count()} accounts from same IP\n")
        for user in users:
            print(f"• {user.name} ({user.email})")
            print(f"  Signed up: {user.created_at.strftime('%Y-%m-%d %H:%M')}\n")
    else:
        print("✓ No suspicious activity detected")


def example_queries():
    """Demonstrate useful queries."""
    
    print("\n=== Example Queries ===\n")
    
    # Query 1: Get total signups
    total = PrelaunchUser.objects.count()
    print(f"1. Total Signups: {total}\n")
    
    # Query 2: Get user by email
    try:
        user = PrelaunchUser.objects.get(email="sarah@example.com")
        print(f"2. User by Email:")
        print(f"   Name: {user.name}")
        print(f"   Referral Code: {user.referral_code}\n")
    except PrelaunchUser.DoesNotExist:
        print("2. User not found\n")
    
    # Query 3: Count referrals for a user
    try:
        user = PrelaunchUser.objects.get(email="sarah@example.com")
        count = user.referral_count
        print(f"3. Referral Count for {user.name}: {count}\n")
    except PrelaunchUser.DoesNotExist:
        pass
    
    # Query 4: Get top 3 referrers
    top_referrers = PrelaunchUser.objects.annotate(
        ref_count=Count('referrals_made')
    ).order_by('-ref_count')[:3]
    
    print("4. Top 3 Referrers:")
    for user in top_referrers:
        print(f"   • {user.name}: {user.ref_count} referrals")
    print()
    
    # Query 5: Recent signups (last 5)
    recent = PrelaunchUser.objects.order_by('-created_at')[:5]
    print("5. Recent Signups:")
    for user in recent:
        print(f"   • {user.name} - {user.created_at.strftime('%Y-%m-%d %H:%M')}")
    print()


def run_examples():
    """Run all examples."""
    
    print("\n" + "="*60)
    print("PRE-LAUNCH WAITLIST SYSTEM - EXAMPLES")
    print("="*60)
    
    # Check if test data already exists
    if PrelaunchUser.objects.filter(email="sarah@example.com").exists():
        print("\n⚠️  Test data already exists. Skipping creation.\n")
        user1 = PrelaunchUser.objects.get(email="sarah@example.com")
    else:
        # Create test data
        user1, user2, user3, user4 = create_test_users()
    
    # Display statistics
    display_statistics()
    
    # Display leaderboard
    display_leaderboard()
    
    # Display specific user's referrals
    if PrelaunchUser.objects.filter(email="sarah@example.com").exists():
        user1 = PrelaunchUser.objects.get(email="sarah@example.com")
        display_user_referrals(user1.referral_code)
    
    # Check for fraud
    check_fraud_by_ip("192.168.1.1")
    
    # Example queries
    example_queries()
    
    print("\n" + "="*60)
    print("EXAMPLES COMPLETED")
    print("="*60 + "\n")


# Run this in Django shell:
# python manage.py shell
# >>> from apps.prelaunch.examples import run_examples
# >>> run_examples()

if __name__ == "__main__":
    print("Run this script in Django shell:")
    print("python manage.py shell")
    print(">>> from apps.prelaunch.examples import run_examples")
    print(">>> run_examples()")
