
PWA_SERVICE_WORKER_PATH = os.path.join(BASE_DIR, "static", "js", "serviceworker.js")
PWA_APP_NAME = 'Padword'
PWA_APP_DESCRIPTION = "Padword PWA"
PWA_APP_THEME_COLOR = '#000000'
PWA_APP_BACKGROUND_COLOR = '#ffffff'
PWA_APP_DISPLAY = 'standalone'
PWA_APP_START_URL = '/guestpda/'
PWA_APP_STATUS_BAR_COLOR = 'default'
PWA_APP_ICONS = [
    {
        'src': 'static/images/icon-160x160.png',
        'sizes': '160x160'
    }
]
# PWA_APP_ICONS_APPLE = [
#     {
#         'src': 'static/images/icon-160x160.png',
#         'sizes': '160x160'
#     }
# ]
# PWA_APP_SPLASH_SCREEN = [
#     {
#         'src': 'static/images/icon.png',
#         'media': '(device-width: 320px) and (device-height: 568px) and (-webkit-device-pixel-ratio: 2)'
#     }
# ]
PWA_APP_DIR = 'ltr'
PWA_APP_LANG = 'es-ES'
