from apps.cms.models import (
    Page, FAQ, HeroSection, FitnessGoal, SuccessStoriesSection,
    Testimonial, AICoachSection, FeatureSection, CTASection,
    FooterLink, SocialMediaLink, WebsiteContentManager
)
from datetime import date


def seed_page():
    pages = [
        {
            "title": "Privacy Policy",
            "slug": "privacy-policy",
            "content": "This Privacy Policy explains how we collect, use, and protect your personal data when you use our website and services.",
            "type": "privacy_policy",
            "status": True
        },
        {
            "title": "Terms and Conditions",
            "slug": "terms-and-conditions",
            "content": "These Terms and Conditions govern your use of our website and services. By accessing the site, you agree to comply with these rules.",
            "type": "terms_and_conditions",
            "status": True
        },
        {
            "title": "Cookie Policy",
            "slug": "cookie-policy",
            "content": "Our website uses cookies to enhance user experience. This policy explains what cookies we use and how you can manage them.",
            "type": "cookie_policy",
            "status": True
        },
        {
            "title": "Imprint",
            "slug": "imprint",
            "content": "This Imprint provides legal information about our company, including address, contact details, and responsible representatives.",
            "type": "imprint",
            "status": True
        }
    ]
    
    for page in pages:
        Page.objects.get_or_create(slug=page['slug'], defaults=page)
    
    print("✅ Pages seeded successfully.")


def seed_hero_section():
    """Seed hero section with fitness goals"""
    hero, created = HeroSection.objects.get_or_create(
        heading="What fitness goal do you need to achieve?",
        defaults={
            "sub_heading": "",
            "description": "Get personalized guidance and join thousands who've transformed their lives with 3rd+ months of all.",
            "status": True,
            "order": 1
        }
    )
    
    if created:
        # Fitness goals from the image
        goals = [
            "I want to lose fat and build muscle.",
            "I'm hesitant about starting at a body shop at a bad level of fitness, and.",
            "I want to run or lift at all types of a time, even organized life.",
            "I want to Get in Shape.",
            "I have a complete starting up. How can I use my plan.",
        ]
        
        for idx, goal_text in enumerate(goals, 1):
            FitnessGoal.objects.create(
                hero_section=hero,
                goal_text=goal_text,
                order=idx,
                is_active=True
            )
    
    print("✅ Hero section seeded successfully.")


def seed_success_stories():
    """Seed success stories section with testimonials"""
    section, created = SuccessStoriesSection.objects.get_or_create(
        heading="Success Stories",
        defaults={
            "sub_heading": "Join thousands of others who have made their goals with 3rd+ months of personalized guidance, improved well-being!",
            "background_color": "#000000",
            "status": True
        }
    )
    
    if created:
        testimonials = [
            {
                "user_name": "Alice Mueller",
                "rating": 4.5,
                "testimonial_text": "I wasn't sure where to start, but the AI coach guided me step by step. I gained confidence and lost 15 pounds in 3 months. It feels like having a personal trainer in my pocket!",
                "order": 1
            },
            {
                "user_name": "Ayan Kohler",
                "rating": 5.0,
                "testimonial_text": "The AI Personal Coach understood exactly what I needed. It wasn't just about workouts—it helped me stay consistent, motivated, and on track with my nutrition too. Highly recommend!",
                "order": 2
            },
            {
                "user_name": "Leslie Alexander",
                "rating": 5.0,
                "testimonial_text": "I lost 20 pounds in 12 weeks and felt stronger than I've ever been. The guidance was personalized and easy to follow!",
                "order": 3
            },
            {
                "user_name": "Nikki Reed",
                "rating": 4.9,
                "testimonial_text": "Best fitness journey ever! I gained muscle and lost fat at the same time. The program was designed specifically for my body type.",
                "order": 4
            },
            {
                "user_name": "Leslie Alexander",
                "rating": 5.0,
                "testimonial_text": "This AI coach is incredible! It adapted to my schedule and pushed me just enough. I'm stronger, healthier, and more confident.",
                "order": 5
            },
            {
                "user_name": "Leslie Alexander",
                "rating": 4.8,
                "testimonial_text": "I've tried many fitness programs, but this one stands out. The personalized approach made all the difference in achieving my goals.",
                "order": 6
            }
        ]
        
        for testimonial_data in testimonials:
            Testimonial.objects.create(
                section=section,
                **testimonial_data,
                is_active=True
            )
    
    print("✅ Success stories seeded successfully.")


