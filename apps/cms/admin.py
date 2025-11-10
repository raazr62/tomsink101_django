from django.contrib import admin
from apps.cms.models import (
    Page, HeroSection, FitnessGoal, SuccessStoriesSection, 
    Testimonial, AICoachSection, FeatureSection, CTASection,
    FooterLink, SocialMediaLink, FAQ, WebsiteContentManager
)
from unfold.admin import ModelAdmin, TabularInline, StackedInline
from django.utils.html import format_html


# ============= Inline Classes =============

class FitnessGoalInline(TabularInline):
    model = FitnessGoal
    extra = 3
    fields = ('goal_text', 'icon', 'order', 'is_active')
    ordering = ['order']


class TestimonialInline(StackedInline):
    model = Testimonial
    extra = 2
    fields = ('user_name', 'user_avatar', 'rating', 'testimonial_text', 'order', 'is_active')
    ordering = ['order']


class AICoachSectionInline(StackedInline):
    model = AICoachSection
    extra = 1
    fields = (
        'badge_text', 'heading', 'description', 
        'button_text', 'button_link', 'preview_image',
        'background_color', 'order', 'status'
    )
    ordering = ['order']


class FeatureSectionInline(StackedInline):
    model = FeatureSection
    extra = 1
    fields = (
        'section_name', 'heading', 'sub_heading', 'description',
        'image', 'button_text', 'button_link',
        'background_color', 'order', 'status'
    )
    ordering = ['order']


class FooterLinkInline(TabularInline):
    model = FooterLink
    extra = 2
    fields = ('category', 'title', 'url', 'icon', 'order', 'is_active', 'open_in_new_tab')
    ordering = ['category', 'order']


class SocialMediaLinkInline(TabularInline):
    model = SocialMediaLink
    extra = 1
    fields = ('platform', 'url', 'icon', 'order', 'is_active')
    ordering = ['order']


class FAQInline(StackedInline):
    model = FAQ
    extra = 2
    fields = ('question', 'answer', 'category', 'order', 'status')
    ordering = ['order']


class PageInline(StackedInline):
    model = Page
    extra = 0
    fields = ('title', 'slug', 'type', 'content', 'status')
    prepopulated_fields = {'slug': ('title',)}

# ============= Main Admin - ALL IN ONE PAGE =============

@admin.register(WebsiteContentManager)
class WebsiteContentManagerAdmin(ModelAdmin):
    """
    🎯 CMS Dashboard - Quick access to all content sections
    """
    
    readonly_fields = ('last_updated', 'quick_links_display')
    
    fieldsets = (
        ('🌐 Website Overview', {
            'fields': ('site_name', 'is_active', 'last_updated'),
        }),
        ('🚀 Quick Actions', {
            'fields': ('quick_links_display',),
            'description': 'Click the links below to edit content with inline management'
        }),
    )
    
    def quick_links_display(self, obj):
        """Display clickable links to main content sections"""
        return format_html(
            '''
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h3 style="color: #28a745; margin-top: 0;">🎯 Edit Content - All-In-One Pages</h3>
                
                <div style="margin: 15px 0;">
                    <a href="/admin/cms/herosection/" style="display: inline-block; background: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        🏠 Hero Sections (+ Fitness Goals)
                    </a>
                    <a href="/admin/cms/successstoriessection/" style="display: inline-block; background: #28a745; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        ⭐ Success Stories (+ Testimonials)
                    </a>
                </div>
                
                <h3 style="color: #6c757d; margin-top: 25px;">📋 Other Content Sections</h3>
                
                <div style="margin: 15px 0;">
                    <a href="/admin/cms/aicoachsection/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        🤖 AI Coach Sections
                    </a>
                    <a href="/admin/cms/featuresection/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        ✨ Feature Sections
                    </a>
                    <a href="/admin/cms/ctasection/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        📣 CTA Sections
                    </a>
                </div>
                
                <div style="margin: 15px 0;">
                    <a href="/admin/cms/footerlink/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        🔗 Footer Links
                    </a>
                    <a href="/admin/cms/socialmedialink/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        📱 Social Media
                    </a>
                    <a href="/admin/cms/faq/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        ❓ FAQs
                    </a>
                    <a href="/admin/cms/page/" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px;">
                        📄 Pages
                    </a>
                </div>
                
                <div style="background: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin-top: 20px;">
                    <strong>💡 Pro Tip:</strong> The blue and green buttons above are your ALL-IN-ONE pages where you can edit sections AND their related content (goals/testimonials) on a single page!
                </div>
            </div>
            '''
        )
    
    quick_links_display.short_description = 'Quick Access Links'
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not WebsiteContentManager.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion
        return False


