import datetime
import decimal
import json

import psycopg2.extensions
import psycopg2.extras
import pytz


def load(value):
    """
    Reads the passed in file to a JSON dictionary. The dictionary passed back will be ordered
    and decimal values will be represented as a decimal.Decimal.
    """
    return json.load(value, parse_float=decimal.Decimal)


def loads(value):
    """
    Converts the passed in string to a JSON dictionary. The dictionary passed back will be ordered
    and decimal values will be represented as a decimal.Decimal.
    """
    return json.loads(value, parse_float=decimal.Decimal)


def dumps(value, *args, **kwargs):
    """
    Converts the passed in dictionary into a JSON string. Any decimal.Decimal values will be
    turned into floats.
    """
    return json.dumps(value, *args, cls=TembaEncoder, **kwargs)


def encode_datetime(dt, micros=False):
    """
    Formats a datetime as a string for inclusion in JSON using the format 2018-08-31T12:13:30.123Z which is parseable
    on all modern browsers.
    :param dt: the datetime to format
    :param micros: whether to include microseconds
    """
    # always output as UTC / Z and always include milliseconds
    as_utc = dt.astimezone(pytz.utc)
    as_str = as_utc.strftime("%Y-%m-%dT%H:%M:%S.%f")
    return (as_str if micros else as_str[:-3]) + "Z"


class TembaEncoder(json.JSONEncoder):
    """
    Our own encoder for datetimes.. we always convert to UTC and always include milliseconds
    """

    def default(self, o):
        # See "Date Time String Format" in the ECMA-262 specification.
        if isinstance(o, datetime.datetime):
            return encode_datetime(o)
        elif isinstance(o, decimal.Decimal):
            return float(o)
        else:
            return super().default(o)


class TembaJsonAdapter(psycopg2.extras.Json):
    """
    Json adapter for psycopg2 that uses Temba specific `dumps` that serializes numbers as Decimal types
    """

    def dumps(self, o, **kwargs):
        return dumps(o, **kwargs)


# register UJsonAdapter for all dict Python types
psycopg2.extensions.register_adapter(dict, TembaJsonAdapter)
# register global json python encoders
psycopg2.extras.register_default_jsonb(loads=loads, globally=True)
psycopg2.extras.register_default_json(loads=loads, globally=True)
