# -*- coding: utf-8 -*-
# config.py

from authomatic.providers import oauth2, oauth1
import authomatic

CONFIG = {

    'wl': {  # Your internal provider name

        # Provider class
        'class_': oauth2.WindowsLive,

        'consumer_key': 'e9bf7a9a-13bc-4db8-af9d-f6626ec9705f',
        'consumer_secret': 'ekbvXCNU187!golTCD36[#|',
 
        'id': authomatic.provider_id(),
        'scope': oauth2.WindowsLive.user_info_scope, # + ['wl.skydrive'],
        '_name': 'Live',
        '_apis': {
            #'List your recent documents': ('GET', 'https://apis.live.net/v5.0/me/skydrive/recent_docs'),
            #'List your contacts': ('GET', 'https://apis.live.net/v5.0/me/contacts'),
        },    
        },

    'tw': {  # Your internal provider name

        # Provider class
        'class_': oauth1.Twitter,

        # Twitter is an AuthorizationProvider so we need to set several other
        # properties too:
        'consumer_key': '########################',
        'consumer_secret': '########################',
    },

    'fb': {

        'class_': oauth2.Facebook,

        # Facebook is an AuthorizationProvider too.
        'consumer_key': '########################',
        'consumer_secret': '########################',

        # But it is also an OAuth 2.0 provider and it needs scope.
        'scope': ['user_about_me', 'email', 'publish_stream'],
    },

}
