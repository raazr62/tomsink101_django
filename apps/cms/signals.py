from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.cms.models import (
    HeroSection, SuccessStoriesSection, AICoachSection, 
    FeatureSection, FAQ, SocialMediaLink, ContactInfo, LegalDocument
)
from apps.cms.cache_utils import clear_cms_cache


@receiver([post_save, post_delete], sender=HeroSection)
@receiver([post_save, post_delete], sender=SuccessStoriesSection)
@receiver([post_save, post_delete], sender=AICoachSection)
@receiver([post_save, post_delete], sender=FeatureSection)
@receiver([post_save, post_delete], sender=FAQ)
@receiver([post_save, post_delete], sender=SocialMediaLink)
@receiver([post_save, post_delete], sender=ContactInfo)
@receiver([post_save, post_delete], sender=LegalDocument)
def clear_cms_cache_on_update(sender, **kwargs):
    clear_cms_cache()
