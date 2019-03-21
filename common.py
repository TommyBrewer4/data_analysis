from datetime import datetime
from constants import *
from pytz import timezone
import platform
import pytz
import re

def json_drilldown(source_json,drilldown_array):
    i = 0
    for child_item in check_array(drilldown_array):
        try:
            source_json = source_json[child_item]
        except:
            for item in source_json:
                e = regex_inbetween_brackets(str(item.keys()))
                if e == child_item:
                    return item
                else:
                    i += 1
    return source_json

def check_date(date_value):
    if isinstance(date_value,datetime):
        return date_value
    else:
        try:
            return datetime.utcfromtimestamp(date_value)
        except:
            return 'time conversion failed'

def check_array(array,delimiter=','):
    if not isinstance(array,list) :
        if delimiter not in array:
            return [array]
        else:
            return array.split(delimiter)
    else:
        return array

def localize_UTC_time(utc_time,time_zone=None,date_format=DT_FMT):
    converted_utc = check_date(utc_time)
    if time_zone is not None:
        try:
            conversion_time_zone= timezone(str(time_zone))
            local_date = converted_utc.replace(tzinfo=pytz.utc).astimezone(conversion_time_zone)
            return local_date.strftime(date_format)
        except:
            return converted_utc.strftime(date_format)
    else:
        return converted_utc.strftime(date_format)

def format_date(raw_time,date_format=DT_FMT):
    date_value = check_date(raw_time)
    return date_value.strftime(date_format)

def regex_inbetween_brackets(source_str,option=REGEX_RETURN):
    if option == REGEX_RETURN:
        re_pattern = r'\[(.*?)\]'
        bracketed_value = re.search(re_pattern,source_str).group(0)
        for b in ['[',']',"\'"]:
            bracketed_value = bracketed_value.replace(b,'')
        return bracketed_value
    elif option == REGEX_REPLACE:
        re_pattern = r'\[.*?\]'
        return_str = re.sub(re_pattern,'',source_str)
        return return_str

def bracketed_value_to_key_value_pair(source_str,delimiter = ':'):
    bracketed_value = regex_inbetween_brackets(source_str)
    if delimiter in source_str:
        key = bracketed_value.split(':')[0].replace('[','')
        value = bracketed_value.split(':')[1].replace(']','')
        return [key,value]
    else:
        bracketed_value = bracketed_value.replace('[','')
        return [0,bracketed_value.replace(']','')]

def wrap_string(string_to_wrap=None,wrap_type=None,type_override=False):
    if isinstance(string_to_wrap,str) or type_override==True:
        first_character = 0
        last_character = 1
        wrap_types = {
        DQUOTES:("\"","\""),
        SQUOTES:("\'","\'"),
        CBRACKETS:("{","}"),
        SBRACKETS:("[","]"),
        XML:("<","/>"),
        PARAENTHESES:("(",")")
        }
        string_to_wrap = str(string_to_wrap)
        if string_to_wrap[:1] != wrap_types[wrap_type][first_character] and string_to_wrap[1:] != wrap_types[wrap_type][last_character]:
            return wrap_types[wrap_type][first_character] + string_to_wrap + wrap_types[wrap_type][last_character]
    else:          
        return string_to_wrap

def system_value(system_options):
    system = str(platform.system()).lower()
    system_enum = {
        'windows':0,
        'linux':1,
        'darwin':2
    }
    return system_options[system_enum[system]]

def optional_delimiter_split(source_str,delimiter_array,split_source_str=True,limit=-1):
    for delimiter in delimiter_array:
        if delimiter in str(source_str):
            found_delimiter = delimiter
            if split_source_str == True:
                return str(source_str).split(found_delimiter,limit)
            else:
                return found_delimiter
    return [0,0]

def multi_string_search(source_str,search_item):
    if isinstance(search_item,list) or isinstance(search_item,tuple):
        for i in search_item:
        	if i in source_str:
        		return i
        return ''
    elif isinstance(search_item,dict):
        for k,v in search_item.items():
          if k in source_str:
            return v
        return ''

"""
FILE AND PATH INSPECTION FUNCTIONS
"""
def regex_file_path(source_str,return_value=FIRST_ITEM):
    path_str = re.search(REGEX_FILE_PATH,source_str).group(0)
    file_name_str = re.sub(REGEX_FILE_PATH,'',source_str)
    values = [path_str,file_name_str]
    return values[return_value]

def regex_file_ext(source_str,return_value=FOR_VAL):
    ext = re.search(REGEX_FILE_EXT,source_str)
    if return_value == FOR_BOOL:
        if len(ext.group(0)) != 0:
            return True
        return False
    elif return_value == FOR_VAL:
        return ext.group(0)

def has_path(source_str):
    if '\\' in source_str:
        return True
    return False

def has_file(source_str):
    if regex_file_ext(source_str,FOR_BOOL):
        return True
    return False
    