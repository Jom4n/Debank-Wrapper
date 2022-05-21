import numpy as np
import pandas as pd

from IPython.display import display

import requests, json

class debank:
    
    IDs = ['eth',  
     'bsc',
     'xdai',
     'matic',
     'ftm',
     'okt',
     'heco',
     'avax',
     'op',
     'arb',
     'celo',
     'movr',
     'cro',
     'boba',
     'metis',
     'btt',
     'aurora',
     'mobm',
     'sbch',
     'fuse',
     'hmy',
     'klay',
     'astar',
     'sdn',
     'palm']
    
    group = ["USDC"]
    wrapped = ["ETH","FTM"]     

    def get_wallet(self,address):
        frame = {'symbol':[],'chain':[],'amount':[],'amount_usd':[]}
        self.data = pd.DataFrame(data=frame)        
        for i in self.IDs:
            #Coins
            url = requests.get("https://openapi.debank.com/v1/user/token_list?id="+address+"&chain_id="+i+"&is_all=false")
            full_coins = pd.DataFrame(data = json.loads(url.text))
            if not full_coins.empty:
                full_coins["amount_usd"] = full_coins["amount"]*full_coins["price"]
                coins = full_coins.loc[:,["symbol","chain","amount","amount_usd"]]        
                self.data = pd.concat([self.data,coins], ignore_index=True)
            #Protocols
            url = requests.get("https://openapi.debank.com/v1/user/complex_protocol_list?id="+address+"&chain_id="+i)
            full_protocols = pd.DataFrame(data=json.loads(url.text))
            if not full_protocols.empty:
                for j in full_protocols["portfolio_item_list"]:                
                    values = self.get_protocolvalues(j)
                    self.data = pd.concat([self.data,values], ignore_index=True)    
        return self.do_clean()


    def do_clean(self):
        for i in self.group:
            self.data = self.data.replace(to_replace=r'.*(?i)'+i+'.*',value=i,regex=True)
        for j in self.wrapped:
            self.data = self.data.replace(to_replace=r'.*(?i)'+j,value=j,regex=True)

        self.data['total_amount'] = self.data.groupby(['symbol'])['amount'].transform('sum')
        self.data['total_amount_usd'] = self.data.groupby(['symbol'])['amount_usd'].transform('sum')
        self.data['weight'] = self.data["total_amount_usd"] / self.data['total_amount_usd'].sum()
        self.data = self.data.drop_duplicates(subset=['symbol'])
        self.data = self.data.drop(columns=["amount","amount_usd"])
        self.data = self.data.drop_duplicates(subset=['symbol', 'chain']).reset_index(drop=True)
        return self.data
    
    def get_protocolvalues(self,full_protocol):
        frame = {'symbol':[],'chain':[],'amount':[], 'amount_usd':[]}
        df = pd.DataFrame(data=frame)        
        #Currently not accounting for rewards      
        if full_protocol[0]["name"]=="Farming" or full_protocol[0]["name"]=="Yield" or full_protocol[0]["name"]=="Liquidity Pool":        
            for i in full_protocol[0]["detail"]["supply_token_list"]:
                i["amount_usd"] = i["price"]*i["amount"]  
                i_df = pd.DataFrame.from_dict([i],orient='columns')                
                df = pd.concat([df,i_df.loc[:,["symbol","chain","amount","amount_usd"]]], ignore_index=True)       
        elif full_protocol[0]["name"]=="Options Buyer":            
            i_df = pd.DataFrame.from_dict([full_protocol[0]["detail"]],orient='columns')            
            i_df_underlying = pd.DataFrame.from_dict([i_df.underlying_token[0]],orient='columns')
            i_df_strike = pd.DataFrame.from_dict([i_df.strike_token[0]],orient='columns')            
            
            df.symbol = i_df_underlying.name[0] +"_"+ i_df.type +"_"+str(int(i_df_strike.amount[0] / i_df_underlying.amount[0]))
            df.chain = i_df_underlying.chain
            df.amount = i_df_underlying.amount            
            df.amount_usd = max(0,i_df_underlying.price[0] - (i_df_strike.amount[0] / i_df_underlying.amount[0]))
        elif full_protocol[0]["name"]=="Lending":
            #supply        
            for i in full_protocol[0]["detail"]["supply_token_list"]:            
                i["amount_usd"]=i["price"]*i["amount"]
                i_df = pd.DataFrame.from_dict([i],orient='columns')                
                df = pd.concat([df,i_df.loc[:,["symbol","chain","amount","amount_usd"]]], ignore_index=True)            
            #borrow
            for i in full_protocol[0]["detail"]["borrow_token_list"]:
                i["amount"]=i["amount"]*(-1)
                i["amount_usd"]=i["price"]*i["amount"]
                i_df = pd.DataFrame.from_dict([i],orient='columns')
                df = pd.concat([df,i_df.loc[:,["symbol","chain","amount","amount_usd"]]], ignore_index=True)               
        return df

dbank = debank()

dbank.get_wallet("0xe3f8c6416621ef2e8cf1828ab2c0e1ee5522d4e2")

display(dbank.data)