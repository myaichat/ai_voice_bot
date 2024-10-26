import  os, sys, json, codecs
import re
from pubsub import pub
from pprint import pprint as pp
from ..common import PropertyDefaultDict
from pubsub import pub
from datetime import datetime
from datetime import date
from os.path import join, basename, isdir, isfile, splitext   



e=sys.exit




class MutableAttribute:
    def __init__(self):
        self.parent = None
        self.name = None
        self.real_name = None

    def __set_name__(self, owner, name):
        self.name = f"_{name}"
        self.real_name = name

    def __get__(self, obj, objtype=None):
        if self.parent is None:
            self.parent = obj
        return getattr(obj, self.name, None)

    def __set__(self, obj, value):
        if self.parent is None:
            self.parent = obj
        processed_value = self.process(value)
        setattr(obj, self.name, processed_value)
        self.notify_change(processed_value)

    def process(self, value):
        #print('77711 Processing:', self.real_name, value)
        new_value = {}
        for key, val in value.items():
            #print(222, type(val))
            if not isinstance(val, (str, dict,int, float, bool, type(None))):
                #print('\t 999 Processing:', self.real_name, str(val))
                new_value[key] =str(val)
            else:
                new_value[key] = val
        if new_value:
            #pp(value)
            value= new_value        
        if hasattr(self.parent, 'process'):

            return self.parent.process(self.real_name, value)

        return value

    def notify_change(self, value):
        pub.sendMessage(f'{self.real_name}_changed', value=value)
        #print('888 Notifying:', self.real_name, value)

        
        #pub.sendMessage('{self.real_name}_changed', name=self.real_name, value=value)


