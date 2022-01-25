import json
from subprocess import CalledProcessError, check_call
import subprocess
import sys

import pytz
from django_redis import get_redis_connection

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError, call_command
from django.db import connection
from django.utils import timezone

from temba.campaigns.models import Campaign, CampaignEvent
from temba.channels.models import Channel
from temba.classifiers.models import Classifier
from temba.contacts.models import Contact, ContactField, ContactGroup, ContactURN
from temba.flows.models import Flow
from temba.globals.models import Global
from temba.locations.models import AdminBoundary
from temba.msgs.models import Label
from temba.orgs.models import Org
from temba.templates.models import Template, TemplateTranslation
from temba.tickets.models import Ticketer

# by default every user will have this password including the superuser
USER_PASSWORD = "Qwerty123"

# database dump containing admin boundary records
LOCATIONS_DUMP = "test-data/nigeria.bin"

ORG1 = dict(
    uuid="bf0514a5-9407-44c9-b0f9-3f36f9c18414",
    name="UNICEF",
    has_locations=True,
    languages=("eng", "fra"),
    sequence_start=10000,
    users=(
        dict(email="admin1@nyaruka.com", role="administrators", first_name="Andy", last_name="Admin"),
        dict(email="editor1@nyaruka.com", role="editors", first_name="Ed", last_name="McEditor"),
        dict(email="viewer1@nyaruka.com", role="viewers", first_name="Veronica", last_name="Views"),
        dict(email="agent1@nyaruka.com", role="agents", first_name="Ann", last_name="D'Agent"),
        dict(email="surveyor1@nyaruka.com", role="surveyors", first_name="Steve", last_name="Surveys"),
    ),
    classifiers=(
        dict(
            uuid="097e026c-ae79-4740-af67-656dbedf0263",
            classifier_type="luis",
            name="LUIS",
            config=dict(app_id="12345", version="0.1", endpoint_url="https://foo.com", primary_key="sesame"),
            intents=(
                dict(name="book_flight", external_id="10406609-9749-47d4-bd2b-f3b778d5a491"),
                dict(name="book_car", external_id="65eae80b-c0fb-4054-9d64-10de08e59a62"),
            ),
        ),
        dict(
            uuid="ff2a817c-040a-4eb2-8404-7d92e8b79dd0",
            classifier_type="wit",
            name="Wit.ai",
            config=dict(app_id="67890", access_token="sesame"),
            intents=(dict(name="register", external_id="register"),),
        ),
        dict(
            uuid="859b436d-3005-4e43-9ad5-3de5f26ede4c",
            classifier_type="bothub",
            name="BotHub",
            config=dict(access_token="access_token"),
            intents=(dict(name="intent", external_id="intent"),),
        ),
    ),
    channels=(
        dict(
            uuid="74729f45-7f29-4868-9dc4-90e491e3c7d8",
            name="Twilio",
            channel_type="T",
            address="+13605551212",
            scheme="tel",
            role=Channel.ROLE_SEND + Channel.ROLE_RECEIVE + Channel.ROLE_CALL + Channel.ROLE_ANSWER,
        ),
        dict(
            uuid="19012bfd-3ce3-4cae-9bb9-76cf92c73d49",
            name="Vonage",
            channel_type="NX",
            address="5789",
            scheme="tel",
            role=Channel.ROLE_SEND + Channel.ROLE_RECEIVE,
        ),
        dict(
            uuid="0f661e8b-ea9d-4bd3-9953-d368340acf91",
            name="Twitter",
            channel_type="TWT",
            address="ureport",
            scheme="twitter",
            role=Channel.ROLE_SEND + Channel.ROLE_RECEIVE,
        ),
    ),
    globals=(
        dict(uuid="c1a65849-243c-438e-987e-3fa5f884e3e1", key="org_name", name="Org Name", value="Nyaruka"),
        dict(uuid="57a18892-9fc9-45f7-aa14-c7e5b3583b54", key="access_token", name="Access Token", value="A213CD78"),
    ),
    groups=(
        dict(uuid="c153e265-f7c9-4539-9dbc-9b358714b638", name="Doctors", size=120),
        dict(uuid="5e9d8fab-5e7e-4f51-b533-261af5dea70d", name="Testers", size=10),
    ),
    fields=(
        dict(
            uuid="3a5891e4-756e-4dc9-8e12-b7a766168824",
            key="gender",
            label="Gender",
            value_type=ContactField.TYPE_TEXT,
        ),
        dict(uuid="903f51da-2717-47c7-a0d3-f2f32877013d", key="age", label="Age", value_type=ContactField.TYPE_NUMBER),
        dict(
            uuid="d83aae24-4bbf-49d0-ab85-6bfd201eac6d",
            key="joined",
            label="Joined",
            value_type=ContactField.TYPE_DATETIME,
        ),
        dict(uuid="de6878c1-b174-4947-9a65-8910ebe7d10f", key="ward", label="Ward", value_type=ContactField.TYPE_WARD),
        dict(
            uuid="3ca3e36b-3d5a-42a4-b292-482282ce9a90",
            key="district",
            label="District",
            value_type=ContactField.TYPE_DISTRICT,
        ),
        dict(
            uuid="1dddea55-9a3b-449f-9d43-57772614ff50",
            key="state",
            label="State",
            value_type=ContactField.TYPE_STATE,
        ),
    ),
    contacts=(
        dict(
            uuid="6393abc0-283d-4c9b-a1b3-641a035c34bf",
            name="Cathy",
            urns=["tel:+16055741111"],
            groups=["Doctors"],
            fields=dict(gender="F", state="Nigeria > Yobe", ward="Nigeria > Yobe > Gulani > Dokshi"),
            created_on="2021-06-01T12:29:30Z",
        ),
        dict(
            uuid="b699a406-7e44-49be-9f01-1a82893e8a10",
            name="Bob",
            urns=["tel:+16055742222"],
            fields=dict(joined="2019-01-24T04:32:22Z"),
            created_on="2020-12-31T16:45:30Z",
        ),
        dict(
            uuid="8d024bcd-f473-4719-a00a-bd0bb1190135",
            name="George",
            urns=["tel:+16055743333"],
            fields=dict(age="30"),
            created_on="2018-03-31T09:45:30Z",
        ),
        dict(
            uuid="9709c157-4606-4d41-9df3-9e9c9b4ae2d4",
            name="Alexandia",
            urns=["tel:+1605574444"],
            created_on="2020-12-31T16:45:30Z",
        ),
    ),
    labels=(
        dict(uuid="ebc4dedc-91c4-4ed4-9dd6-daa05ea82698", name="Reporting"),
        dict(uuid="a6338cdc-7938-4437-8b05-2d5d785e3a08", name="Testing"),
        dict(uuid="fe33e8e3-f32d-4167-8632-64c2ba1c574d", name="Youth"),
    ),
    flows=(
        dict(uuid="9de3663f-c5c5-4c92-9f45-ecbc09abcc85", name="Favorites", file="favorites_timeout.json"),
        dict(uuid="5890fe3a-f204-4661-b74d-025be4ee019c", name="Pick a Number", file="pick_a_number.json"),
        dict(uuid="70b04fa1-e2ee-4afd-b658-9a3f87f9b6f7", name="SMS Form", file="sms_form.json"),
        dict(uuid="2f81d0ea-4d75-4843-9371-3f7465311cce", name="IVR Flow", file="ivr_flow.json"),
        dict(uuid="a7c11d68-f008-496f-b56d-2d5cf4cf16a5", name="Send All", file="send_all.json"),
        dict(uuid="ed8cf8d4-a42c-4ce1-a7e3-44a2918e3cec", name="Contact Surveyor", file="contact_surveyor.json"),
        dict(uuid="376d3de6-7f0e-408c-80d6-b1919738bc80", name="Incoming Extra", file="incoming_extra.json"),
        dict(
            uuid="81c0f323-7e06-4e0c-a960-19c20f17117c",
            name="Parent Child Expiration",
            file="parent_child_expiration.json",
        ),
    ),
    campaigns=(
        dict(
            uuid="72aa12c5-cc11-4bc7-9406-044047845c70",
            name="Doctor Reminders",
            group="Doctors",
            events=(
                dict(flow="Favorites", offset_field="joined", offset="5", offset_unit="D", delivery_hour=12),
                dict(
                    uuid="3a92a964-3a8d-420b-9206-2cd9d884ac30",
                    base_language="eng",
                    message=dict(
                        eng="Hi @contact.name, it is time to consult with your patients.",
                        fra="Bonjour @contact.name, il est temps de consulter vos patients.",
                    ),
                    offset_field="joined",
                    offset="10",
                    offset_unit="M",
                ),
            ),
        ),
    ),
    templates=(
        dict(
            uuid="9c22b594-fcab-4b29-9bcb-ce4404894a80",
            name="revive_issue",
            translations=(
                dict(
                    channel_uuid="0f661e8b-ea9d-4bd3-9953-d368340acf91",
                    country="US",
                    language="eng",
                    content="Hi {{1}}, are you still experiencing problems with {{2}}?",
                    variable_count=2,
                    namespace="2d40b45c_25cd_4965_9019_f05d0124c5fa",
                    status="A",
                    external_id="eng1",
                ),
                dict(
                    channel_uuid="0f661e8b-ea9d-4bd3-9953-d368340acf91",
                    country=None,
                    language="fra",
                    content="Bonjour {{1}}, a tu des problems avec {{2}}?",
                    variable_count=2,
                    namespace="ea9cd1b3_b018_4ffe_bb0e_7cb898e527ae",
                    status="P",
                    external_id="fra1",
                ),
            ),
        ),
        dict(
            uuid="3b8dd151-1a91-411f-90cb-dd9065bb7a71",
            name="goodbye",
            translations=(
                dict(
                    channel_uuid="0f661e8b-ea9d-4bd3-9953-d368340acf91",
                    country=None,
                    language="fra",
                    content="Salut!",
                    variable_count=0,
                    namespace="",
                    status="A",
                    external_id="fra2",
                ),
            ),
        ),
    ),
    ticketers=(
        dict(
            uuid="f9c9447f-a291-4f3c-8c79-c089bbd4e713",
            name="Mailgun (IT Support)",
            ticketer_type="mailgun",
            config=dict(
                domain="tickets.rapidpro.io",
                api_key="sesame",
                to_address="bob@acme.com",
                brand_name="RapidPro",
                url_base="https://app.rapidpro.io",
            ),
        ),
        dict(
            uuid="4ee6d4f3-f92b-439b-9718-8da90c05490b",
            name="Zendesk (Nyaruka)",
            ticketer_type="zendesk",
            config=dict(
                subdomain="nyaruka", oauth_token="754845822", secret="sesame", push_id="1234-abcd", push_token="523562"
            ),
        ),
        dict(
            uuid="6c50665f-b4ff-4e37-9625-bc464fe6a999",
            name="Rocket.Chat",
            ticketer_type="rocketchat",
            config=dict(
                base_url="https://temba.rocket.chat/apps/public/1234",
                secret="123456789",
                admin_auth_token="1234",
                admin_user_id="ADMIN346",
            ),
        ),
    ),
)

