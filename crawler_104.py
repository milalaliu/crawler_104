#!/usr/bin/env python
# coding: utf-8


import pandas as pd
import numpy as np

import  requests
import json
import re
from bs4 import BeautifulSoup
from selenium import webdriver


# # 合併相同key


def comb_dict(dictobj):
    
    newdict = {
        nm: [obdict.get(nm) for obdict in dictobj]
        for nm in set().union(*dictobj)
    }
    
    return newdict


# # 爬工作清單


def search_job():
    url = 'https://www.104.com.tw/jobs/search/?'
    headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
              }
    
    r = requests.get(url , JobSearchParams, headers = headers)
    soup = BeautifulSoup(r.text,"html.parser")
    List = soup.findAll('a',{'class':'js-job-link'})
    
    JobList = pd.DataFrame()
    
    for idx, val in enumerate(List):
            df = pd.DataFrame(
                data = [{
                    'JobTitle':val.get('title'),
                    'JobLink':'https://' + val.get('href').strip('//'),
                    'JobLinkId':re.search('[^\/][\w]+(?=\?)',val.get('href')).group()}],
                columns = ['JobTitle','JobLink','JobLinkId'])
            JobList = JobList.append(df, ignore_index=True)
            
    print('共有 ' + str(len(List)) + ' 筆資料')
    return JobList


# # 擷取完整工作內容


def get_job_detail(job_link_id):

        url = f'https://www.104.com.tw/job/ajax/content/{job_link_id}'

        headers = {'Referer': 'https://www.104.com.tw/job/{job_link_id}',
                   'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
        }
        
        resp = requests.get(url, headers = headers)
        
        target = json.loads(resp.text)['data']
        
        target['header'].pop('corpImageTop', None)
        
        point_key = ['skill','specialty','jobCategory']
        
        for key in target['condition']:
            if type(target['condition'][key])==str:
                continue
            
            elif not target['condition'][key]:
                target['condition'][key] = ','.join(target['condition'][key])
                
            else:
                if key in point_key:
                    tras_dict = comb_dict(target['condition'][key])
                    target['condition'][key] = ','.join(tras_dict['description'])
                elif key =='acceptRole':
                        tras_dict = comb_dict(target['condition'][key]['role'])
                        target['condition'][key] = ','.join(tras_dict['description'])
                elif key == 'language':
                        fnlstr = ''
                        for i in target['condition']['language']:
                            tmpstr = ':'.join(i.values())+';'
                            fnlstr += tmpstr
                            target['condition'][key] = fnlstr
        
        for key in target['jobDetail']:
            if type(target['jobDetail'][key]) in (str,int) or target['jobDetail'][key] is None:
                continue
                
            elif not target['jobDetail'][key]:
                target['jobDetail'][key] = ','.join(target['jobDetail'][key])           
                
            else:
                if key in point_key:
                    tras_dict = comb_dict(target['jobDetail'][key])
                    target['jobDetail'][key] = ','.join(tras_dict['description'])
        
        
        contentALL = {**target['header'], **target['contact'], **target['condition'], **target['welfare'],
                      **target['jobDetail'], **{'industry':target['industry']},
                      **{'employees':target['employees']}, **{'chinaCorp':target['chinaCorp']}}
        
        JobListDetail =pd.DataFrame.from_dict(contentALL,orient='index').T        
        
        return JobListDetail



JobSearchParams = {'ro':'1', # 限定全職的工作，如果不限定則輸入0
                  'keyword':'資料科學', # 想要查詢的關鍵字
                  'area':'6001006000,6001001000,6001002000', 
                  'isnew':'30', # 只要最近一個月有更新的過的職缺
                  'mode':'l',
                  'page':'1'} 


JobListDetailAll = pd.DataFrame()

for index, row in JobList.iterrows():
    JobListDetail = get_job_detail(row['JobLinkId'])
    JobListDetailAll = JobListDetailAll.append(JobListDetail, ignore_index=True)



JobListDetailAll.to_csv('JobListDetailAll.csv', index=False)

