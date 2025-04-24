import json
import base64
import time

from Crypto.Cipher import ARC4
from base.spider import Spider
from concurrent.futures import ThreadPoolExecutor


class Spider(Spider):

    def init(self, extend=""):
        if extend:
            host = json.loads(extend)['site']
            self.host = host
        else:
            self.host = "http://110.42.7.59:12388"

    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9; GM1910 Build/PQ3B.190801.12281726)',
        'Authorization': 'Basic c2hlbm1hOnNoZW5tYQ=='
    }
    data = {
        "os": 28,
        "data": "iZwnewb1gvJylJv+MPJQeQB9nM0D4dwHW/fMXTx2rY9YiS3o0YVfEo6t3yI26Iha",
        "sign": "cjJ1cjJjclZVVGN3ZlNXSg=="
    }
    keys = ["90070576afe435782122d0a06e1c6004"]

    # 获取展示类别
    def homeContent(self, filter):
        t, key = self.getTK()
        self.data['time'] = t
        self.data['key'] = key
        resp = self.post(self.host + "/api.php/smtv/Category", headers=self.headers, data=self.data)
        result = {}
        classes = []
        filters = {}
        for i in resp.json():
            classes.append({
                'type_id': i['type_en'].lower(),
                'type_name': i['type_name']
            })

        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.getf, i['type_id'])
                       for i in classes]
            for future in futures:
                try:
                    type_id, filter_data = future.result()
                    if len(filter_data): filters[type_id] = filter_data
                except Exception as e:
                    print(f'处理筛选数据失败: {e}')

        result['class'] = classes
        result['filters'] = filters
        return result

    # 获取站点推荐内容
    def homeVideoContent(self):
        data = self.getdata('/api.php/smtv/top').get('data')
        list = self.getlist(data)
        return {'list': list}

    # 搜索
    def searchContent(self, key, quick, pg="1"):
        data = self.getdata(f'/api.php/smtv/vod/?ac=list&zm={key}&page={pg}').get('data')
        list = self.getlist(data, True)
        return {'list': list, "page": pg}

    # 根据类别获取
    def categoryContent(self, tid, pg, filter, extend):
        data = self.getdata(f'/api.php/smtv/vod/?ac=list&class={tid}&page={pg}').get('data')
        result = {}
        result['list'] = self.getlist(data, True)
        result['page'] = pg
        result['pagecount'] = 9999
        result['limit'] = 90
        result['total'] = 999999
        return result
    # 视频详情
    def detailContent(self, ids):
        data=self.getdata(f'/api.php/smtv/vod/{ids[0]}')
        vod={}
        vod['vod_id']=data.get('id')
        vod['vod_name']=data.get('title')
        vod['vod_remarks']=data.get('trunk')
        vod['vod_content']=data.get('intro')
        vod['vod_pic']=data.get('img_url')
        vod['vod_year']=data.get('pubtime')
        vod['vod_score']=data.get('season_num')
        vod['vod_actor']=" ".join(data.get('actor'))
        vod['vod_class']=" ".join(data.get('type'))
        plist,tlist = [],[]
        for i in data.get("video_list"):
            tlist.append(i['name'].strip())
            plist.append('#'.join([f"{j['title']}$@@{j['url']}" for j in i['list']]))
        return {'list':[vod]}
    # 播放视频

    def getlist(self, data, search=False):
        videos = []
        for i in data:
            videos.append({
                'type_id': i['tjtype'].lower() if not search else i['type'].lower(),
                'vod_id': i['tjurl'] if not search else i['nextlink'],
                'vod_name': i['tjinfo'] if not search else i['title'],
                'vod_pic': i['tjpicur'] if not search else i['pic'],
                'vod_remarks': i['state']
            })
        return videos

    def getdata(self, path, ):
        t, key = self.getTK()
        self.data['time'] = t
        self.data['key'] = key
        url = f'{self.host}{path}'
        response = self.post(url, headers=self.headers, data=self.data).text
        return json.loads(self.decrypt(response, self.keys[0]))

    def getf(self, type_id):
        try:
            fdata = self.getdata(f'/api.php/smtv/vod/?&ac=flitter&class={type_id}')
            filter_list = []
            for value in fdata['flitter']:
                if len(value):
                    filter_list.append({
                        'key': value["field"],
                        'name': value["name"],
                        'value': [{'n': j, 'v': j} for j in value['values']]
                    })
            return type_id, filter_list
        except Exception as e:
            print(f'获取type_id={type_id}的筛选数据失败: {e}')
            return type_id, []

    # RC4解密
    def decrypt(self, cipher_text, key):
        des3 = ARC4.new(key.encode())
        message = des3.decrypt(base64.b64decode(cipher_text))
        return message

    # RC4加密
    def encrypt(self, data: str, key: str) -> str:
        cipher = ARC4.new(key.encode("utf-8"))
        encrypted_bytes = cipher.encrypt(data.encode("utf-8"))
        return encrypted_bytes.hex()

    def getTK(self):
        t = int(time.time())
        key = self.encrypt(str(t), str(t))
        return t, key
