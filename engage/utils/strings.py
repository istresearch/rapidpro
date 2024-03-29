import re
from typing import Union

def _mg_for_cap_words( aMatchGroup: re.Match[str] ) -> str:
    """
    process regular expression match groups for word upper-casing problem\n
    @see https://stackoverflow.com/a/1549983\n
    :param aMatchGroup: re match group
    :return: Return a string with the first letter in word capitalized.
    """
    return aMatchGroup.group(1) + aMatchGroup.group(2).upper()
#enddef _mg_for_cap_words

def cap_words( aString: str ):
    """
    Capitalize words in a string, but leave all other chars alone.\n
    e.g. input: "they're bill's friends from the UK"\n
    output: "They're Bill's Friends From The UK"\n
    @see https://stackoverflow.com/a/1549983\n
    :param aString: the string to work on
    :return: Returns the string with words capitalized.
    """
    return re.sub("(^|\s)(\S)", _mg_for_cap_words, aString)
#enddef cap_words

def sanitize_text( aText: str) -> str:
    """
    Ensure HTML in messages do not bork our display.
    :param aText: the text of a message to process.
    :return: the processed text.
    """
    #from engage.utils import var_dump
    #var_dump(aText)
    if aText and aText is not None:
        # convert non-breaking spaces to normal spaces, ads abuse long strings of them
        aText = aText.replace(u'\xa0', ' ').replace('&nbsp;', ' ')
        # remove 0-width non-joiner characters near spaces
        aText = aText.replace(' '+u"\u200C", ' ').replace(' &zwnj;', ' ')
    return aText
#enddef sanitize_text

def str2bool( v: Union[str, bool] ) -> bool:
    if v is not None:
        return str(v).lower() in ('true', '1', 'on', 'y', 'yes') if type(v) == str else bool(v)
    else:
        return False
#enddef str2bool

def is_empty( s ) -> bool:
    return not ( s and len(s) > 1 )
#enddef is_empty