ORG2 = dict(
    uuid="3ae7cdeb-fd96-46e5-abc4-a4622f349921",
    name="Nyaruka",
    has_locations=True,
    languages=("eng", "fra"),
    sequence_start=20000,
    users=(dict(email="admin2@nyaruka.com", role="administrators", first_name="", last_name=""),),
    channels=(
        dict(
            uuid="a89bc872-3763-4b95-91d9-31d4e56c6651",
            name="Twilio",
            channel_type="T",
            address="1234",
            scheme="tel",
            role=Channel.ROLE_SEND + Channel.ROLE_RECEIVE,
        ),
    ),
    classifiers=(),
    globals=(),
    groups=(dict(uuid="492e438c-02e5-43a4-953a-57410b7fe3dd", name="Doctors", size=120),),
    fields=(),
    contacts=(
        dict(
            uuid="26d20b72-f7d8-44dc-87f2-aae046dbff95",
            name="Fred",
            urns=["tel:+250700000005"],
            created_on="2020-12-31T16:45:30Z",
        ),
    ),
    labels=(),
    flows=(
        dict(uuid="f161bd16-3c60-40bd-8c92-228ce815b9cd", name="Favorites", file="favorites_timeout.json"),
        dict(uuid="5277916d-6011-41ac-a4a4-f6ac6a4f1dd9", name="Send All", file="send_all.json"),
    ),
    campaigns=(),
    templates=(),
    ticketers=(),
)

