from django.core.cache import cache

CMS_DATA_CACHE_KEY = 'cms_landing_page_data'


def clear_cms_cache():
    cache.delete(CMS_DATA_CACHE_KEY)


def invalidate_cms_cache():
    clear_cms_cache()
