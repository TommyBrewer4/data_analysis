from constants import *
from common import *
from datetime import datetime
import sqlite3
import json
import os
import praw
import common as c
from praw import Reddit
import types
import pyodbc
import pandas as pd
import requests


json_filename = 'config.json'

class configuration_manager(object):

    _firstItem = 'connection_arguments'
    
    def __init__(self):
        pass

    def read_json_file(self,json_file,file_path=None):
        if file_path == None:
            file_path = os.path.dirname(os.path.abspath(__file__))
        file_name = os.path.join(file_path,json_file)
        raw_json = open(file_name,'r')
        return raw_json

    def config_arguments(self,json_file, json_item):
        wrkdir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(wrkdir,json_file)
        with open(filename,'r') as bot_info:
            arg_array = check_array(json_item)
            connection_args = check_array(json_item)[len(arg_array)-1]
            raw_json = json_drilldown(json.load(bot_info),json_item)
            return raw_json[connection_args][0]
            bot_info.close()
            
class db_connector(configuration_manager): 

    def __init__(self,configuration_json_file, configuation_json_item = SERVER):
        self.configuation_json_item = configuation_json_item
        self.db_connection_string = self.build_db_string(configuration_json_file)
        self.db_connection = None
        self.cursor = None
        self.database = None
        self.set_db_connection()

    def build_db_string(self,connection_string_json_file):
        passed_arguments = []
        db_json_item = ','.join([self._firstItem,self.configuation_json_item])
        connection_string_list = self.config_arguments(connection_string_json_file,db_json_item)
        for p,a in connection_string_list.items():
            if a is not None:
                if p.lower() == 'driver':
                    a_wrapped = wrap_string(a,CBRACKETS)
                    new_arg = f'{p}={a_wrapped};'
                elif p.lower() == 'database':
                    self.database = a
                    new_arg = f'{p}={a};'
                else:
                    new_arg = f'{p}={a};'
                passed_arguments.append(new_arg)
        passed_arguments = [arg.replace(new_arg,new_arg.replace(';','')) for arg in passed_arguments]
        return ''.join(passed_arguments)

    def set_db_connection(self,connection_type='odbc'):
        if connection_type =='odbc':
            try:
                self.db_connection = pyodbc.connect(self.db_connection_string)
                self.cursor = self.db_connection.cursor()
            except:
                print('db Connection Failed')
        elif connection_type == 'sqlite':
            try:
                self.db_connection = sqlite3.connect(self.SQLite_DB)
                self.cursor = self.db_connection.cursor()
            except:
                print('SQLite Connection Failed')

    def execute_stored_procedure(self,stored_procedure, args, sql_type = DML):
        params = []
        arg_array = []
        for arg in args:
            params.append('?')
            if isinstance(args,dict):
                a = args[arg]
            else:
                a = arg
            arg_array.append(a)
        sp = wrap_string('dbo',SBRACKETS) + '.' + wrap_string(stored_procedure,SBRACKETS) + ' ' + ', '.join(params)
        if sql_type in (DML,DDL):
            self.execute(sp,arg_array)
        elif sql_type == DQL:
            return self.dataframe(sp,arg_array)

    def union_check(self,source_str):
        if isinstance(source_str,str):
            if 'union' in source_str.lower():
                source_str = source_str.replace('union','union;')
            return source_str

        elif isinstance(source_str,list):
            source_str_list = []
            for i in source_str:
                if isinstance(i,str):
                    if 'union' in i.lower():
                        i = i.replace('union','union;')
                source_str_list.append(i)
            return source_str_list
        else:
            return source_str

    def execute(self,qry,params=None):
        params_tuple = tuple(params)
        self.cursor.execute(qry,params_tuple)
    
    def commit_transaction(self):
        self.cursor.commit()
    
    def dataframe(self,qry,args=None):
        params_tuple = tuple(args)
        return pd.read_sql(qry,self.db_connection,params=params_tuple)
    
    def max_date(self,tbl_name,col_name):
        sp = 'usp_SELECT_max_value_by_tbl'
        args = (self.union_check(tbl_name),self.union_check(col_name))
        df = self.execute_stored_procedure(sp,args,DQL)
        return df.iloc[0,0]
    
    def get_table_by_date_range(self,tbl_name,col_name,start_date,end_date=None):
        sp = 'usp_SELECT_all_by_date_range'
        if end_date != None:
            end_date = str(end_date)
        args = (self.union_check(tbl_name),self.union_check(col_name),self.union_check(str(start_date)),self.union_check(end_date))
        df = self.execute_stored_procedure(sp,args,DQL)
        return df

