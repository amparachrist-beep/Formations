def panier_count(request):
    '''
    Ajoute le nombre d'articles dans le panier au contexte global
    '''
    panier = request.session.get('panier', {})
    return {'panier_count': len(panier)}

from django.conf import settings

def moneroo_mode(request):
    """Expose MONEROO_API_KEY aux templates pour détecter le mode Sandbox"""
    return {
        'MONEROO_API_KEY': settings.MONEROO_API_KEY
    }