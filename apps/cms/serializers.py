from rest_framework import serializers
from apps.cms.models import (
    Page, HeroSection, FitnessGoal, SuccessStoriesSection,
    Testimonial, AICoachSection, FeatureSection, CTASection,
    FooterLink, SocialMediaLink, FAQ
)


class FitnessGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = FitnessGoal
        fields = ['id', 'goal_text', 'icon', 'order', 'is_active']


class HeroSectionSerializer(serializers.ModelSerializer):
    goals = FitnessGoalSerializer(many=True, read_only=True)
    
    class Meta:
        model = HeroSection
        fields = [
            'id', 'heading', 'description', 
            'background_image'
        ]


class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = [
            'id', 'user_name', 'user_avatar', 'rating', 
            'testimonial_text', 'date', 'order', 'is_active'
        ]


class SuccessStoriesSectionSerializer(serializers.ModelSerializer):
    testimonials = TestimonialSerializer(many=True, read_only=True)
    
    class Meta:
        model = SuccessStoriesSection
        fields = [
            'id', 'heading', 'sub_heading', 'background_color', 
            'status', 'testimonials'
        ]


class AICoachSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AICoachSection
        fields = [
            'id', 'badge_text', 'heading', 'description', 'preview_image',
            'background_color', 'order', 'status'
        ]


class FeatureSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeatureSection
        fields = [
            'id', 'heading', 'description', 'button_text', 'button_link'
        ]


class CTASectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CTASection
        fields = [
            'id', 'heading', 'description', 'button_text', 
            'button_link', 'background_color', 'button_color', 'status'
        ]


class FooterLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = FooterLink
        fields = [
            'id', 'category', 'title', 'url', 'icon', 
            'order', 'is_active', 'open_in_new_tab'
        ]


class SocialMediaLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMediaLink
        fields = ['id', 'platform', 'url', 'order']


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = [
            'id', 'question', 'answer', 'category', 
            'order', 'status'
        ]


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ['id', 'title', 'slug', 'content', 'type', 'status']


class CompleteCMSSerializer(serializers.Serializer):
    """
    Complete CMS data in one response
    """
    hero_sections = HeroSectionSerializer(many=True)
    success_stories = SuccessStoriesSectionSerializer(many=True)
    ai_coach_sections = AICoachSectionSerializer(many=True)
    feature_sections = FeatureSectionSerializer(many=True)
    cta_sections = CTASectionSerializer(many=True)
    footer_links = FooterLinkSerializer(many=True)
    social_media_links = SocialMediaLinkSerializer(many=True)
    faqs = FAQSerializer(many=True)
    pages = PageSerializer(many=True)
