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
            "image": lambda request: static("sample/login-bg.jpg"),
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
                    "title": _("User Management"),
                    "separator": True,  # Top border
                    "collapsible": True,  # Collapsible group of links
                    "items": [
                        {
                            "title": _("Users"),
                            "icon": "people",
                            "link": reverse_lazy("admin:users_user_changelist"),
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
                    "title": _("Page Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("Pages"),
                            "icon": "pages",
                            "link": reverse_lazy("admin:cms_page_changelist"),
                        },
                    ],
                },
                {
                    "title": _("CMS Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("CMS"),
                            "icon": "auto_stories",
                            # "link": reverse_lazy("admin:cms_landingpagecontent_changelist"),
                        },
                    ],
                },
                {
                    "title": _("FAQ Management"),
                    "separator": True,
                    "collapsible": True,
                    "items": [
                        {
                            "title": _("FAQs"),
                            "icon": "help",
                            "link": reverse_lazy("admin:cms_faq_changelist"),
                        },
                    ],
                }
            ],
        },
    }