def seed_ai_coach_sections():
    """Seed AI Personal Coach sections"""
    coach_sections = [
        {
            "badge_text": "NEW FEATURE",
            "heading": "AI Personal Coach",
            "description": "Get personalized guidance, motivation, and strategies tailored to your specific goals and challenges.",
            "button_text": "Learn how it works",
            "button_link": "/ai-coach",
            "background_color": "#000000",
            "order": 1
        },
        {
            "badge_text": "NEW FEATURE",
            "heading": "AI Personal Coach",
            "description": "Get personalized guidance, motivation, and strategies tailored to your specific goals and challenges.",
            "button_text": "Learn how it works",
            "button_link": "/ai-coach",
            "background_color": "#000000",
            "order": 2
        },
        {
            "badge_text": "NEW FEATURE",
            "heading": "AI Personal Coach",
            "description": "Get personalized guidance, motivation, and strategies tailored to your specific goals and challenges.",
            "button_text": "Learn how it works",
            "button_link": "/ai-coach",
            "background_color": "#000000",
            "order": 3
        },
        {
            "badge_text": "NEW FEATURE",
            "heading": "AI Personal Coach",
            "description": "Get personalized guidance, motivation, and strategies tailored to your specific goals and challenges.",
            "button_text": "Learn how it works",
            "button_link": "/ai-coach",
            "background_color": "#000000",
            "order": 4
        }
    ]
    
    for section_data in coach_sections:
        AICoachSection.objects.get_or_create(
            order=section_data['order'],
            defaults=section_data
        )
    
    print("✅ AI Coach sections seeded successfully.")


def seed_cta_section():
    """Seed Call to Action section"""
    CTASection.objects.get_or_create(
        heading="Create AI-powered solutions people genuinely want to use",
        defaults={
            "description": "We commit to growth by enhancing our products and services to ensure long-term success of ours users.",
            "button_text": "Start Free Trial",
            "button_link": "/signup",
            "background_color": "#000000",
            "button_color": "#CCFF00",
            "status": True
        }
    )
    
    print("✅ CTA section seeded successfully.")


def seed_footer_links():
    """Seed footer navigation links"""
    footer_links = [
        # Product links
        {"category": "product", "title": "About Shredro", "url": "/about", "order": 1},
        {"category": "product", "title": "News", "url": "/news", "order": 2},
        {"category": "product", "title": "Pricing", "url": "/pricing", "order": 3},
        {"category": "product", "title": "Features", "url": "/features", "order": 4},
        
        # Company links
        {"category": "company", "title": "About Us", "url": "/company/about", "order": 1},
        {"category": "company", "title": "Blog", "url": "/blog", "order": 2},
        {"category": "company", "title": "Progress", "url": "/progress", "order": 3},
        
        # Legal links
        {"category": "legal", "title": "Legal Center", "url": "/legal", "order": 1},
        {"category": "legal", "title": "Privacy Policy", "url": "/privacy-policy", "order": 2},
        {"category": "legal", "title": "Cookie Policy", "url": "/cookie-policy", "order": 3},
        {"category": "legal", "title": "Cookie Policy", "url": "/cookie-policy", "order": 4},
    ]
    
    for link_data in footer_links:
        FooterLink.objects.get_or_create(
            category=link_data['category'],
            title=link_data['title'],
            defaults=link_data
        )
    
    print("✅ Footer links seeded successfully.")


