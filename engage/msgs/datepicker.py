from django.conf import settings

class DatePickerMedia:
    js = ('{}js/bootstrap-datepicker.js'.format(settings.STATIC_URL),)
    css = {'all': ('{}css/bootstrap-datepicker3.css'.format(settings.STATIC_URL),)}
