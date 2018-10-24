import os
import requests
import json
from lxml import etree
import urllib3
from hashlib import md5
urllib3.disable_warnings()
from urllib import parse

headers = {
    'Orgin': 'https://www.instagrame.com/',
    'Referer': 'https://www.instagram.com/ahmad_monk/',
    'User-Agent': 'Mozilla/5.0(Macintosh;U;IntelMacOSX10_6_8;en-us)AppleWebKit/534.50(KHTML,\
    likeGecko)Version/5.1Safari/537.36',
    #'Host': 'www.intagram.com'
}

base_url = 'https://instagrame.com/ahmad_monk/'

class Ins_Img():

    # 初始化类
    def __init__(self):
        self.s = requests.session()

    # 访问首页，得到返回页面
    def visit_firstpage(self):
        self.res = self.s.get(base_url, headers=headers, verify=False)

    # json化返回数据
    def get_firstpage(self):

        html = etree.HTML(self.res.content)
        self.html = html.xpath('''//script[@type="text/javascript"]''')[3].text.replace('window._sharedData =', '').strip()[:-1]
        self.detail_img = json.loads(self.html, encoding='utf-8')

    # 结构化解析数据，得到关键数据并返回
    def parse_first_page(self):
        de_dic = self.detail_img['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']
        detail_dic = self.detail_img['entry_data']['ProfilePage'][0]['graphql']['user']['edge_owner_to_timeline_media']['edges']
        print(de_dic)
        self.on = de_dic['page_info']['has_next_page']
        self.next = de_dic['page_info']['end_cursor']

        print(self.next)
        self.src_list = []
        self.id = detail_dic[0]['node']['owner']['id']
        print(self.id)

        for node in detail_dic:
            self.src_list.append(node['node']['display_url'])
            yield {
                'imgurl': node['node']['display_url'],
                'likecount': node['node']['edge_liked_by']['count'],
                'comment': node['node']['edge_media_to_comment']['count'],
                'insmsg': node['node']['edge_media_to_caption']['edges'][0]['node']['text'],
                'shortcode': node['node']['shortcode']
            }

    #未实现功能，需要得到query_hash参数
    def get_query_hash(self):
        pass

    # 解析需要翻页才能得到的数据，并得到关键参数
    def parse_next_page(self):
        params = {
            'id': self.id,
            'first': 12,
            'after': self.next
        }
        url = 'https://www.instagram.com/graphql/query/?query_hash=bd0d6d184eefd4d0ce7036c11ae58ed9&variables'
        res = self.s.get(url, headers=headers, params=params)
        print(res.status_code)
        self.html = etree.HTML(res.content)
        self.detail = json.loads(self.html, encoding='utf-8')
        self.count = self.detail['data']['user']['edge_owner_to_media']['count']
        self.on = self.detail['data']['user']['edge_owner_to_media']['page_info']['has_next_page']
        self.next = self.detail['data']['user']['edge_owner_to_media']['page_info']['end_cursor']
        nodes = self.detail['data']['user']['edge_owner_to_media']['edges'][0]

        for node in nodes:
            self.src_list.append(node['node']['display_url'])

            yield {
                'imgurl': node['node']['display_url'],
                'likecount': node['node'][''],
                'comment': node['node']['edge_media_comment']['count'],
                'insmsg': node['node']['edge_media_comment']['edges'][0]['node']['text'],
                'shortcode': node['node']['shortcode']
            }

    # 保存和图片有关的信息如图片链接，点赞数，评论数，具体内容
    def save_file(self, content):
        with open('img_message.txt', 'a', encoding='utf-8') as f:
            f.write(json.dumps(content, ensure_ascii=False) + '\n')

    # 下载所有的图片并保存
    def save_img(self,item):
        if not os.path.exists(item.get('shortcode')):
            os.mkdir(item.get('shorcode'))

        try:
            res = self.s.get(item.get('imgurl'))

            if res.status_code == 200:
                file_path = '{}/{}.{}'.format(item.get('shortcode'), md5(res.content).hexdigest(), 'jpg')
                print('开始下载%s'%item.get('shortcode'))

                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(res.content)
                else:
                    print('已下载',file_path)
        except requests.ConnectionError:
            print('下载失败')


if __name__ == '__main__':

    ins_img = Ins_Img()
    ins_img.visit_firstpage()
    ins_img.get_firstpage()
    ins_img.parse_first_page()

    for item in ins_img.parse_first_page():
        ins_img.save_file(item)
        ins_img.save_img(item)

    while ins_img.on:
        ins_img.parse_next_page()

        for item in ins_img.parse_next_page():
            ins_img.save_file(item)

# 从开始知道要独立写一个的爬取内容较大的爬虫是是很担心的，又因为需要翻墙，难免有点着急忙慌，好在坚持下来了，对xpath和动态页面数据的处理有了更有效的经验
# 这个ins爬虫因为自己对js破解不熟，虽然找到了加密query_hash参数的js文件，想过用selenium来破解，本来想的是用selenium破解第一页然后得到加密的参数
# 之后需要翻页的数据就用requests来做，找了资料，没有发现可以用selenium来得到加密的元素的方法，也了解过用pyv8来解密js文件得到加密的参数
# 也是因为不了解js，自己的不足还有很多，虽然自己之前也做了一些项目，如猫眼电影的爬取（静态页面），头条图片的爬取（ajax加载页面），微博破解登陆（password为rsa加密）
# 但因为这些项目都可以找到范例，并不是很难，相反这个ins图片的爬取因为网站更新了，加了一个需要加密的参数而网上有没有实际的例子所以学到了很多
# 问了一些程序员朋友这个项目算简单的，唯一的难点就是破解query_hash参数了

