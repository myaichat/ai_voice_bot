
from ..config.Config import Config
from datetime import date
import logging

log=logging.getLogger()



class AppConfig(Config): 
    def __init__(self):
        
        self.gid=0
        
        self.all={}
    def init(self, **kwargs):
        Config.__init__(self,**kwargs)
        
    def get_access_token(self):
        #print('Getting access tokenfrom self.pages', self.page_id, self.pages)
        assert self.page_id in self.pages, f'Page {self.page_id} not found in self.pages'
        assert 'page_token' in self.pages[self.page_id], f'"page_token" is not set for  {self.page_id}'
        return self.pages[self.page_id].page_token

    def get_page_access_token(self, user_id, page_id):
        #print('Getting access tokenfrom self.pages', self.page_id, self.pages)
        assert user_id in self.page_tokens
        assert page_id in self.page_tokens[user_id], f'Page {page_id} not found in self.page_tokens[{user_id}]'
        assert 'page_token' in self.page_tokens[user_id][page_id], f'"page_token" is not set for {user_id}/{page_id}'
        return self.page_tokens[user_id][page_id].page_token    
    def update_stats(self, metrics):
        print('Updating stats:', metrics)
        #followers_count: 457912
        #fan_count: 446560
        #id: 105420925572228
        followers_count = metrics.get('followers_count', 'N/A')
        fan_count = metrics.get('fan_count', 'N/A')
        
        
        #dc= apc.followers_count
        #print(22, self.followers_count, type( self.followers_count))
        self.load_followers()
        followers=self.followers_count[self.user][self.page_id][self.dt]
        prev_followers= followers['followers']
        if prev_followers:
            followers['followers'] = followers_count
            followers['increment'] = increment = followers_count - prev_followers
            followers['delta'] += increment
            #print(333, self.followers_count, type( self.followers_count))
        else:   
            followers['followers'] = followers_count
            followers['increment'] = 0
            followers['delta'] = 0
    def set_input_files(self, input_files):
        self.input_files={k:v for k,v in enumerate(input_files)}
    def get_today_stats(self):
        dt = date.today().strftime("%Y-%m-%d")
        return self.followers_count[dt]
    def load_followers(self):
      
        if not self.followers_count :
            print(999,self.followers_count)
            self.followers_count[self.user]={}
            for page_id in self.pages: 
                print(222,page_id)
                self.followers_count[self.user][page_id]={self.dt:{'followers':0, 'delta':0, 'increment':0}}
                    
        else:
            print(555,self.followers_count)
            for page_id in self.pages: 
                print(111,page_id)
                if not  self.followers_count[self.user].get(page_id):
                    self.followers_count[self.user][self.page_id]={self.dt:{'followers':0, 'delta':0, 'increment':0}}



        
        
            