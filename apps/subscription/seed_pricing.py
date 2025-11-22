"""
Seed data for pricing section
Run: python manage.py shell < apps/subscription/seed_pricing.py
"""
from apps.subscription.models import Package, PackageFeature, PricingSection

def seed_pricing():
    # Create or update pricing section
    pricing_section, created = PricingSection.objects.get_or_create(
        defaults={
            'title': 'Choose Your Plan',
            'subtitle': 'Select the perfect plan for your goal-setting journey',
            'background_color': '#1a1a1a',
            'text_color': '#ffffff',
            'popular_badge_text': 'Most Popular',
            'popular_badge_color': '#d4ff00',
            'free_plan_button_text': 'Get Started Free',
            'paid_plan_button_text': 'Get Started',
            'is_active': True
        }
    )
    
    # Starter Package (Free)
    starter, created = Package.objects.get_or_create(
        name='Starter',
        defaults={
            'tagline': 'Perfect for trying out GoalAI',
            'price': 0.00,
            'discount_price': 0.00,
            'interval': 'month',
            'description': 'Get started with basic goal tracking',
            'is_popular': False,
            'display_order': 1,
            'border_color': '#4a4a4a',
            'button_color': '#ffffff',
            'button_text_color': '#000000',
            'is_active': True
        }
    )
    
    # Starter features
    starter_features = [
        '1 Active Goal',
        'Basic AI Coaching',
        'Simple Progress Tracking',
        'Weekly Check-ins'
    ]
    
    for idx, feature_text in enumerate(starter_features):
        PackageFeature.objects.get_or_create(
            package=starter,
            feature_text=feature_text,
            defaults={'is_included': True, 'order': idx}
        )
    
    # Pro Package
    pro, created = Package.objects.get_or_create(
        name='Pro',
        defaults={
            'tagline': 'For serious goal achievers',
            'price': 19.00,
            'discount_price': 19.00,
            'interval': 'month',
            'description': 'Unlock advanced features and unlimited goals',
            'is_popular': True,
            'display_order': 2,
            'border_color': '#d4ff00',
            'button_color': '#d4ff00',
            'button_text_color': '#000000',
            'is_active': True
        }
    )
    
    # Pro features
    pro_features = [
        '5 Active Goals',
        'Advanced AI Coaching',
        'Custom Visual Trackers',
        'Daily Motivational Messages',
        'Progress Analytics',
        'Export & Share Features'
    ]
    
    for idx, feature_text in enumerate(pro_features):
        PackageFeature.objects.get_or_create(
            package=pro,
            feature_text=feature_text,
            defaults={'is_included': True, 'order': idx}
        )
    
    # Enterprise Package
    enterprise, created = Package.objects.get_or_create(
        name='Enterprise',
        defaults={
            'tagline': 'For teams and organizations',
            'price': 49.00,
            'discount_price': 49.00,
            'interval': 'month',
            'description': 'Complete solution for team goal management',
            'is_popular': False,
            'display_order': 3,
            'border_color': '#4a4a4a',
            'button_color': '#ffffff',
            'button_text_color': '#000000',
            'is_active': True
        }
    )
    
    # Enterprise features
    enterprise_features = [
        'Unlimited Goals',
        'Premium AI Coaching',
        'Team Collaboration',
        'Advanced Analytics',
        'Priority Support',
        'Custom Integrations'
    ]
    
    for idx, feature_text in enumerate(enterprise_features):
        PackageFeature.objects.get_or_create(
            package=enterprise,
            feature_text=feature_text,
            defaults={'is_included': True, 'order': idx}
        )
    
    print("✅ Pricing section seeded successfully!")
    print(f"📦 Created/Updated {Package.objects.count()} packages")
    print(f"✨ Created/Updated {PackageFeature.objects.count()} features")

# Run the seeding
seed_pricing()
