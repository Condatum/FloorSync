from .models import UserSettings


def theme_preference(request):
    """Expose the authenticated user's persisted color scheme across all templates."""
    user = getattr(request, "user", None)
    if user and user.is_authenticated:
        settings_obj = UserSettings.objects.filter(user=user).only("dark_mode").first()
        if settings_obj is not None:
            scheme = "dark" if settings_obj.dark_mode else "light"
            return {
                "active_color_scheme": scheme,
                "active_theme_attr": scheme,
            }
    return {
        "active_color_scheme": "light dark",
        "active_theme_attr": "",
    }