def seed_social_media_links():
    """Seed social media links"""
    social_links = [
        {"platform": "instagram", "url": "https://instagram.com/strenno", "icon": "fab fa-instagram", "order": 1},
        {"platform": "facebook", "url": "https://facebook.com/strenno", "icon": "fab fa-facebook", "order": 2},
        {"platform": "youtube", "url": "https://youtube.com/strenno", "icon": "fab fa-youtube", "order": 3},
        {"platform": "twitter", "url": "https://twitter.com/strenno", "icon": "fab fa-twitter", "order": 4},
        {"platform": "linkedin", "url": "https://linkedin.com/company/strenno", "icon": "fab fa-linkedin", "order": 5},
        {"platform": "tiktok", "url": "https://tiktok.com/@strenno", "icon": "fab fa-tiktok", "order": 6},
        {"platform": "discord", "url": "https://discord.gg/strenno", "icon": "fab fa-discord", "order": 7},
        {"platform": "threads", "url": "https://threads.net/@strenno", "icon": "fab fa-threads", "order": 8},
    ]
    
    for social_data in social_links:
        SocialMediaLink.objects.get_or_create(
            platform=social_data['platform'],
            defaults=social_data
        )
    
    print("✅ Social media links seeded successfully.")


def seed_faq():
    faqs = [
        {
            "question": "How can I create an account?",
            "answer": "You can create an account by clicking the 'Sign Up' button and filling out the registration form.",
            "category": "Account",
            "order": 1,
            "status": True
        },
        {
            "question": "How do I reset my password?",
            "answer": "Click on 'Forgot Password' on the login page, then follow the instructions to reset your password.",
            "category": "Account",
            "order": 2,
            "status": True
        },
        {
            "question": "Can I change my email address?",
            "answer": "Yes, you can update your email in your profile settings under 'Account Information'.",
            "category": "Account",
            "order": 3,
            "status": True
        },
        {
            "question": "How does the AI Personal Coach work?",
            "answer": "Our AI Personal Coach uses advanced algorithms to create personalized workout and nutrition plans based on your goals, fitness level, and preferences.",
            "category": "Features",
            "order": 4,
            "status": True
        },
        {
            "question": "What makes this different from other fitness apps?",
            "answer": "We provide truly personalized guidance that adapts to your progress, schedule, and unique needs. Our AI learns from your feedback and adjusts your plan accordingly.",
            "category": "Features",
            "order": 5,
            "status": True
        },
        {
            "question": "How do I contact support?",
            "answer": "You can reach our support team via the 'Contact Us' page or by emailing support@strenno.com.",
            "category": "Support",
            "order": 6,
            "status": True
        },
        {
            "question": "Is my personal information safe?",
            "answer": "Yes, we use industry-standard security measures to protect your data. Your privacy is our top priority.",
            "category": "Privacy",
            "order": 7,
            "status": True
        },
        {
            "question": "Can I cancel my subscription anytime?",
            "answer": "Yes, you can cancel your subscription at any time from your account settings. No questions asked.",
            "category": "Billing",
            "order": 8,
            "status": True
        }
    ]

    for faq in faqs:
        FAQ.objects.get_or_create(
            question=faq['question'],
            defaults=faq
        )

    print("✅ FAQs seeded successfully.")


def seed_all_cms_data():
    """Run all seed functions"""
    print("\n🌱 Starting CMS data seeding...\n")
    
    # Create the master content manager first
    WebsiteContentManager.objects.get_or_create(
        defaults={
            'site_name': 'STRENNO Fitness Platform',
            'is_active': True
        }
    )
    print("✅ Website Content Manager created successfully.")
    
    seed_page()
    seed_hero_section()
    seed_success_stories()
    seed_ai_coach_sections()
    seed_cta_section()
    seed_footer_links()
    seed_social_media_links()
    seed_faq()
    
    print("\n✅ All CMS data seeded successfully!\n")