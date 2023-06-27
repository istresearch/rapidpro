"""
Alternative to overwriting a file with customizations/any is to provide 'surgical overrides' in
the form of methods put into specific classes "after initialization, but before handle-ization".

Import this file just after all the urls in the main urls.py and run its overrides.
"""
class EngageOverrides:
    ENGAGE_OVERRIDES_RAN: bool = False

    @classmethod
    def RunEngageOverrides(cls):
        """
        Overrides that need to be conducted at the tail end of temba/urls.py
        """
        #logging.debug('Ran? ' + str(cls.ENGAGE_OVERRIDES_RAN))
        if cls.ENGAGE_OVERRIDES_RAN:
            return
        #dndif

        from django.conf import settings
        settings.PM_CONFIG.fetch_apk_link()

        cls.ENGAGE_OVERRIDES_RAN = True
    #enddef RunEngageOverrides
#endclass EngageOverrides
