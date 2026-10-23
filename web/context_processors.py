from django.conf import settings


def demo(request):
    return {"demo_as_of": settings.DEMO_AS_OF}
