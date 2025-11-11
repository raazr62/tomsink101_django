from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.cms.models import (
    HeroSection, SuccessStoriesSection, AICoachSection, 
    FeatureSection, CTASection, FooterLink, SocialMediaLink, FAQ, Page
)
from apps.cms.serializers import (
    HeroSectionSerializer, SuccessStoriesSectionSerializer,
    AICoachSectionSerializer, FeatureSectionSerializer,
    CTASectionSerializer, FooterLinkSerializer,
    SocialMediaLinkSerializer, FAQSerializer, PageSerializer
)


class CompleteCMSDataView(APIView):
    """
    GET: Returns all CMS data in one response
    
    Returns:
    {
        "hero_sections": [...],
        "success_stories": [...],
        "ai_coach_sections": [...],
        "feature_sections": [...],
        "cta_sections": [...],
        "footer_links": {
            "product": [...],
            "company": [...],
            "legal": [...],
            "social": [...],
            "other": [...]
        },
        "social_media_links": [...],
        "faqs": [...],
        "pages": {...}
    }
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        try:
            # Get all active hero sections with their goals
            hero_sections = HeroSection.objects.filter(status=True).prefetch_related('goals').order_by('order')
            
            # Get success stories with testimonials
            success_stories = SuccessStoriesSection.objects.filter(status=True).prefetch_related('testimonials').first()
            
            # Get AI coach sections
            ai_coach_sections = AICoachSection.objects.filter(status=True).order_by('order')
            
            # Get feature sections
            feature_sections = FeatureSection.objects.filter(status=True).order_by('order')
            
            # Get CTA sections
            cta_sections = CTASection.objects.filter(status=True).first()
            
            # Get footer links organized by category
            footer_links_all = FooterLink.objects.filter(is_active=True).order_by('category', 'order')
            footer_links_grouped = {
                'product': footer_links_all.filter(category='product'),
                'company': footer_links_all.filter(category='company'),
                'legal': footer_links_all.filter(category='legal'),
                'social': footer_links_all.filter(category='social'),
                'other': footer_links_all.filter(category='other'),
            }
            
            # Get social media links
            social_media_links = SocialMediaLink.objects.filter(is_active=True).order_by('order')
            
            # Get FAQs
            faqs = FAQ.objects.filter(status=True).order_by('order')
            
            # Get pages organized by type
            pages_all = Page.objects.filter(status=True)
            pages_grouped = {
                'privacy_policy': pages_all.filter(type='privacy_policy').first(),
                'terms_and_conditions': pages_all.filter(type='terms_and_conditions').first(),
                'cookie_policy': pages_all.filter(type='cookie_policy').first(),
                'imprint': pages_all.filter(type='imprint').first(),
            }
            
            # Serialize data
            data = {
                'hero_sections': HeroSectionSerializer(hero_sections, many=True, context={'request': request}).data,
                'success_stories': SuccessStoriesSectionSerializer(success_stories, context={'request': request}).data if success_stories else None,
                'ai_coach_sections': AICoachSectionSerializer(ai_coach_sections, many=True, context={'request': request}).data,
                'feature_sections': FeatureSectionSerializer(feature_sections, many=True, context={'request': request}).data,
                'cta_section': CTASectionSerializer(cta_sections, context={'request': request}).data if cta_sections else None,
                'footer_links': {
                    'product': FooterLinkSerializer(footer_links_grouped['product'], many=True).data,
                    'company': FooterLinkSerializer(footer_links_grouped['company'], many=True).data,
                    'legal': FooterLinkSerializer(footer_links_grouped['legal'], many=True).data,
                    'social': FooterLinkSerializer(footer_links_grouped['social'], many=True).data,
                    'other': FooterLinkSerializer(footer_links_grouped['other'], many=True).data,
                },
                'social_media_links': SocialMediaLinkSerializer(social_media_links, many=True).data,
                'faqs': FAQSerializer(faqs, many=True).data,
                'pages': {
                    'privacy_policy': PageSerializer(pages_grouped['privacy_policy']).data if pages_grouped['privacy_policy'] else None,
                    'terms_and_conditions': PageSerializer(pages_grouped['terms_and_conditions']).data if pages_grouped['terms_and_conditions'] else None,
                    'cookie_policy': PageSerializer(pages_grouped['cookie_policy']).data if pages_grouped['cookie_policy'] else None,
                    'imprint': PageSerializer(pages_grouped['imprint']).data if pages_grouped['imprint'] else None,
                }
            }
            
            return Response({
                'status': status.HTTP_200_OK,
                'success': True,
                'message': 'CMS data retrieved successfully',
                'data': data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'status': status.HTTP_400_BAD_REQUEST,
                'success': False,
                'message': f'Error retrieving CMS data: {str(e)}',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

