from apps.review.models import Review, ReviewCategory, ReviewSettings
from apps.users.models import User
from datetime import datetime, timedelta
from django.utils import timezone


def seed_review_settings():
    """Create default review settings"""
    settings, created = ReviewSettings.objects.get_or_create(
        defaults={
            'enable_reviews': True,
            'require_approval': True,
            'allow_anonymous': True,
            'show_title': 'Share Your Feedback',
            'show_subtitle': 'Help us improve your experience',
            'placeholder_text': "Share your thoughts, suggestions, or anything else you'd like us to know...",
            'submit_button_text': 'Submit Feedback',
            'min_rating': 1,
            'max_rating': 5,
            'min_text_length': 10,
            'max_text_length': 500,
            'notify_on_new_review': True,
            'show_on_homepage': True,
            'reviews_per_page': 10
        }
    )
    
    if created:
        print("✅ Review settings created successfully.")
    else:
        print("ℹ️  Review settings already exist.")
    
    return settings


def seed_review_categories():
    """Create review categories"""
    categories = [
        {
            'name': 'General Feedback',
            'description': 'General thoughts and feedback',
            'icon': 'fas fa-comment',
            'order': 1
        },
        {
            'name': 'Feature Request',
            'description': 'Suggestions for new features',
            'icon': 'fas fa-lightbulb',
            'order': 2
        },
        {
            'name': 'Bug Report',
            'description': 'Report issues or bugs',
            'icon': 'fas fa-bug',
            'order': 3
        },
        {
            'name': 'User Experience',
            'description': 'Feedback about user experience',
            'icon': 'fas fa-user-check',
            'order': 4
        },
        {
            'name': 'Performance',
            'description': 'Feedback about app performance',
            'icon': 'fas fa-tachometer-alt',
            'order': 5
        }
    ]
    
    for cat_data in categories:
        cat, created = ReviewCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"✅ Category '{cat.name}' created.")


def seed_sample_reviews():
    """Create sample reviews"""
    
    # Get or create test users
    users = []
    user_data = [
        {'email': 'alice@example.com', 'name': 'Alice Johnson'},
        {'email': 'bob@example.com', 'name': 'Bob Smith'},
        {'email': 'carol@example.com', 'name': 'Carol Williams'},
    ]
    
    for user_info in user_data:
        user, created = User.objects.get_or_create(
            email=user_info['email'],
            defaults={
                'is_active': True
            }
        )
        if created:
            user.set_password('password123')
            user.save()
            # Create profile with name
            from apps.users.models import Profile
            Profile.objects.create(
                user=user,
                name=user_info['name']
            )
        users.append(user)
    
    # Sample reviews
    reviews_data = [
        {
            'user': users[0] if len(users) > 0 else None,
            'rating': 5,
            'feedback_text': "Absolutely love this platform! The AI coaching feature is a game-changer. It's like having a personal trainer available 24/7. The interface is intuitive and easy to navigate.",
            'is_approved': True,
            'is_featured': True
        },
        {
            'user': users[1] if len(users) > 1 else None,
            'rating': 4,
            'feedback_text': "Great app overall! The personalized workout plans are really helpful. Only minor issue is the loading time on some pages. Otherwise, highly recommend!",
            'is_approved': True,
            'is_featured': True
        },
        {
            'user': users[2] if len(users) > 2 else None,
            'rating': 5,
            'feedback_text': "This is exactly what I needed! The progress tracking features are comprehensive and motivating. I've seen real results in just 2 months. Customer support is also fantastic!",
            'is_approved': True,
            'is_featured': False
        },
        {
            'user': None,
            'user_name': 'Sarah Davis',
            'user_email': 'sarah@example.com',
            'rating': 5,
            'feedback_text': "Best fitness app I've used! The AI understands my goals and adapts the workouts accordingly. The nutrition tracking is also very detailed and helpful.",
            'is_approved': True,
            'is_featured': True
        },
        {
            'user': None,
            'user_name': 'Mike Thompson',
            'user_email': 'mike@example.com',
            'rating': 4,
            'feedback_text': "Really enjoying the experience so far. The variety of workouts keeps things interesting. Would love to see more yoga and stretching routines added in the future.",
            'is_approved': True,
            'is_featured': False
        },
        {
            'user': None,
            'user_name': 'Emma Wilson',
            'user_email': 'emma@example.com',
            'rating': 5,
            'feedback_text': "Game changer for my fitness journey! Lost 15 pounds in 3 months. The community support and AI coaching make all the difference. Highly recommend!",
            'is_approved': True,
            'is_featured': True
        },
        {
            'user': users[0] if len(users) > 0 else None,
            'rating': 3,
            'feedback_text': "Good app with solid features. The workout tracking could be more detailed. Also, it would be great to have offline mode for when I'm at the gym with poor connection.",
            'is_approved': True,
            'is_featured': False
        },
        {
            'user': None,
            'user_name': 'John Martinez',
            'user_email': 'john@example.com',
            'rating': 5,
            'feedback_text': "Exceptional platform! The personalized coaching adapts to my busy schedule perfectly. I've tried many fitness apps, but this one truly stands out with its AI capabilities.",
            'is_approved': True,
            'is_featured': True
        },
        # Pending reviews (not approved)
        {
            'user': None,
            'user_name': 'Jane Doe',
            'user_email': 'jane@example.com',
            'rating': 2,
            'feedback_text': "The app crashes sometimes when I try to log my meals. Please fix this issue. Otherwise, the concept is good.",
            'is_approved': False,
            'is_featured': False
        },
        {
            'user': users[1] if len(users) > 1 else None,
            'rating': 4,
            'feedback_text': "Really like the AI suggestions! Would be even better if there were more video demonstrations for the exercises. Overall great experience though!",
            'is_approved': False,
            'is_featured': False
        }
    ]
    
    created_count = 0
    for review_data in reviews_data:
        # Create review with staggered dates
        review_data['created_at'] = timezone.now() - timedelta(days=created_count * 3)
        
        # Check if similar review exists
        if review_data.get('user'):
            exists = Review.objects.filter(
                user=review_data['user'],
                feedback_text=review_data['feedback_text']
            ).exists()
        else:
            exists = Review.objects.filter(
                user_email=review_data.get('user_email'),
                feedback_text=review_data['feedback_text']
            ).exists()
        
        if not exists:
            Review.objects.create(**review_data)
            created_count += 1
    
    print(f"✅ {created_count} sample reviews created.")


def seed_all_review_data():
    """Run all review seed functions"""
    print("\n🌱 Starting review data seeding...\n")
    
    seed_review_settings()
    seed_review_categories()
    seed_sample_reviews()
    
    print("\n✅ All review data seeded successfully!\n")


if __name__ == '__main__':
    seed_all_review_data()
