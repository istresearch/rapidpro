from ...models import ClassifierType, ClassifierLog, Intent
from .views import ConnectView
from django.utils import timezone
import requests


class LuisType(ClassifierType):
    """
    Type for classifiers from Luis.ai
    """

    name = "Luis.ai"
    slug = "luis"
    icon = "icon-luis"

    CONFIG_APP_ID = "app_id"
    CONFIG_VERSION = "version"
    CONFIG_ENDPOINT_URL = "endpoint_url"
    CONFIG_PRIMARY_KEY = "primary_key"

    AUTH_HEADER = "Ocp-Apim-Subscription-Key"

    connect_view = ConnectView
    connect_blurb = """
    <a href="https://luis.ai">Luis.ai</a> is a Microsoft Azure platform that lets you interpret natural language in
    your bots. It supports 13 languages and is a highly scalable paid offering.
    """

    form_blurb = """
    You can find the attributes for your app on your Luis.ai app page.
    """

    @classmethod
    def get_active_intents_from_api(cls, classifier, logs):
        """
        Gets the current intents defined by this app, in Luis that's an attribute of the app version
        """
        app_id = classifier.config[cls.CONFIG_APP_ID]
        version = classifier.config[cls.CONFIG_VERSION]
        endpoint_url = classifier.config[cls.CONFIG_ENDPOINT_URL]
        primary_key = classifier.config[cls.CONFIG_PRIMARY_KEY]

        start = timezone.now()
        url = endpoint_url + "/apps/" + app_id + "/versions/" + version + "/intents"
        response = requests.get(url, headers={cls.AUTH_HEADER: primary_key})
        elapsed = (timezone.now() - start).total_seconds() * 1000

        log = ClassifierLog.from_response(classifier, url, response, "Synced Intents", "Syncing Error")
        log.request_time = elapsed
        logs.append(log)

        response.raise_for_status()
        response_json = response.json()

        intents = []
        for intent in response_json:
            intents.append(Intent(name=intent["name"], external_id=intent["id"]))

        return intents
