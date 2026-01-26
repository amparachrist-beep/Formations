def panier_count(request):
    '''
    Ajoute le nombre d'articles dans le panier au contexte global
    '''
    panier = request.session.get('panier', {})
    return {'panier_count': len(panier)}