ORGS = [ORG1, ORG2]

# database id sequences to be reset to make ids predictable
RESET_SEQUENCES = (
    "contacts_contact_id_seq",
    "contacts_contacturn_id_seq",
    "contacts_contactgroup_id_seq",
    "flows_flow_id_seq",
    "channels_channel_id_seq",
    "campaigns_campaign_id_seq",
    "campaigns_campaignevent_id_seq",
    "msgs_label_id_seq",
    "templates_template_id_seq",
    "templates_templatetranslation_id_seq",
)


class Command(BaseCommand):
    help = "Generates a database suitable for mailroom testing"

    def handle(self, *args, **kwargs):
        self._log("Checking Postgres database version... ")

        result = subprocess.run(["pg_dump", "--version"], stdout=subprocess.PIPE)
        version = result.stdout.decode("utf8")
        if version.split(" ")[-1].find("11.") == 0:
            self._log(self.style.SUCCESS("OK") + "\n")
        else:
            self._log(
                "\n" + self.style.ERROR("Incorrect pg_dump version, needs version 11.*, found: " + version) + "\n"
            )
            sys.exit(1)

        self._log("Initializing mailroom_test database...\n")

        # drop and recreate the mailroom_test db and user
        subprocess.check_call('psql -c "DROP DATABASE IF EXISTS mailroom_test;"', shell=True)
        subprocess.check_call('psql -c "CREATE DATABASE mailroom_test;"', shell=True)
        subprocess.check_call('psql -c "DROP USER IF EXISTS mailroom_test;"', shell=True)
        subprocess.check_call("psql -c \"CREATE USER mailroom_test PASSWORD 'temba';\"", shell=True)
        subprocess.check_call('psql -c "ALTER ROLE mailroom_test WITH SUPERUSER;"', shell=True)

        # always use mailroom_test as our db
        settings.DATABASES["default"]["NAME"] = "mailroom_test"
        settings.DATABASES["default"]["USER"] = "mailroom_test"

        # patch UUID generation so it's deterministic
        from temba.utils import uuid

        uuid.default_generator = uuid.seeded_generator(1234)

        self._log("Running migrations...\n")

        # run our migrations to put our database in the right state
        call_command("migrate")

        # this is a new database so clear out redis
        self._log("Clearing out Redis cache... ")
        r = get_redis_connection()
        r.flushdb()
        self._log(self.style.SUCCESS("OK") + "\n")

        self._log("Creating superuser... ")
        superuser = User.objects.create_superuser("root", "root@nyaruka.com", USER_PASSWORD)
        self._log(self.style.SUCCESS("OK") + "\n")

        mr_cmd = 'mailroom -db="postgres://mailroom_test:temba@localhost/mailroom_test?sslmode=disable" -uuid-seed=123'
        input(f"\nPlease start mailroom:\n   % ./{mr_cmd}\n\nPress enter when ready.\n")

        country, locations = self.load_locations(LOCATIONS_DUMP)

        # create each of our orgs
        for spec in ORGS:
            self.create_org(spec, superuser, country, locations)

        # dump our file
        subprocess.check_call("pg_dump -Fc mailroom_test > mailroom_test.dump", shell=True)

        self._log("\n" + self.style.SUCCESS("Success!") + " Dump file: mailroom_test.dump\n\n")

    def load_locations(self, path):
        """
        Loads admin boundary records from the given dump of that table
        """
        self._log("Loading locations from %s... " % path)

        # load dump into current db with pg_restore
        db_config = settings.DATABASES["default"]
        try:
            subprocess.check_call(
                f"export PGPASSWORD={db_config['PASSWORD']} && pg_restore -h {db_config['HOST']} "
                f"-p {db_config['PORT']} -U {db_config['USER']} -w -d {db_config['NAME']} {path}",
                shell=True,
            )
        except subprocess.CalledProcessError:  # pragma: no cover
            raise CommandError("Error occurred whilst calling pg_restore to load locations dump")

        # fetch as tuples of (WARD, DISTRICT, STATE)
        wards = AdminBoundary.objects.filter(level=3).prefetch_related("parent", "parent__parent")
        locations = [(w, w.parent, w.parent.parent) for w in wards]

        country = AdminBoundary.objects.filter(level=0).get()

        self._log(self.style.SUCCESS("OK") + "\n")
        return country, locations

    def create_org(self, spec, superuser, country, locations):
        self._log(f"\nCreating org {spec['name']}...\n")

        org = Org.objects.create(
            uuid=spec["uuid"],
            name=spec["name"],
            timezone=pytz.timezone("America/Los_Angeles"),
            brand="rapidpro.io",
            country=country,
            created_on=timezone.now(),
            created_by=superuser,
            modified_by=superuser,
        )
        ContactGroup.create_system_groups(org)
        ContactField.create_system_fields(org)
        org.init_topups(100_000)

        # set our sequences to make ids stable across orgs
        with connection.cursor() as cursor:
            for seq_name in RESET_SEQUENCES:
                cursor.execute(f"ALTER SEQUENCE {seq_name} RESTART WITH {spec['sequence_start']}")

        self.create_users(spec, org)
        self.create_channels(spec, org, superuser)
        self.create_fields(spec, org, superuser)
        self.create_globals(spec, org, superuser)
        self.create_labels(spec, org, superuser)
        self.create_groups(spec, org, superuser)
        self.create_flows(spec, org, superuser)
        self.create_contacts(spec, org, superuser)
        self.create_group_contacts(spec, org, superuser)
        self.create_campaigns(spec, org, superuser)
        self.create_templates(spec, org, superuser)
        self.create_classifiers(spec, org, superuser)
        self.create_ticketers(spec, org, superuser)

        return org

    def create_users(self, spec, org):
        self._log(f"Creating {len(spec['users'])} users... ")

        for u in spec["users"]:
            user = User.objects.create_user(
                u["email"], u["email"], USER_PASSWORD, first_name=u["first_name"], last_name=u["last_name"]
            )
            getattr(org, u["role"]).add(user)
            user.set_org(org)

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_channels(self, spec, org, user):
        self._log(f"Creating {len(spec['channels'])} channels... ")

        for c in spec["channels"]:
            Channel.objects.create(
                org=org,
                name=c["name"],
                channel_type=c["channel_type"],
                address=c["address"],
                schemes=[c["scheme"]],
                uuid=c["uuid"],
                role=c["role"],
                created_by=user,
                modified_by=user,
            )

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_classifiers(self, spec, org, user):
        self._log(f"Creating {len(spec['classifiers'])} classifiers... ")

        for c in spec["classifiers"]:
            classifier = Classifier.objects.create(
                org=org,
                name=c["name"],
                config=c["config"],
                classifier_type=c["classifier_type"],
                uuid=c["uuid"],
                created_by=user,
                modified_by=user,
            )

            # add the intents
            for intent in c["intents"]:
                classifier.intents.create(
                    name=intent["name"], external_id=intent["external_id"], created_on=timezone.now()
                )

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_ticketers(self, spec, org, user):
        self._log(f"Creating {len(spec['ticketers'])} ticketers... ")

        for t in spec["ticketers"]:
            Ticketer.objects.create(
                org=org,
                name=t["name"],
                config=t["config"],
                ticketer_type=t["ticketer_type"],
                uuid=t["uuid"],
                created_by=user,
                modified_by=user,
            )

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_fields(self, spec, org, user):
        self._log(f"Creating {len(spec['fields'])} fields... ")

        for f in spec["fields"]:
            field = ContactField.user_fields.create(
                org=org,
                key=f["key"],
                label=f["label"],
                value_type=f["value_type"],
                show_in_table=True,
                created_by=user,
                modified_by=user,
            )
            field.uuid = f["uuid"]
            field.save(update_fields=["uuid"])

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_globals(self, spec, org, user):
        self._log(f"Creating {len(spec['globals'])} globals... ")

        for g in spec["globals"]:
            Global.objects.create(
                org=org, key=g["key"], name=g["name"], value=g["value"], created_by=user, modified_by=user
            )

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_groups(self, spec, org, user):
        self._log(f"Creating {len(spec['groups'])} groups... ")

        for g in spec["groups"]:
            if g.get("query"):
                group = ContactGroup.create_dynamic(org, user, g["name"], g["query"], evaluate=False)
            else:
                group = ContactGroup.create_static(org, user, g["name"])
            group.uuid = g["uuid"]
            group.save(update_fields=["uuid"])

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_labels(self, spec, org, user):
        self._log(f"Creating {len(spec['labels'])} labels... ")

        for l in spec["labels"]:
            Label.label_objects.create(org=org, name=l["name"], uuid=l["uuid"], created_by=user, modified_by=user)

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_flows(self, spec, org, user):
        self._log(f"Creating {len(spec['flows'])} flows... ")

        for f in spec["flows"]:
            with open("media/test_flows/mailroom/" + f["file"], "r") as flow_file:
                org.import_app(json.load(flow_file), user)

                # set the uuid on this flow
                Flow.objects.filter(org=org, name=f["name"]).update(uuid=f["uuid"])

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_campaigns(self, spec, org, user):
        self._log(f"Creating {len(spec['campaigns'])} campaigns... ")

        for c in spec["campaigns"]:
            group = ContactGroup.all_groups.get(org=org, name=c["group"])
            campaign = Campaign.objects.create(
                name=c["name"],
                group=group,
                is_archived=False,
                org=org,
                created_by=user,
                modified_by=user,
                uuid=c["uuid"],
            )

            for e in c.get("events", []):
                field = ContactField.all_fields.get(org=org, key=e["offset_field"])

                if "flow" in e:
                    flow = Flow.objects.get(org=org, name=e["flow"])
                    CampaignEvent.create_flow_event(
                        org,
                        user,
                        campaign,
                        field,
                        e["offset"],
                        e["offset_unit"],
                        flow,
                        delivery_hour=e.get("delivery_hour", -1),
                    )
                else:
                    evt = CampaignEvent.create_message_event(
                        org,
                        user,
                        campaign,
                        field,
                        e["offset"],
                        e["offset_unit"],
                        e["message"],
                        delivery_hour=e.get("delivery_hour", -1),
                        base_language=e["base_language"],
                    )
                    evt.flow.uuid = e["uuid"]
                    evt.flow.save()

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_templates(self, spec, org, templates):
        self._log(f"Creating {len(spec['templates'])} templates... ")

        for t in spec["templates"]:
            Template.objects.create(org=org, uuid=t["uuid"], name=t["name"])
            for tt in t["translations"]:
                channel = Channel.objects.get(uuid=tt["channel_uuid"])
                TemplateTranslation.get_or_create(
                    channel,
                    t["name"],
                    tt["language"],
                    tt["country"],
                    tt["content"],
                    tt["variable_count"],
                    tt["status"],
                    tt["external_id"],
                    tt["namespace"],
                )

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_contacts(self, spec, org, user):
        self._log(f"Creating {len(spec['contacts'])} contacts... ")

        fields_by_key = {f.key: f for f in ContactField.user_fields.all()}

        for c in spec["contacts"]:
            values = {fields_by_key[key]: val for key, val in c.get("fields", {}).items()}
            groups = list(ContactGroup.user_groups.filter(org=org, name__in=c.get("groups", [])))

            contact = Contact.create(org, user, c["name"], language="", urns=c["urns"], fields=values, groups=groups)
            contact.uuid = c["uuid"]
            contact.created_on = c["created_on"]
            contact.save(update_fields=("uuid", "created_on"))

        self._log(self.style.SUCCESS("OK") + "\n")

    def create_group_contacts(self, spec, org, user):
        self._log(f"Generating group contacts...")

        for g in spec["groups"]:
            size = int(g.get("size", 0))
            if size > 0:
                group = ContactGroup.user_groups.get(org=org, name=g["name"])

                contacts = []
                for i in range(size):
                    urn = f"tel:+250788{i:06}"
                    contact = ContactURN.lookup(org, urn)
                    if not contact:
                        contact = Contact.create(org, user, name="", language="", urns=[urn], fields={}, groups=[])
                    contacts.append(contact)

                Contact.bulk_change_group(user, contacts, group, add=True)

        self._log(self.style.SUCCESS("OK") + "\n")

    def _log(self, text):
        self.stdout.write(text, ending="")
        self.stdout.flush()
