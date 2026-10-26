"""
Quando o django-debug-toolbar entra em ação no ambiente de desenvolvimento.
"""


def _default_show_toolbar(request) -> bool:
    # import tardio: o debug_toolbar só está em INSTALLED_APPS nas settings de dev
    from debug_toolbar.middleware import show_toolbar

    return show_toolbar(request)


def show_toolbar_for_pages(request) -> bool:
    """
    O toolbar só aparece em páginas HTML (admin, API navegável do DRF). As chamadas JSON do front
    pagavam a instrumentação dele (SQL, cache, sinais, templates) sem nunca exibi-lo: ~35% a mais
    de tempo por chamada no runserver.
    """
    return "text/html" in request.headers.get("Accept", "") and _default_show_toolbar(request)
