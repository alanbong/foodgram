from django.urls import get_resolver


def list_urls(patterns, prefix=''):
    for pattern in patterns:
        if hasattr(pattern, 'url_patterns'):
            list_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            print(f"{prefix}{pattern.pattern}")


list_urls(get_resolver().url_patterns)