class reddit_bot(configuration_manager,Reddit):

    _COMMENT_MAX_LEN = 10000

    def __init__(self,configuration_json_file, configuation_json_item):
        self.bot = None
        self.bot_call = None
        self.bot_subreddit = None
        self.bot_database = None
        self.bot_name = None
        self.bot_objects = []
        self.configuation_json_item = configuation_json_item
        self.initialize_bot(configuration_json_file)
        self.subscribed_subreddits = self.get_subscribed_subreddits()

    def initialize_bot(self,PRAW_bot_json_file):
        PRAW_json_item = ','.join([self._firstItem,self.configuation_json_item])
        connection_string_list = self.config_arguments(PRAW_bot_json_file,PRAW_json_item)
        self.bot = Reddit(
        user_agent=connection_string_list['user_agent'],
        client_id=connection_string_list['client_id'],
        client_secret=connection_string_list['client_secret'],
        username=connection_string_list['username'],
        password=connection_string_list['password']
        )
        self.bot_name=connection_string_list['username']
        self.bot_call=connection_string_list['bot_call']
        self.bot_subreddit=self.bot.subreddit(connection_string_list['bot_subreddit'])
        self.bot_database=connection_string_list['source_database']
    
    def get_subscribed_subreddits(self):
        subreddit_list = []
        for subreddit in list(self.bot.user.subreddits(limit=None)):
            subreddit_list.append(subreddit.display_name)
        return '+'.join(subreddit_list)
    
    def get_reddit_obj_type(self,object_id):
        try:
            return str(self.bot.redditor(object_id[0:3]))
        except:
            print('didn\'t work')
    
    def get_reddit_obj(self,object_id):
        try:
            return self.bot.redditor(object_id)
        except:
            print('didn\'t work')

    def reddit_object_redditor_reply(self,object_id,source_redditor=None,return_comment_id=False):
        if source_redditor is None:
            source_redditor = self.bot_name
        if self.get_reddit_obj_type(object_id)==REDDIT_COMMENT:
            object_id=object_id.replace(REDDIT_COMMENT,'')
            calling_object = self.bot.comment(object_id)
            calling_object.comment_sort = 'new'
        elif self.get_reddit_obj_type(object_id)==REDDIT_LINK:
            object_id=object_id.replace(REDDIT_LINK,'')
            calling_object = self.bot.submission(object_id)
            calling_object.comment_sort = 'new'
            calling_object.reply_sort = 'new'
        try:
            replies = calling_object.comments
            for r in replies:
                if r.author == source_redditor:
                    if return_comment_id:
                        return r
                    else:
                        return True
            return False
        except:
            return False

class basic_api_bot(configuration_manager):

    def __init__(self,configuration_json_file, configuation_json_item):
        self.json_drilldown_list=','.join([self._firstItem,configuation_json_item])
        self.config_arguments_list=self.config_arguments(configuration_json_file, self.json_drilldown_list)

    def build_request(self,macro_id=0):
        args = []
        macro = self.config_arguments_list['macros'][macro_id]
        macro_prefix = '/'.join([self.config_arguments_list['api_endpoint_base'],macro['prefix']])
        print(macro_prefix)
        for k,v in macro['parameters'][0].items():
            args.append('='.join([k,str(v)]))
        arg_str = '&'.join(args)
        return '?'.join([macro_prefix,arg_str])
    
    def call_api(self,macro_id=0):
        api_request = self.build_request(macro_id)
        api_command = self.config_arguments_list['macros'][macro_id]['command']
        return requests.request(api_command,api_request)

    def response_json(self,macro_id=0):
        r = self.call_api(macro_id)
        t = r.text
        return json.loads(t)

class super_reddit_bot(db_connector,reddit_bot):

    def __init__(self,configuration_json_file,db_json_item=SERVER,json_item = None):
        db_connector.__init__(self,configuration_json_file,db_json_item)
        reddit_bot.__init__(self,configuration_json_file,json_item)

class super_api_bot(db_connector,basic_api_bot):

    def __init__(self,configuration_json_file,db_json_item=SERVER,json_item = None):
        db_connector.__init__(self,configuration_json_file,db_json_item)
        basic_api_bot.__init__(self,configuration_json_file,json_item)

if __name__ == "__main__":
    pass