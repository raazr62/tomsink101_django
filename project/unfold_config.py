from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.apps import apps
from apps.system_setting.admin_profile import update_profile


def _get_about_system_instance():
    """Return the AboutSystem instance or None.

    This is safe to call at import time because it first checks whether
    the app registry is ready. It only imports the model when Django
    apps are loaded. Uses caching for better performance.
    """
    try:
        if not apps.ready:
            return None
        from apps.system_setting.models import AboutSystem

        return AboutSystem.get_instance()
    except Exception:
        # Any failure here should not break settings import.
        return None


def get_unfold_settings():
    # Use callables that resolve values at runtime (when a request is available)
    # so we avoid touching the ORM during settings import.
    return {
        "SITE_TITLE": (lambda request: (_get_about_system_instance().title if _get_about_system_instance() else '')),
        "SITE_HEADER": (lambda request: (_get_about_system_instance().title if _get_about_system_instance() else '')),
        "SITE_SUBHEADER": (lambda request: (_get_about_system_instance().title if _get_about_system_instance() else '')),
        "SITE_URL": "/",
        "SITE_ICON": {
            "light": (lambda request: (_get_about_system_instance().logo.url if _get_about_system_instance() and _get_about_system_instance().logo else '')),
            "dark": (lambda request: (_get_about_system_instance().logo.url if _get_about_system_instance() and _get_about_system_instance().logo else '')),
        },
        "SITE_SYMBOL": "speed",  # symbol from icon set
        "SITE_FAVICONS": [
            {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": (lambda request: (_get_about_system_instance().favicon.url if _get_about_system_instance() and _get_about_system_instance().favicon else '')),
            },
        ],
        "DASHBOARD_CALLBACK": "apps.dashboard.views.dashboard_callback",

        "SHOW_HISTORY": True,  # show/hide "History" button, default: True
        "SHOW_VIEW_ON_SITE": True,  # show/hide "View on site" button, default: True
        "SHOW_BACK_BUTTON": True,  # show/hide "Back" button on changeform in header, default: False
        # "THEME": "light",
        "LOGIN": {
            "image": lambda request: static("logo/login.png"),
            "redirect_after": lambda request: reverse_lazy("admin:APP_MODEL_changelist"),
        },
        "BORDER_RADIUS": "6px",
        "SIDEBAR": {
            "show_search": True,  # Search in applications and models names
            "show_all_applications": True,  # Dropdown with all applications and models
            "navigation": [
                {
                    "items": [
                        {
                            "title": _("Dashboard"),
                            "icon": "dashboard",
                            "link": reverse_lazy("admin:index"),
                            "permission": lambda request: request.user.is_superuser,
                        },
                    ],
                },
                {
                    "title": _("User"),
                    "separator": True,  # Top border
                    "collapsible": True,  # Collapsible group of links
                    "items": [
                        {
                            "title": _("Users"),
                            "icon": "people",
                            "link": reverse_lazy("admin:users_profile_changelist"),
                        },
                    ],
                },
                {
                    "title": _("Pre-Launch"),
                    "separator": True,  # Top border
                    "collapsible": True,  # Collapsible group of links
                    "items": [
                        {
                            "title": _("Pre-Launch Users"),
                            "icon": "people",
                            "link": reverse_lazy("admin:prelaunch_prelaunchuser_changelist"),
                        },
                    ],
                },
                {
                    "title": _("Subscription"),
                    "separator": True,  # Top border
                    "collapsible": True,  # Collapsible group of links
                    "items": [
                        {
                            "title": _("Packages"),
                            "icon": "package_2",
                            "link": reverse_lazy("admin:subscription_package_changelist"),
                        },
                        {
                            "title": _("Subscribers"),
                            "icon": "how_to_reg",
                            "link": reverse_lazy("admin:subscription_subscription_changelist"),
                        },
                        {
                            "title": _("Pricing Sections"),
                            "icon": "barcode_reader",
                            "link": reverse_lazy("admin:subscription_pricingsection_changelist"),
                        },
                        {
                            "title": _("Package Features"),
                            "icon": "featured_play_list",
                            "link": reverse_lazy("admin:subscription_packagefeature_changelist"),
                        },
                    ],
                },
                {
                    "title": _("System Setting"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Update Profile"),
                            "icon": "edit",
                            "link": lambda req: update_profile(req),
                        },
                        {
                            "title": _("About System"),
                            "icon": "info",
                            "link": reverse_lazy(
                                "admin:system_setting_aboutsystem_changelist"
                            ),
                        },
                        {
                            "title": _("Social Media"),
                            "icon": "share",
                            "link": reverse_lazy(
                                "admin:system_setting_socialmedia_changelist"
                            ),
                        },
                        {
                            "title": _("SMTP Settings"),
                            "icon": "email",
                            "link": reverse_lazy(
                                "admin:system_setting_smtpsetting_changelist"
                            ),
                        },
                        {
                            "title": _("System Color"),
                            "icon": "palette",
                            "link": reverse_lazy(
                                "admin:system_setting_systemcolor_changelist"
                            ),
                        }
                    ],
                },
                {
                    "title": _("Content"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("🎯 CMS Dashboard"),
                            "icon": "dashboard_customize",
                            "link": reverse_lazy("admin:cms_websitecontentmanager_changelist"),
                        },
                        {
                            "title": _("Hero Section"),
                            "icon": "home",
                            "link": reverse_lazy("admin:cms_herosection_changelist"),
                        },
                        {
                            "title": _("Success Stories"),
                            "icon": "stars",
                            "link": reverse_lazy("admin:cms_successstoriessection_changelist"),
                        },
                        {
                            "title": _("AI Coach"),
                            "icon": "smart_toy",
                            "link": reverse_lazy("admin:cms_aicoachsection_changelist"),
                        },
                        {
                            "title": _("Features"),
                            "icon": "auto_awesome",
                            "link": reverse_lazy("admin:cms_featuresection_changelist"),
                        },
                        {
                            "title": _("Call-to-Action"),
                            "icon": "campaign",
                            "link": reverse_lazy("admin:cms_ctasection_changelist"),
                        },
                        {
                            "title": _("Footer & Social"),
                            "icon": "link",
                            "link": reverse_lazy("admin:cms_footerlink_changelist"),
                        },
                        {
                            "title": _("FAQs"),
                            "icon": "help",
                            "link": reverse_lazy("admin:cms_faq_changelist"),
                        },
                        {
                            "title": _("Legal Pages"),
                            "icon": "gavel",
                            "link": reverse_lazy("admin:cms_page_changelist"),
                        },
                    ],
                },
                {
                    "title": _("Reviews & Feedback"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Reviews"),
                            "icon": "star",
                            "link": reverse_lazy("admin:review_review_changelist"),
                        },
                        {
                            "title": _("Categories"),
                            "icon": "category",
                            "link": reverse_lazy("admin:review_reviewcategory_changelist"),
                        },
                        {
                            "title": _("Settings"),
                            "icon": "settings",
                            "link": reverse_lazy("admin:review_reviewsettings_changelist"),
                        },
                    ],
                },
                {
                    "title": _("AI Chat"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("User Chats Sessions"),
                            "icon": "assistant_device",
                            "link": reverse_lazy("admin:manageai_chatsession_changelist"),
                        },
                        {
                            "title": _("AI Chat Messages"),
                            "icon": "assistant_on_hub",
                            "link": reverse_lazy("admin:manageai_chatmessage_changelist"),
                        },
                    ],
                },
                {
                    "title": _("User Task"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("User Workout Sessions"),
                            "icon": "directions_run",
                            "link": reverse_lazy("admin:task_workoutplan_changelist"),
                        },
                        {
                            "title": _("User Exercises"),
                            "icon": "exercise",
                            "link": reverse_lazy("admin:task_exercise_changelist"),
                        },
                        {
                            "title": _("User Diet Plans"),
                            "icon": "nutrition",
                            "link": reverse_lazy("admin:task_dietplan_changelist"),
                        },
                        {
                            "title": _("User Meals"),
                            "icon": "skillet",
                            "link": reverse_lazy("admin:task_meal_changelist"),
                        },
                        {
                            "title": _("User Daily Progress"),
                            "icon": "area_chart",
                            "link": reverse_lazy("admin:task_dailyprogress_changelist"),
                        },
                    ],
                },
            ],
        },
    }
