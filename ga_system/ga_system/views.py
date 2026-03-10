"""
Views for the ga_system project root — landing page.
"""

from django.views.generic import TemplateView


class LandingPageView(TemplateView):
    template_name = "landing.html"
