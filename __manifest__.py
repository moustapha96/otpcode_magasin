{
    'name': 'OTP Code Magasin',
    'version': '1.1',
    'category': 'Immobilier',
    'support': 'alhussein.khouma@ccbm.sn',
    'summary': 'Vérification OTP pour les partenaires par SMS',
    'description': 'Ce module permet la vérification OTP des partenaires par SMS.',
    'author': 'Al hussein KHOUMA',
    'depends': ['base', 'contacts'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
}