class NotifyingList(list):
    def __init__(self, *args, parent=None, key=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.key = key
        self._processing = False
        for i, v in enumerate(self):
            if isinstance(v, dict):
                self[i] = NotifyingDict(v, parent=self, key=i)
            elif isinstance(v, list):
                self[i] = NotifyingList(v, parent=self, key=i)

    def __setitem__(self, index, value):
        if isinstance(value, dict):
            value = NotifyingDict(value, parent=self, key=index)
        elif isinstance(value, list):
            value = NotifyingList(value, parent=self, key=index)
        super().__setitem__(index, value)
        self.propagate_change()

    def append(self, value):
        if isinstance(value, dict):
            value = NotifyingDict(value, parent=self, key=len(self))
        elif isinstance(value, list):
            value = NotifyingList(value, parent=self, key=len(self))
        super().append(value)
        self.propagate_change()

    def extend(self, iterable):
        for v in iterable:
            if isinstance(v, dict):
                v = NotifyingDict(v, parent=self, key=len(self))
            elif isinstance(v, list):
                v = NotifyingList(v, parent=self, key=len(self))
            super().append(v)
        self.propagate_change()

    def propagate_change(self):
        if self.parent and not self._processing:
            if isinstance(self.parent, NotifyingDict) or isinstance(self.parent, NotifyingList):
                self.parent.propagate_change()
            elif isinstance(self.parent, MutableDictAttribute):
                self.parent.child_changed()



class NotifyingDict(dict):
    def __init__(self, *args, parent=None, key=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.key = key
        self._processing = False

        # Recursively wrap nested dictionaries and lists
        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = NotifyingDict(v, parent=self, key=k)
            elif isinstance(v, list):
                self[k] = NotifyingList(v, parent=self, key=k)

    def __setitem__(self, key, value):
        # Automatically wrap dictionaries and lists in NotifyingDict or NotifyingList
        if isinstance(value, dict) and not isinstance(value, NotifyingDict):
            value = NotifyingDict(value, parent=self, key=key)
        elif isinstance(value, list) and not isinstance(value, NotifyingList):
            value = NotifyingList(value, parent=self, key=key)
        
        super().__setitem__(key, value)
        self.propagate_change()

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'NotifyingDict' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        if name in ['parent', 'key', '_processing']:
            super().__setattr__(name, value)
        else:
            self[name] = value

    def propagate_change(self):
        if self.parent and not self._processing:
            if isinstance(self.parent, NotifyingDict) or isinstance(self.parent, NotifyingList):
                self.parent.propagate_change()
            elif isinstance(self.parent, MutableDictAttribute):
                self.parent.child_changed()


class MutableDictAttribute:
    def __init__(self):
        self.parent = None
        self.name = None
        self.real_name = None

    def __set_name__(self, owner, name):
        self.name = f"_{name}"
        self.real_name = name

    def __get__(self, obj, objtype=None):
        if self.parent is None:
            self.parent = obj
        return getattr(obj, self.name, None)

    def __set__(self, obj, value):
        if self.parent is None:
            self.parent = obj
        processed_value = self.process(value)
        if isinstance(processed_value, dict):
            processed_value = NotifyingDict(processed_value, parent=self, key=self.real_name)
        elif isinstance(processed_value, list):
            processed_value = NotifyingList(processed_value, parent=self, key=self.real_name)
        setattr(obj, self.name, processed_value)

    def process(self, value):
        # Hook for any processing before setting the value
        if hasattr(self.parent, 'process'):
            return self.parent.process(self.real_name, value)
        return value

    def child_changed(self):
        if hasattr(self.parent, 'process'):
            current_value = getattr(self.parent, self.name, None)
            if current_value is not None:
                current_value._processing = True
                processed = self.parent.process(self.real_name, current_value)
                current_value._processing = False
                setattr(self.parent, self.name, processed)

         
        #pub.sendMessage(f'{attr_name}_changed', value=value)



class DictWithAttributes:
    page_info = MutableDictAttribute()

    def __init__(self):
        dt = date.today().strftime("%Y-%m-%d")
        self.page_info[dt] = {'followers': 0, 'delta': 0}

    def process(self, attr_name, value):
        print(f'-----parent Processing: {attr_name} {value} {type(value)}')
        if  isinstance(value, dict):
            self.process_dict(value)
        return value

    def process_dict(self, d):
        for key, value in d.items():
            if isinstance(value, str):
                d[key] = value.strip()
            elif isinstance(value, dict):
                self.process_dict(value)




class MutableList(list):
    def __init__(self, parent_obj, descriptor):
        super().__init__(getattr(parent_obj, descriptor.name))
        self.parent_obj = parent_obj
        self.descriptor = descriptor

    def add_item(self, item):
        if not isinstance(item, dict):
            raise ValueError("Item must be a dictionary")
        self.append(item)
        self.descriptor.__set__(self.parent_obj, self)

    def remove_item(self, index):
        if 0 <= index < len(self):
            del self[index]
            self.descriptor.__set__(self.parent_obj, self)
        else:
            raise IndexError("Index out of range")

    def update_item(self, index, new_item):
        if not isinstance(new_item, dict):
            raise ValueError("New item must be a dictionary")
        if 0 <= index < len(self):
            self[index] = new_item
            self.descriptor.__set__(self.parent_obj, self)
        else:
            raise IndexError("Index out of range")
        
class MutableListAttribute:
    def __init__(self):
        self.parent = None
        self.name = None
        self.real_name = None

    def __set_name__(self, owner, name):
        self.name = f"_{name}"
        self.real_name = name

    def __get__(self, obj, objtype=None):
        if self.parent is None:
            self.parent = obj
        if not hasattr(obj, self.name):
            setattr(obj, self.name, [])
        return MutableList(obj, self)

    def __set__(self, obj, value):
        if not isinstance(value, list):
            raise ValueError("Value must be a list")
        if not all(isinstance(item, dict) for item in value):
            raise ValueError("All items in the list must be dictionaries")
        if self.parent is None:
            self.parent = obj
        processed_value = self.process(value)
        setattr(obj, self.name, processed_value)
        self.notify_change(processed_value)

    def process(self, value):
        #print(f'Processing: {self.real_name}', value)
        if hasattr(self.parent, 'process'):
            return self.parent.process(self.real_name, value)
        return value

    def notify_change(self, value):
        pub.sendMessage(f'{self.real_name}_changed', value=value)


class Config(): 

    app_config  = MutableDictAttribute()
    app_log  = MutableDictAttribute()
    ppl_log  = MutableDictAttribute()
    chat=MutableAttribute()
    def __init__(self, **kwargs):
        self.cfg={}
        self.mta=set()
        self.ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.home=None
        self.data=None
        self.vars=None
        self.title=None
        self.llm_api=None
        self.mock_file   = None
        self.mock_data   = None
        self.py_pipeline_name=None
        self.yaml_pprompt_config=None
        #self.page_tokens_fn='.page_tokens.json'
        self.dump_file={}
       
        
        self.app_config=self.get_attr('app_config', {}, join('config', 'app_config.json')) 
        self.log_dir='log'
        if not isdir(self.log_dir):
            os.makedirs(self.log_dir)
        self.app_log=self.get_attr('app_log', {}, join(self.log_dir, f'app_log_{self.ts}.json')) 
        self.app_log['ts']=self.ts
        self.app_log['log']=[]
    def load_mock(self, mock_file): 
        self.mock_file=mock_file
        if isfile(mock_file):
            with open(mock_file, 'r') as f:
                data= json.load(f)
                self.mock_data = data['ppl_log']["agent_response"]
        else:
            self.mock_data = {}
        assert self.mock_data, ('Mock file not found:', mock_file)
    def set_pipeline_log(self,py_pipeline_name, yaml_pprompt_config):
        print('Setting pipeline log:', py_pipeline_name, yaml_pprompt_config)
        self.py_pipeline_name=py_pipeline_name
        self.yaml_pprompt_config=yaml_pprompt_config
        bn=basename(yaml_pprompt_config)
        ppl_log_dir=join(self.log_dir, py_pipeline_name,)
        if not isdir(ppl_log_dir):
            os.makedirs(ppl_log_dir)
        name, ext = splitext(bn)
        fn=f'{py_pipeline_name}_{name}_{self.ts}.json'
        self.yaml_pprompt_fn=fn
        self.ppl_log=self.get_attr('ppl_log', {}, join(ppl_log_dir, fn)) 
        self.ppl_log['ts']=self.ts
        self.ppl_log['agent_response']=[]
        self.log(f'Starting pipeline log: {ppl_log_dir}\\{fn}')

      
    def plog(self,agent_name, msg):
        pub.sendMessage('ppllog',agent=agent_name, msg=msg)
        self.ppl_log['agent_response'].append({'ts':datetime.now().strftime("%Y-%m-%d %H:%M:%S"),'agent_name':agent_name, 'py_pipeline_name':self.py_pipeline_name,
                                       'yaml_pprompt_config':self.yaml_pprompt_config, 'chat':self.chat,'msg':msg})        
    def log(self, msg, type='info'):
        pub.sendMessage('applog', msg=msg, type=type)
        self.app_log['log'].append({'ts':datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'msg':msg, 'type':type})
    def get_reel_descr(self):
        print   ('-----Getting reel descr:', self.user, self.page_id)
        return self.all_reel_descr[self.user].get(self.page_id,'No description')
    def set_reel_descr(self, descr):
        print('Setting reel descr:', descr) 
        self.all_reel_descr[self.user][self.page_id] = descr
            
    def get_user_token(self):
        user_token=self.user_tokens[self.user]
        if user_token:
            return user_token   
        else:
            return ''
    def set_user_token(self, user_token):
        self.user_token = user_token
        self.user_tokens[self.user] = user_token
        
    def increment_uploads(self):

        self.num_of_uploads[self.user][self.page_id][self.dt]['uploads'] += 1
        
    def get_attr(self, attr, default=None, dump_file='.config.json'): 
        if attr not in self.dump_file:
            self.dump_file[attr]=dump_file
        config_fn=self.dump_file[attr]
        self.mta.add(attr)
        print('-------------------config_fn: ' , attr, config_fn)
        if config_fn not in self.cfg:
            self.cfg[config_fn]={}
        cfg=self.cfg[config_fn]

        if not cfg:
            if isfile(config_fn):
                try:
                    print(f"Reading config file {config_fn}")
                    with open(config_fn, 'r') as f:
                        content = f.read().strip()
                        #pp(content)
                        if content:
                            cfg_dump = json.loads(content)
                            #pp(cfg_dump)
                            self.cfg[config_fn]=cfg=cfg_dump
                        else:
                            print(f"Warning: {config_fn} is empty.")
                except json.JSONDecodeError as e:
                    print(f"Error reading config file {config_fn}: {e}")
                    #print("Initializing with an empty PropertyDefaultDict.")
                except Exception as e:
                    print(f"Unexpected error reading config file {config_fn}: {e}")
                    #print("Initializing with an empty PropertyDefaultDict.")
            else:
                print(f"Warning: connfig file {config_fn} does not exist.")
            
                
        if cfg:
            print(8888, cfg)
            #print (attr.name)
            value=cfg.get(attr, default)
            print('Getting:', attr, type(value))   
           
            
            return value
        self.cfg[config_fn]=cfg
        return default
    def set_attr(self, attr, value):
        #print('Setting:', attr, value, type(value))
        assert attr in self.dump_file, f'set_attr: No dump file specified for attr "{attr}"'
        dump_file = self.dump_file[attr]   
        assert dump_file, f'set_attr: dump_file is not set  for attr "{attr}"'     
        cfg=self.cfg[dump_file]
        #pp(self.cfg)
        assert cfg is not None, dump_file
        cfg[attr]=value

        assert dump_file, 'set_attr: No dump file specified'
        #print('Dumping ******************************:', attr, dump_file)    
        with open(dump_file, 'w') as f:
            #json.dumps(example_dict, cls=CustomEncoder)
            json.dump(cfg, f, indent=2)
        
        
    def process(self, attr_name, value):
        #print   ('-----Processing:', attr_name, value)
        if attr_name in self.mta: # ['page_id', 'reel_id', 'user_token','followers_count','uploaded_cnt']:
            #print(f"Parent processing: {attr_name} = {value}")
            if value:
                self.set_attr(attr_name, value)
            return value
        
        return value  
    def _process_dict(self, attr_name, value):
        #print   ('-----Processing dict:', attr_name, value)
        if attr_name in ['followers_count']:
            print(f"Parent dict processing: {attr_name} = {value}")
            if value:
                self.set_attr(attr_name, value)
            return str(value).strip()
        
        
        return value 
    

    def _process(self, attr_name, value):
        #print(f'-----parent Processing: {attr_name} {value} {type(value)}')
        if attr_name in self.mta:        
            if  isinstance(value, dict):
                self.process_dict(value)
            return value

    def _process_dict(self, d):
        for key, value in d.items():
            if isinstance(value, str):
                d[key] = value.strip()
            elif isinstance(value, dict):
                self.process_dict(value)

    def _load_page_tokens(self):
        if not self.pages:
            self.pages = self.init_pages()
        return self.pages              
    def _dump_page_tokens(self):
        with open(self.page_tokens_fn, 'w') as f:
            #pp(self.pages.to_dict())
            json.dump(self.pages, f, indent=2)
    def _init_pages(self):
        self.pages = PropertyDefaultDict()
        if isfile(self.page_tokens_fn):
            try:
                print(f"Reading page tokens from {self.page_tokens_fn}")
                with open(self.page_tokens_fn, 'r') as f:
                    content = f.read().strip()
                    if content:
                        js = json.loads(content)
                        self.pages = PropertyDefaultDict(js)
                    else:
                        print(f"Warning: {self.page_tokens_fn} is empty.")
            except json.JSONDecodeError as e:
                print(f"Error reading {self.page_tokens_fn}: {e}")
                print("Initializing with an empty PropertyDefaultDict.")
            except Exception as e:
                print(f"Unexpected error reading {self.page_tokens_fn}: {e}")
                print("Initializing with an empty PropertyDefaultDict.")
        else:
            print(f"Warning: {self.page_tokens_fn} does not exist.")

        return self.pages
