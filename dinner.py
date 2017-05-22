#! python
# -*- coding: utf-8 -*-
import sys
import time
import datetime
import calendar
import urllib
import re
import random
import getpass

sys.path.append('requests-2.5.1')
import requests

server_url = 'http://172.16.64.141:8080/od'
favorite_list = [
    '田鄉-總匯',
    '大廚-無骨',
    '大廚-嘴邊',
    '大廚-麻辣雞',
    '原味',
    '養生-鐵板',
    '小南-黑胡椒',
    '好吉米-黑白',
    '香港-叉燒燒肉',
    '香港-三寶',
    '隆哥-蔥爆',
    '綜合',
    '豬',
    '牛',
    '雞',
    '八方-蔬菜',
    '鬍鬚張']


def read_list_from_file():
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rU') as in_file:
            global favorite_list
            favorite_list = in_file.read().split('\n')

def print_favorite_list():
    print 'Favorite list: ' + ', '.join(favorite_list)


def login(s, user, passwd):
    payload = {'user': user, 'passwd': passwd}
    response_post = s.post(server_url + '/login.jsp', data=payload)
    return not ('使用者或密碼錯誤'.decode('utf-8') in response_post.text)


def check_order(s):
    response_post = s.post(server_url + '/user_query.jsp')
    #print response_post.text
    return re.search(time.strftime('%Y%m%d') + '(.*)\n(.*)left\">(.*)</td>', response_post.text)


def make_order(s):
    response_post = s.post(server_url + '/user_order.jsp')
    all_items = re.findall('item_(.*)\" value=\"(.*)\"', response_post.text)
    all_items_len = len(all_items)

    if all_items_len <= 0:
        print '  Dinner menu is not ready, please wait...'
        return

    selection = 0 # default selection
    for f, i in ((f, i) for f in favorite_list for i in range(all_items_len)):
        if f.decode('utf-8') in all_items[i][1]:
            selection = i
            print 'Favorite matched: %s (%s)' % (all_items[i][1], f.decode('utf-8'))
            break
    else:
        selection = random.randint(0, all_items_len - 1) # random selection
    print '(all_items_len=' + str(all_items_len) + ', selection=' + str(selection) + ')'

    order_url = server_url + '/OrderProcess.jsp?orderdate=' + time.strftime('%Y%m%d') + '&company=' + urllib.quote('不限訂廠商'.decode('utf8').encode('big5'))
    for i in range(all_items_len):
        if i == selection:
            order_url += '&order=' + str(i+1)
            print '> ' + all_items[i][1]
        else:
            print '  ' + all_items[i][1]
        order_url += '&item_' + str(i+1) + '=' + urllib.quote(all_items[i][1].encode('big5'))
        order_url += '&qty_' + str(i+1) + '=1'

    #print order_url
    response_post = s.get(order_url)


def order_dinner(user, passwd):
    with requests.session() as s:
        if not login(s, user, passwd):
            raise Exception('Invalid account!')

        match = check_order(s)
        if match:
            print 'You have ordered a Ban-Don today: ' + match.group(3)
        else:
            print 'Randomly ordered a Ban-Don for you today.'
            print_favorite_list()
            make_order(s)


def main():
    print 'This is a dinner ordering daemon for MStar Taipei.'
    user = raw_input('Please enter username: ')
    passwd = getpass.getpass(prompt='Please enter passwd: ')
    if not login(requests.session(), user, passwd):
        raise Exception('Invalid account!')

    day_start = 0
    day_end = 4
    time_start = datetime.time(10, 0, 0)
    time_end = datetime.time(14, 0, 0)
    str_time_avail = '(Available time: %s - %s, %s - %s)' % (calendar.day_abbr[day_start], calendar.day_abbr[day_end], time_start, time_end)

    read_list_from_file()
    print_favorite_list()
    print '\n' + str_time_avail + '\n'

    while True:
        weekday = datetime.datetime.today().weekday()
        time_now = datetime.datetime.now().time()
        print(time.strftime('[%Y-%m-%d %H:%M:%S]')),
        if day_start <= weekday <= day_end and time_start < time_now < time_end:
            try:
                read_list_from_file()
                order_dinner(user, passwd)
            except KeyboardInterrupt:
                raise
            except:
                print 'crashed somehow, might be connection issue.'
        else:
            print 'Not yet. ' + str_time_avail
        time.sleep(60 * 60) # 60 min


if __name__ == '__main__':
  main()

