# coding:utf8
"""
BaseCrawler is The Crawler Framework, Author is Salem.Jin, my nickname is 39
Github:https://github.com/ever391/base-crawler
I first write BaseCrawler of The Crawler Framework, I hope everybody like it.
The BaseCrawler is very flexible, you can use function  do you wanna things in the class
"""

import io
import re
import time
import random
import logging
import requests
import urlparse
import imghdr
import urllib
import lxml


try:
    from Pillow import Image
except:
    from PIL import Image
from selenium import webdriver
from bs4 import BeautifulSoup
from lxml import etree
from selenium.webdriver.common.proxy import Proxy, ProxyType



USER_AGENTS = [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36"
    ]


HEADER = {
    'User-Agent': random.choice(USER_AGENTS),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
    'Accept-Encoding': 'gzip, deflate',
}

class BaseCrawler(object):
    """基础爬虫类,实现多种解析方法及实用功能"""

    def __init__(self):
        """
        构造方法
        """
        self.request = requests.Session()
        self.request.headers.update(HEADER)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        fmt = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        fh = logging.FileHandler('crawler.log')
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)

    def run(self, *args, **kwargs):
        """
        抽像方法：主程序入口

        :param args:

        :param kwargs:

        :return: None
        """
        raise ImportError('you must override this function')


    def get_content_urls(self, *args, **kwargs):
        """
        抽像方法：获取内容页url列表

        :param args:

        :param kwargs:

        :return: List [url1,url2,url3]
        """
        raise ImportError('you must override this function')

    def get_content(self, *args, **kwargs):
        """
        抽像方法：解析内容页结果

        :param args:

        :param kwargs:

        :return: Json {"title":String,"content":String,……}
        """
        raise ImportError('you must override this function')

    def static_downloader_get(self, url, charset='utf8', timeout=15, proxy=None):
        """
        静态爬取

        :param url: String 目标url

        :param charset: String 解码格式

        :param timeout: int 超时时间

        :param proxy: Json {"http":"http://ip:port","https":"http://ip:port"}

        :return: requests.Response对象
        """
        response = self.request.get(url, proxies=proxy, timeout=timeout)
        response.encoding = charset
        return response

    def get_phantomjs_browser(self, proxy=None, timeout=15,):
        """
        创建一个phantomjs浏览器

        :param proxy: String "ip:port"

        :param timeout: Int

        :return: Phantomjs.Browser 浏览器对象
        """
        capabilities = webdriver.DesiredCapabilities.PHANTOMJS
        capabilities['phantomjs.page.settings.userAgent'] = random.choice(USER_AGENTS)
        capabilities["phantomjs.page.settings.loadImages"] = False
        if proxy:
            prox = Proxy()
            prox.proxy_type = ProxyType.MANUAL
            prox.http_proxy = proxy
            prox.socks_proxy = proxy
            prox.ssl_proxy = proxy
            prox.add_to_capabilities(capabilities)

        browser = webdriver.PhantomJS(desired_capabilities=capabilities)
        browser.maximize_window()
        browser.set_page_load_timeout(timeout)
        return browser


    def css_parser_urls(self, soup, css_rule, limit=None):
        """
        基于CSS选择器解析

        :param soup: Obj BeautifulSoup对象

        :param css_rule: String css提取规则

        :param limit: Int 限制

        :return: List [url1,url2,url3]
        """
        if not isinstance(soup, BeautifulSoup):
            raise ValueError('args soup must a BeautifulSoup object!')
        if not isinstance(css_rule, str):
            raise ValueError('args rules must a str object!')

        urls = []
        list_node_a = soup.select(css_rule, limit=limit)
        for node_a in list_node_a:
            try:
                url = node_a['href']
            except Exception as e:
                url = None
            if not url:
                continue

            urls.append(url)
        return urls

    def format_proxy_by_requests(self, ip):
        """
        格式化为requests代理格式

        :param ip: String "127.0.0.1:1234"

        :return: Dict {"http":"http://127.0.0.1:1234","https":"https://127.0.0.1:1234"}
        """
        return {
            "http": "http://{}".format(ip),
            "https": "https://{}".format(ip)
        }

    def exec_lazy_loads(self, browser, start=1000, stop=10000, step=1000, interval=0.1):
        """
        Phantomjs浏览器惰性加载

        :param browser: Obj Phantomjs浏览器对象

        :param start: Int 开始页

        :param stop: Int 停止页

        :param step: Int 偏移页

        :param interval: Float 频率

        :return: Obj 完成惰性加载后的Phantomjs浏览器对象
        """
        if not isinstance(browser, webdriver.PhantomJS):
            raise ValueError('args browser must a webdriver PhantomJS object!')

        for i in range(start, stop, step):
            browser.execute_script('document.body.scrollTop={}'.format(i))
            time.sleep(interval)
        return browser

    def get_full_url(self, base_url, half_url, is_img=False):
        """
        获取完整url地址

        :param base_url: String 源地址

        :param half_url: String 提取后的非完整url地址

        :return: String 完整的url地址
        """
        SPECIAL_URLS = ['arinchina.com']
        IMG_SPECIAL_URLS = ['itp8.com', 'guijinshu.com', 'chinarta.com', 'cmmo.cn']
        protocol, result = urllib.splittype(base_url)
        base_url, rest = urllib.splithost(result)
        base_url = protocol + '://' + base_url
        if is_img:
            SPECIAL_URLS = IMG_SPECIAL_URLS
        url_flag = False
        for special_url in SPECIAL_URLS:
            if special_url in base_url:
                url_flag = True

        if not url_flag and (not half_url.startswith('/') or half_url.startswith('./')) :
            url = urlparse.urljoin(base_url, half_url)
        elif half_url.startswith('//'):
            url = 'http:' + half_url
        elif half_url.startswith('../'):
            filter_url = re.sub('\.\./', '', half_url)
            url = urllib.basejoin(base_url, filter_url)
        else:
            url = urlparse.urljoin(base_url, half_url.strip('..'))
        return url


    def datetime_format(self, datetime):
        """
        时间格式化, 非标准时间："1天前，2天前……大于2天未进行格式化"

        :param datetime: String 任何格式的时间

        :return: String example: 2017-10-6
        """
        if ',' in datetime:
            time_info = datetime.split(',')
            time_info[2] = time_info[2].split(' ')
            time_info[2] = time_info[2][1]
            time_info = time_info[2] + unicode(time_info[1])
            months = [u'一月', u'二月', u'三月', u'四月', u'五月', u'六月', u'七月', u'八月', u'九月', u'十月', u'十一月', u'十二月']
            months_num = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
            datetime = dict(zip(months, months_num))
            for mon in months:
                if mon in time_info:
                    time_info = time_info.split(' ')
                    month = datetime[time_info[1]]
                    time_format = time_info[0] + '-' + month + '-' + time_info[2]
                    break
        else:
            unstandard_time = False
            keyword_times = [u'天前', u'昨天', u'前天', u'月前', u'年前']
            for keyword in keyword_times:
                if keyword in datetime:
                    unstandard_time = True
                    break

            if unstandard_time:
                time_info = False
                if ('1' in datetime and u'天前' in datetime) or u'昨天' in datetime:
                    time_info = time.time() - 86400

                if ('2' in datetime and u'天前' in datetime) or u'前天' in datetime:
                    time_info = time.time() - 86400 * 2

                for day in range(3, 32):
                    if (str(day) in datetime and u'天前' in datetime):
                        time_info = time.time() - 86400 * day
                        break

                for months in range(1, 13):
                    if (str(months) in datetime and u'月前' in datetime):
                        time_info = time.time() - (86400 * 30) * months
                        break

                for year in range(1, 11):
                    if (str(year) in datetime and u'年前' in datetime):
                        time_info = time.time() - (86400 * 30 * 12) * year
                        break

                if u'小时' in datetime or u'分钟' in datetime:
                    time_info = time.time()

                if not time_info:
                    time_info = time.time()

                time_info = time.localtime(time_info)
                time_format = time.strftime('%Y-%m-%d', time_info)
            else:
                time_format = datetime

            year = time.localtime()[0]
            result = re.search(u'(\d{4})[-,/,年, ]+(\d+)[-,/,月, ]+(\d+)|(\d+)[-,/,月, ]+(\d+)', time_format)
            if result:
                result = result.groups()
            if result[0]:
                time_format = result[0] + '-' + result[1] + '-' + result[2]
            else:
                time_format = str(year) + '-' + result[3] + '-' + result[4]

        return time_format

    def re_exclude(self, rule, content, separator=":::"):
        """
        正则不包含

        :param rule: String 正则规则

        :param content: String 被匹配的内容

        :param separator: String 分隔符

        :return: String 被过滤后的内容
        """
        if separator in rule:
            exclude_rules = rule.split(separator)
            for exclude_rule in exclude_rules:
                content = re.sub(exclude_rule, '', content, flags=re.S)
        else:
            content = re.sub(rule, '', content, flags=re.S)
        return content

    def re_parser(self, rule, content):
        """
        正则匹配内容

        :param rule: String 正则规则

        :param content: String 被匹配的内容

        :return: String 匹配后的结果
        """
        if rule:
            item = re.search(rule, content, flags=re.S)
            if not item:
                return
            try:
                result = item.group()
                return result
            except AttributeError:
                return
        else:
            return content

    def static_many_page(self, url, start_page, stop_page, step=1, chaset='utf8', timeout=15, proxy=None):
        """
        爬取多页
        :param url: String 格式化后的ulr "http://www.news.com?page={page}"

        :param start_page: Int 开始页面

        :param stop_page: Int 结束页面

        :return: requests.Response对象
        """
        for num in range(start_page, stop_page+1, step):
            print url
            tmp_url = url.format(page=num)
            yield self.static_downloader_get(tmp_url, charset=chaset, timeout=timeout, proxy=proxy)

    def get_picture(self, base_url, content, bucket=None):
        """
        下载图片

        :param base_url: String 文章URL

        :param content: String HTML

        :param bucket: Obj 阿里云 服务使用

        :return: String HTML

        pics List [主图片列表]
        """
        # data-original 图片处理
        SP_URLS_DATA_ORIGINAL = ['sfw.cn', 'ithome.com', 'bzw315.com', 'sootoo.com', 'newmotor.com.cn', 'meihua.info',
                                 'zhulong.com', 'ixiqi.com']
        # original 图片处理
        SP_URLS_ORIGINAL = ['chrm.cn']
        # file 图片处理
        SP_URLS_FILE = ['wisenjoy.com', 'useit.com.cn']
        # src与data-src都存在的处理
        SP_URLS_SRC_AND_DATA_SRC = ['36kr.com']
        # data-src 处理
        SP_URLS_DATA_SRC = ['mp.weixin.qq.com', 'qdaily.com']

        try:
            content = re.sub('<IMG', '<img', content)
        except Exception as e:
            logging.error(str(e))
        try:
            pics = []
            img_data_original = [sp_url for sp_url in SP_URLS_DATA_ORIGINAL if sp_url in base_url]
            img_original = [sp_url for sp_url in SP_URLS_ORIGINAL if sp_url in base_url]
            img_file = [sp_url for sp_url in SP_URLS_FILE if sp_url in base_url]
            img_src_and_data_src = [sp_url for sp_url in SP_URLS_SRC_AND_DATA_SRC if sp_url in base_url]
            img_data_src = [sp_url for sp_url in SP_URLS_DATA_SRC if sp_url in base_url]
            if bool(img_data_original):
                urls = re.findall('<img.*?data-original="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)
            elif bool(img_original):
                urls = re.findall('<img.*?original="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)
            elif bool(img_file):
                urls = re.findall('<img.*? file="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)
            elif bool(img_src_and_data_src):
                urls = re.findall('<img.*? src="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)
                urls = re.findall('<img.*? data-src="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)
            elif bool(img_data_src):
                urls = re.findall('<img.*? data-src="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)
            else:
                urls = re.findall('<img.*? src="(.*?)"', content, re.M)
                content, pics = self.download_img(urls, base_url, content, bucket, pics)

            return content, pics
        except Exception as e:
            logging.error(base_url + ':::' + str(e), exc_info=True)
            return content, pics

    def download_img(self, urls, base_url, content, bucket, pics, img_base_name=''):
        """
        图片下载
        :param urls: List 提取图片链接地址

        :param base_url: String 文章URL

        :param content: String HTML

        :param bucket: Obj 阿里云oss服务使用

        :param pics: List 空列表

        :param img_base_name: String 图片名前缀
        :return: String 替换图片地址后的HTML

            List 符合格式大小的图片列表地址
        """
        for url in urls:
            url = url.strip()

            if len(url) == 0:
                continue

            img_url = url
            if 'http' not in img_url:
                img_url = self.get_full_url(base_url, url, is_img=True)
            try:
                if 'bzw315.com' in img_url:
                    img_url = img_url.split('?')[0]
                try:
                    pict_content = requests.get(img_url, timeout=20).content
                except:
                    continue

                img_flag = self.is_img_uniform_size(pict_content)
            except Exception as e:
                print '%s' % e.message
                continue
            try:
                name = self.get_img_name(pict_content)
            except Exception as e:
                continue
            if bucket:
                try:
                    bucket.put_object(name, pict_content)
                except Exception as e:
                    print '3' * 100
                    logging.error(url + e.message)
                    logging.info(url)
                    continue


            oss2_pict = ''.join(img_base_name + name)
            pat = self.get_img_replace_pattern_rule(url)
            content = re.sub(pat, '<img src="{}"/>'.format(oss2_pict), content)

            if img_flag:
                pics.append(oss2_pict)
        return content, pics

    def is_img_uniform_size(self, img_content):
        """
        判断图片格式大小是否符合要求

        :param img_content: Stream2bin 2进制流文件

        :return: Boole True/False
        """
        try:
            img = Image.open(io.BytesIO(img_content))
        except:
            print 'Image.open io.BytesIO failed'
            return
        height, width = img.size
        img_flag = True
        if height < 150 or width < 150:
            img_flag = False
        return img_flag

    def get_image_format(self, img_content):
        """
        获取图片格式

        :param img_content: img_content: Stream2bin 2进制流文件

        :return: String 图片格式
        """
        return imghdr.what('test', img_content)

    def get_img_replace_pattern_rule(self, url):
        """
        图片地址预处理

        :param url: String url

        :return: String 正则匹配规则
        """
        if u'(' in url:
            url = re.sub('\(', '\(', url)
        if u')' in url:
            url = re.sub('\)', '\)', url)
        if u'?' in url:
            url = re.sub('\?', '\?', url)
        pat = u'<img .*?"{}".*?>'.format(url)
        return pat

    def get_proxy_ips(self):
        """
        获取99个ip代理, 不要频烦请求

        :return: List ip代理列表
        """
        url = 'http://www.xicidaili.com/nn/1'
        response = self.static_downloader_get(url)
        select = etree.HTML(response.text)
        ips = set()
        for tr_node in select.xpath('//*[@id="ip_list"]/tr[position()>1]'):
            ip = tr_node.xpath('td[2]/text()')[0]
            port = tr_node.xpath('td[3]/text()')[0]
            ip_and_port = ip + ':' + port
            ips.add(ip_and_port)
        return ips

    def login_account(self, url, data):
        """
        网站登录操作

        :param url: String 登录请求的url地址

        :param data: Dict 登录请求提交的相关数据

        :return:  None
        """
        self.request.post(url, data)

    def update_headers(self, header):
        """
        修改请求头信息

        :param header: Dict 请求头信息

        :return:
        """
        self.request.headers.update(header)
        return None

if __name__ == "__main__":
    bc = BaseCrawler()
    print len(bc.get_proxy_ips())

