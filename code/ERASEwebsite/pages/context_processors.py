from .models import WebsiteTheme


def website_theme(request):
    theme = WebsiteTheme.objects.filter(pk=1).first() or WebsiteTheme()
    return {'website_theme': theme}
