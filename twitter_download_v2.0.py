import requests
import os
import json
import pprint
import time
import datetime
import urllib.error
import urllib.request
import tweepy
from urllib.parse import urlparse

config_open = open("config.json","r")
config_load = json.load(config_open)

#定数の設定
username=input("twitterID:")
makefolder = config_load["makefolder"]
bearer_token = config_load["token"]["bearer"]
CONSUMER_TOKEN  = config_load["token"]["consumer"]["token"]
CONSUMER_SECRET  = config_load["token"]["consumer"]["secret"]
ACCESS_TOKEN    = config_load["token"]["access"]["token"]
ACCESS_SECRET = config_load['token']['access']['secret']
url_before = "https://api.twitter.com/2/users/"
id_url="by/username/"
search_url="/tweets"
query_params = {'expansions': 'attachments.media_keys', 'media.fields': 'url,type', 'tweet.fields': 'entities', 'max_results': 100}

#videoのmediakeyを一次保存するリスト
videokey = []
video_tweetid = []

#認証用の関数
def bearer_oauth(r):
    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def create_api():
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)
    api = tweepy.API(auth)
    return api

def download_file(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file:
            data = web_file.read()
            with open(dst_path, mode='wb') as local_file:
                local_file.write(data)
    except urllib.error.URLError as e:
        print(e)

def download_file_to_dir(url, dst_dir):
    download_file(url, os.path.join(dst_dir, os.path.basename(url)))

def retrieve_video(id,dst_dir):
    api = create_api()
    try:
        try:
            status = api.get_status(id, tweet_mode='extended')
        except tweepy.errors.TooManyRequests:
            print("v1.1 too many requests")
            dt_now = datetime.datetime.now
            print(dt_now)
            time.sleep(900)
            status = api.get_status(id, tweet_mode='extended')
        finally:
            if hasattr(status, 'extended_entities'):
                for media in status.extended_entities.get('media', [{}]):
                    url = media['video_info']['variants'][0]['url']
                    p = urlparse(url)
                    link = p.scheme + "://" + p.netloc + p.path
                    download_file_to_dir(link,dst_dir)               
    except tweepy.errors as e:
        print(e)
            
#検索エンドポイントに接続してJSONを取得する関数
def connect_to_endpoint(list,idlist,name, params):
    idsearch = url_before + id_url + name
    status = requests.get(idsearch, auth=bearer_oauth)
    json_object = json.loads(status.text)
    url = url_before + json_object["data"]["id"] + search_url
    folder = makefolder + name
    os.makedirs(folder, exist_ok=True)
    while true:
        #APIを叩いて結果を取得
        response = requests.get(url, auth=bearer_oauth, params=params)

        #ステータスコードが200以外ならエラー処理
        if response.status_code != 200:
            raise Exception(response.status_code, response.text)

        #responseからJSONを取得してループを回し、URLを追加していく
        json_response = response.json()
      
        if 'includes' in json_response:
            for image in json_response['includes']['media']:
                try:
                    download_file_to_dir(image['url'], folder)
                except:
                    list.append(image['media_key'])

        print("mediakey:")
        print(list)
                
        for tweet in json_response['data']:
            try:
                print(tweet['attachments']['media_keys'], tweet['id'])
            except:
                pass
            else:
                if tweet['attachments']['media_keys'][0] in list:
                    idlist.append(tweet['id'])
        print("tweetid:")    
        print(idlist)

        for id in idlist:
            print(id)
            retrieve_video(id,folder)

        if hasattr(json_response['meta'],'next_token'):
            try:
                query_params['pagination_token'] = json_response['meta']['next_token']
                print(json_response['meta']['next_token'])
            except:
                print("nextpagetoken_error")
                break
        else:
            print("all_download")
            break

    
#実行
connect_to_endpoint(videokey,video_tweetid,username,query_params)

print("download_complete")

