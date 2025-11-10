from apps.users.models import User, Profile


def seed_users():
    user_data = [
        {
            "email": "imdadhossain376@gmail.com",
            "password": "12345678",
            "is_staff": True,
            "is_superuser": True,
            "profile": {
                "name": "Super",
                "accepted_terms": True,
                "avatar": "avatars/1.jpg",
                "dob": "1990-01-01",
            },
        },
        {
            "email": "admin@admin.com",
            "password": "12345678",
            "is_staff": True,
            "is_superuser": True,
            "profile": {
                "name": "Admin",
                "accepted_terms": True,
                "avatar": "avatars/1.jpg",
                "dob": "1990-01-01",
            },
        },

        {
            "email": "user1@user1.com",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "profile": {
                "name": "User",
                "accepted_terms": True,
                "avatar": "avatars/2.jpg",
                "dob": "1990-01-01",
            },
        },
        {
            "email": "user2@user2.com",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "profile": {
                "name": "User2",
                "accepted_terms": True,
                "avatar": "avatars/3.jpg",
                "dob": "1990-01-01",
            },
        },
        {
            "email": "user3@user3.com",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "profile": {
                "name": "User3",
                "accepted_terms": True,
                "avatar": "avatars/4.jpg",
                "dob": "1990-01-01",
            },
        },
        {
            "email": "user4@user4.com",
            "password": "12345678",
            "is_staff": False,
            "is_superuser": False,
            "profile": {
                "name": "User4",
                "accepted_terms": True,
                "avatar": "avatars/5.jpg",
                "dob": "1990-01-01",
            },
        }

    ]

    for user in user_data:
        # Use get_or_create to avoid duplicate users
        user_instance, created = User.objects.get_or_create(
            email=user["email"],
            defaults={
                'is_staff': user["is_staff"],
                'is_superuser': user["is_superuser"],
            }
        )
        
        # Set password if user was just created
        if created:
            user_instance.set_password(user["password"])
            user_instance.save()

        # Get or create profile
        Profile.objects.get_or_create(
            user=user_instance,
            defaults={
                'name': user["profile"]["name"],
                'accepted_terms': user["profile"]["accepted_terms"],
                'avatar': user["profile"]["avatar"],
                'dob': user["profile"]["dob"],
            }
        )

    print("✅ User data seeded successfully.")