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

    def getdata(self, path, data=None, json_data=None):
        url = f'{self.host}{path}'
        response = self.post(url, headers=self.headers, data=data, json=json_data).text
        return json.loads(self.decrypt(response, self.keys[0]))

    def getf(self, type_id):
        try:
            t, key = self.getTK()
            self.data['time'] = t
            self.data['key'] = key
            fdata = self.getdata(f'/api.php/smtv/vod/?&ac=flitter&class={type_id}',
                                 data=self.data)
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