class HeroSectionInlineForMaster(StackedInline):
    model = HeroSection
    extra = 0
    max_num = 3
    fields = ('heading', 'sub_heading', 'description', 'status', 'order')
    classes = ['collapse']


@admin.register(HeroSection)
class HeroSectionAllInOneAdmin(ModelAdmin):
    """
    🎯 HERO SECTIONS - Edit with inline Fitness Goals
    """
    list_display = ('id', 'heading_preview', 'goals_count', 'status', 'order', 'created_at')
    list_display_links = ('id', 'heading_preview')
    list_filter = ('status', 'created_at')
    search_fields = ('heading', 'description')
    list_editable = ('status', 'order')
    
    # Include ALL inlines for complete management
    inlines = [
        FitnessGoalInline,
    ]
    
    fieldsets = (
        ('🏠 Hero Section Content', {
            'fields': ('heading', 'sub_heading', 'description', 'background_image'),
            'description': 'Main landing page hero section'
        }),
        ('⚙️ Settings', {
            'fields': ('status', 'order')
        }),
    )
    
    def heading_preview(self, obj):
        return obj.heading[:50] + '...' if len(obj.heading) > 50 else obj.heading
    heading_preview.short_description = 'Heading'
    
    def goals_count(self, obj):
        count = obj.goals.count()
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 3px; font-weight: bold;">{} goals</span>',
            count
        )
    goals_count.short_description = 'Fitness Goals'


@admin.register(SuccessStoriesSection)
class SuccessStoriesSectionAllInOneAdmin(ModelAdmin):
    """
    ⭐ SUCCESS STORIES - ALL IN ONE
    Manage success stories section with all testimonials in one place!
    """
    list_display = ('id', 'heading', 'status', 'testimonial_count', 'created_at')
    list_display_links = ('id', 'heading')
    list_filter = ('status', 'created_at')
    search_fields = ('heading', 'sub_heading')
    
    inlines = [TestimonialInline]
    
    fieldsets = (
        ('⭐ Success Stories Section', {
            'fields': ('heading', 'sub_heading', 'background_color'),
            'description': 'Manage all customer testimonials from this page'
        }),
        ('⚙️ Settings', {
            'fields': ('status',)
        }),
    )
    
    def testimonial_count(self, obj):
        count = obj.testimonials.count()
        return format_html(
            '<span style="background: #28a745; color: white; padding: 3px 10px; border-radius: 3px;">{} testimonials</span>',
            count
        )
    testimonial_count.short_description = 'Total Testimonials'


# ============= Individual Admin Classes (Hidden from menu but accessible) =============

@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ('id', 'title', 'type', 'status', 'slug')
    list_display_links = ('id', 'title')
    list_filter = ('type', 'status')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('📄 Page Information', {
            'fields': ('title', 'slug', 'type', 'status')
        }),
        ('📝 Content', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
    )


@admin.register(FitnessGoal)
class FitnessGoalAdmin(ModelAdmin):
    """
    🏋️ FITNESS GOALS - Editable Table View
    Edit multiple goals directly in the list!
    """
    list_display = ('id', 'goal_text_preview', 'hero_section', 'icon_preview', 'order', 'is_active')
    list_display_links = ('id', 'goal_text_preview')
    list_filter = ('is_active', 'hero_section')
    search_fields = ('goal_text',)
    list_editable = ('order', 'is_active')
    list_per_page = 50
    
    fieldsets = (
        ('Goal Details', {
            'fields': ('hero_section', 'goal_text', 'icon', 'order', 'is_active')
        }),
    )
    
    def goal_text_preview(self, obj):
        return obj.goal_text[:80] + '...' if len(obj.goal_text) > 80 else obj.goal_text
    goal_text_preview.short_description = 'Goal Text'
    
    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<img src="{}" style="max-height: 30px; max-width: 30px;" />', obj.icon.url)
        return '-'
    icon_preview.short_description = 'Icon'


@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    """
    💬 TESTIMONIALS - Editable Table View
    Edit multiple testimonials directly in the list!
    """
    list_display = ('id', 'user_name', 'rating', 'text_preview', 'section', 'date', 'order', 'is_active')
    list_display_links = ('id', 'user_name')
    list_filter = ('is_active', 'rating', 'section', 'date')
    search_fields = ('user_name', 'testimonial_text')
    date_hierarchy = 'date'
    list_editable = ('rating', 'order', 'is_active')
    list_per_page = 50
    
    fieldsets = (
        ('👤 User Information', {
            'fields': ('section', 'user_name', 'user_avatar', 'rating')
        }),
        ('💬 Testimonial', {
            'fields': ('testimonial_text',),
            'classes': ('wide',)
        }),
        ('⚙️ Settings', {
            'fields': ('order', 'is_active')
        }),
    )
    
    def text_preview(self, obj):
        return obj.testimonial_text[:100] + '...' if len(obj.testimonial_text) > 100 else obj.testimonial_text
    text_preview.short_description = 'Testimonial Text'


