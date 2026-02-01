# manager/context_processors.py
from .models import HospitalSetting

def hospital_settings(request):
    """
    Makes hospital settings available to all templates globally.
    This allows us to use {{ hospital_settings.hospital_name }} anywhere.
    """
    return {
        'hospital_settings': HospitalSetting.load()
    }