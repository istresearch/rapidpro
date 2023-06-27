import json
import operator
from functools import reduce

from django.db.models import Q
from django.db.models.functions import Upper

from temba.channels.models import Channel
from temba.contacts.models import Contact, ContactGroup, ContactGroupCount, ContactURN
from temba.utils.models.es import IDSliceQuerySet

from . import SearchException, search_contacts

SEARCH_ALL_GROUPS = "g"
SEARCH_STATIC_GROUPS = "s"
SEARCH_CONTACTS = "c"
SEARCH_URNS = "u"


def omnibox_query(org, **kwargs):
    """
    Performs a omnibox query based on the given arguments
    """
    # determine what type of group/contact/URN lookup is being requested
    contact_uuids = kwargs.get("c", None)  # contacts with ids
    group_uuids = kwargs.get("g", None)  # groups with ids
    urn_ids = kwargs.get("u", None)  # URNs with ids
    search = kwargs.get("search", None)  # search of groups, contacts and URNs
    types = list(kwargs.get("types", ""))  # limit search to types (g | s | c | u)

    if contact_uuids:
        return (
            Contact.objects.filter(
                org=org, status=Contact.STATUS_ACTIVE, is_active=True, uuid__in=contact_uuids.split(",")
            )
            .distinct()
            .order_by("name")
        )

    elif group_uuids:
        return ContactGroup.get_groups(org).filter(uuid__in=group_uuids.split(",")).order_by("name")

    elif urn_ids:
        return ContactURN.objects.filter(org=org, id__in=urn_ids.split(",")).select_related("contact").order_by("path")

    # searching returns something which acts enough like a queryset to be paged
    return omnibox_mixed_search(org, search, types)


def term_search(queryset, fields, terms):
    term_queries = []
    for term in terms:
        field_queries = []
        for field in fields:
            field_queries.append(Q(**{field: term}))
        term_queries.append(reduce(operator.or_, field_queries))

    return queryset.filter(reduce(operator.and_, term_queries))


def omnibox_mixed_search(org, query, types):
    """
    Performs a mixed group, contact and URN search, returning the first N matches of each type.
    """
    query_terms = query.split(" ") if query else None
    search_types = types or (SEARCH_ALL_GROUPS, SEARCH_CONTACTS, SEARCH_URNS)
    per_type_limit = 25
    results = []

    if SEARCH_ALL_GROUPS in search_types or SEARCH_STATIC_GROUPS in search_types:
        groups = ContactGroup.get_groups(org, ready_only=True)

        # exclude dynamic groups if not searching all groups
        if SEARCH_ALL_GROUPS not in search_types:
            groups = groups.filter(query=None)

        if query:
            groups = term_search(groups, ("name__icontains",), query_terms)

        results += list(groups.order_by(Upper("name"))[:per_type_limit])

    if SEARCH_CONTACTS in search_types:
        try:
            # query elastic search for contact ids, then fetch contacts from db
            search_results = search_contacts(org, query, group=org.active_contacts_group, sort="name")
            contacts = IDSliceQuerySet(
                Contact,
                search_results.contact_ids,
                offset=0,
                total=len(search_results.contact_ids),
                only=("id", "uuid", "name", "org_id"),
            ).prefetch_related("org")

            results += list(contacts[:per_type_limit])
            Contact.bulk_urn_cache_initialize(contacts=results)

        except SearchException:
            pass

    if SEARCH_URNS in search_types:
        if not org.is_anon and query and len(query) >= 3:
            try:
                # build an OR'ed query of all sendable schemes
                sendable_schemes = org.get_schemes(Channel.ROLE_SEND)
                scheme_query = " OR ".join(f"{s} ~ {json.dumps(query)}" for s in sendable_schemes)
                search_results = search_contacts(org, scheme_query, group=org.active_contacts_group, sort="name")
                urns = ContactURN.objects.filter(
                    contact_id__in=search_results.contact_ids, scheme__in=sendable_schemes
                )
                results += list(urns.prefetch_related("contact").order_by(Upper("path"))[:per_type_limit])
            except SearchException:
                pass

    return results


def omnibox_serialize(org, groups, contacts, *, urns=(), raw_urns=(), json_encode=False):
    """
    Shortcut for proper way to serialize a queryset of groups and contacts for omnibox component
    """
    serialized = omnibox_results_to_dict(org, list(groups) + list(contacts) + list(urns), version="2")

    serialized += [{"type": "urn", "id": u} for u in raw_urns]

    if json_encode:
        return [json.dumps(_) for _ in serialized]

    return serialized


def omnibox_deserialize(org, omnibox):
    group_ids = [item["id"] for item in omnibox if item["type"] == "group"]
    contact_ids = [item["id"] for item in omnibox if item["type"] == "contact"]
    urns = [item["id"] for item in omnibox if item["type"] == "urn"] if not org.is_anon else []

    return {
        "groups": org.groups.filter(uuid__in=group_ids, is_active=True),
        "contacts": Contact.objects.filter(uuid__in=contact_ids, org=org, is_active=True),
        "urns": urns,
    }


def omnibox_results_to_dict(org, results, version: str = "1"):
    """
    Converts the result of a omnibox query (queryset of contacts, groups or URNs, or a list) into a dict {id, text}
    """
    formatted = []

    groups = [r for r in results if isinstance(r, ContactGroup)]
    group_counts = ContactGroupCount.get_totals(groups) if groups else {}

    for obj in results:
        if isinstance(obj, ContactGroup):
            if version == "1":
                result = {"id": "g-%s" % obj.uuid, "text": obj.name, "extra": group_counts[obj]}
            else:
                result = {"id": obj.uuid, "name": obj.name, "type": "group", "count": group_counts[obj]}
        elif isinstance(obj, Contact):
            if version == "1":
                if org.is_anon:
                    result = {"id": "c-%s" % obj.uuid, "text": obj.get_display(org)}
                else:
                    result = {"id": "c-%s" % obj.uuid, "text": obj.get_display(org), "extra": obj.get_urn_display()}
            else:
                if org.is_anon:
                    result = {"id": obj.uuid, "name": obj.get_display(org), "type": "contact"}
                else:
                    result = {
                        "id": obj.uuid,
                        "name": obj.get_display(org),
                        "type": "contact",
                        "urn": obj.get_urn_display(),
                    }

        elif isinstance(obj, ContactURN):
            if version == "1":
                result = {
                    "id": "u-%d" % obj.id,
                    "text": obj.get_display(org),
                    "scheme": obj.scheme,
                    "extra": obj.contact.name or None,
                }
            else:
                result = {
                    "id": obj.identity,
                    "name": obj.get_display(org),
                    "contact": obj.contact.name or None,
                    "scheme": obj.scheme,
                    "type": "urn",
                }

        formatted.append(result)

    return formatted