@admin.register(AICoachSection)
class AICoachSectionAdmin(ModelAdmin):
    """
    🤖 AI COACH SECTIONS - Editable Table View
    """
    list_display = ('id', 'heading', 'badge_text', 'button_text', 'status', 'order', 'created_at')
    list_display_links = ('id', 'heading')
    list_filter = ('status', 'created_at')
    search_fields = ('heading', 'description')
    list_editable = ('status', 'order')
    list_per_page = 50
    
    fieldsets = (
        ('🤖 AI Coach Content', {
            'fields': ('badge_text', 'heading', 'description', 'preview_image')
        }),
        ('🔗 Call to Action', {
            'fields': ('button_text', 'button_link')
        }),
        ('🎨 Design', {
            'fields': ('background_color',)
        }),
        ('⚙️ Settings', {
            'fields': ('status', 'order')
        }),
    )


@admin.register(FeatureSection)
class FeatureSectionAdmin(ModelAdmin):
    list_display = ('id', 'section_name', 'heading', 'status', 'order', 'created_at')
    list_display_links = ('id', 'section_name')
    list_filter = ('status', 'created_at')
    search_fields = ('section_name', 'heading', 'description')
    list_editable = ('order', 'status')
    
    fieldsets = (
        ('✨ Feature Content', {
            'fields': ('section_name', 'heading', 'sub_heading', 'description', 'image')
        }),
        ('🔗 Call to Action', {
            'fields': ('button_text', 'button_link')
        }),
        ('🎨 Design', {
            'fields': ('background_color',)
        }),
        ('⚙️ Settings', {
            'fields': ('status', 'order')
        }),
    )


@admin.register(CTASection)
class CTASectionAdmin(ModelAdmin):
    list_display = ('id', 'heading', 'button_text', 'status', 'created_at')
    list_display_links = ('id', 'heading')
    list_filter = ('status', 'created_at')
    search_fields = ('heading', 'description')
    
    fieldsets = (
        ('📣 CTA Content', {
            'fields': ('heading', 'description')
        }),
        ('🔗 Call to Action', {
            'fields': ('button_text', 'button_link')
        }),
        ('🎨 Design', {
            'fields': ('background_color', 'button_color')
        }),
        ('⚙️ Settings', {
            'fields': ('status',)
        }),
    )


@admin.register(FooterLink)
class FooterLinkAdmin(ModelAdmin):
    """
    🔗 FOOTER LINKS - Editable Table View
    Edit links directly in the list by category!
    """
    list_display = ('id', 'title', 'category', 'url', 'order', 'is_active', 'open_in_new_tab')
    list_display_links = ('id', 'title')
    list_filter = ('category', 'is_active', 'open_in_new_tab')
    search_fields = ('title', 'url')
    list_editable = ('category', 'order', 'is_active', 'open_in_new_tab')
    list_per_page = 100
    
    fieldsets = (
        ('🔗 Footer Link', {
            'fields': ('category', 'title', 'url', 'icon', 'order', 'is_active', 'open_in_new_tab')
        }),
    )


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(ModelAdmin):
    """
    📱 SOCIAL MEDIA - Editable Table View
    Edit all social links directly!
    """
    list_display = ('id', 'platform', 'url', 'icon', 'order', 'is_active')
    list_display_links = ('id', 'platform')
    list_filter = ('platform', 'is_active')
    search_fields = ('platform', 'url')
    list_editable = ('url', 'icon', 'order', 'is_active')
    list_per_page = 50
    
    fieldsets = (
        ('📱 Social Media', {
            'fields': ('platform', 'url', 'icon', 'order', 'is_active')
        }),
    )


@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    """
    ❓ FAQs - Editable Table View
    Edit questions and answers directly!
    """
    list_display = ('id', 'question_preview', 'answer_preview', 'category', 'order', 'status')
    list_display_links = ('id', 'question_preview')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('category', 'order', 'status')
    list_per_page = 50
    
    fieldsets = (
        ('❓ FAQ Content', {
            'fields': ('question', 'answer', 'category')
        }),
        ('⚙️ Settings', {
            'fields': ('order', 'status')
        }),
    )
    
    def question_preview(self, obj):
        return obj.question[:80] + '...' if len(obj.question) > 80 else obj.question
    question_preview.short_description = 'Question'
    
    def answer_preview(self, obj):
        return obj.answer[:100] + '...' if len(obj.answer) > 100 else obj.answer
    answer_preview.short_description = 'Answer'