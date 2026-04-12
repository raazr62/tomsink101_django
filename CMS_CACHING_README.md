# CMS Redis Caching Implementation

## Overview

Redis caching has been added to the `CompleteCMSDataView` endpoint to improve performance. The landing page data is now cached in Redis, reducing database queries on subsequent requests.

## How It Works

### First Request

1. User hits the `/data/` endpoint for the first time
2. The view checks Redis cache for the key `cms_landing_page_data`
3. Cache miss - data is fetched from the database
4. Serialized data is cached in Redis for 24 hours
5. Response is returned to the user

### Subsequent Requests

1. User hits the `/data/` endpoint again
2. The view checks Redis cache
3. Cache hit - data is returned immediately from Redis (no database queries)
4. Response is returned to the user (much faster)

## Configuration

### Settings

Redis cache is configured in `project/settings.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': config('REDIS_CACHE_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        },
        'TIMEOUT': 24 * 60 * 60,  # 24 hours default cache timeout
    }
}
```

### Environment Variable

You can set a custom Redis URL in your `.env` file:

```
REDIS_CACHE_URL=redis://username:password@hostname:port/database
```

Default: `redis://127.0.0.1:6379/1` (Database 1, keeping Database 0 for Celery)

## Cache Invalidation

### Automatic

The cache is automatically invalidated when any CMS data is updated:

- When HeroSection is created/updated/deleted
- When SuccessStoriesSection is created/updated/deleted
- When AICoachSection is created/updated/deleted
- When FeatureSection is created/updated/deleted
- When FAQ is created/updated/deleted
- When SocialMediaLink is created/updated/deleted
- When ContactInfo is created/updated/deleted
- When LegalDocument is created/updated/deleted

This is handled by Django signals in `apps/cms/signals.py`.

### Manual

You can manually clear the cache using the management command:

```bash
python manage.py clear_cms_cache
```

Or programmatically:

```python
from apps.cms.cache_utils import clear_cms_cache

clear_cms_cache()
```

## Performance Impact

### Expected Improvements

- **First request**: Same time as before (database + serialization)
- **Subsequent requests**: 10-100x faster (Redis lookup only)
- **Landing page**: Should load significantly faster with fewer database queries

### Cache Duration

- Cache timeout is set to 24 hours
- You can modify `TIMEOUT` in settings.py if needed
- Cache is automatically cleared whenever CMS data is updated

## Utilities

### Files Added/Modified

1. **apps/cms/cache_utils.py** - Cache utility functions
   - `clear_cms_cache()` - Clear the cache
   - `invalidate_cms_cache()` - Alias for clear_cms_cache()

2. **apps/cms/signals.py** - Django signals for cache invalidation
   - Listens to post_save and post_delete signals

3. **apps/cms/apps.py** - App configuration
   - Registers signals on app ready

4. **apps/cms/views.py** - Updated CompleteCMSDataView
   - Added cache check before database query
   - Cache data after fetching from database

5. **project/settings.py** - Added CACHES configuration

6. **Management Command**: `clear_cms_cache`
   - Usage: `python manage.py clear_cms_cache`

## Monitoring

To check if caching is working, you can:

1. Monitor incoming requests to see if database queries decrease
2. Check Redis using redis-cli:

   ```bash
   redis-cli
   SELECT 1
   KEYS cms_*
   GET cms_landing_page_data
   ```

3. Look for "cache hit" behavior by comparing response times

## Troubleshooting

### Cache not clearing after updates

- Ensure `CACHES` is properly configured in settings.py
- Check that Redis is running and accessible
- Verify signals.py is being imported (check app's ready() method)

### Redis connection errors

- Ensure Redis is running: `redis-cli ping` should return `PONG`
- Check REDIS_CACHE_URL environment variable
- Verify database number (default is 1, different from Celery's 0)

### Cache serving stale data

- Manually clear: `python manage.py clear_cms_cache`
- Or update any CMS model to trigger automatic invalidation

## Future Enhancements

Consider implementing:

- Cache warming on deployment
- Cache statistics/monitoring dashboard
- Different cache timeouts for different data types
- Cache preloading for specific cache keys
