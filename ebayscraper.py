from gevent import monkey

monkey.patch_all()
import os
import webbrowser
import requests
from bs4 import BeautifulSoup
import re
import easygui
from yattag import Doc
from gevent.pool import Pool
import urllib.parse


TITLE = 'eBay Scraper'

country_codes = {
    'International': '',
    'Korea': '111',
    'Japan': '104',
    'United States': '1',
    'Spain': '186',
    'Turkey': '204',
    'Israel': '100',
    'India': '95',
    'Canada': '1',
    'United Kingdom': '3',
}


def scrape_ebay(ebay_url):
    r = requests.get(ebay_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'})

    html = r.text
    soup = BeautifulSoup(html, 'lxml')

    for el in soup.find_all(attrs={'class': 'li'}):

        try:
            item_name = el.find(attrs={'class': 'vip'}).text
            href = el.find(attrs={'class': 'vip'}).get('href')
            location = ''

            letter = href.split(':')[-2]
            item_id = href.split(':')[-1]
            img = f'https://i.ebayimg.com/thumbs/images/{letter}/{item_id}/s-l225.jpg'

            price = el.select('.prc .bold')[0].text.strip().replace(',', '').split('$')[-1]

            sales = el.find_all(attrs={'class': 'hotness-signal'}, text=re.compile(r'.*Sold'))
            if sales:
                sales = sales[0].text.strip()
                sales = re.findall(r'\d+', sales)[0]
            else:
                continue

            data[item_name] = {'price': float(price), 'sales': int(sales), 'url': href, 'img': img, 'location': location}

        except AttributeError:
            break


while True:
    data = {}

    item = easygui.enterbox('Scrape Item:', TITLE)
    item = urllib.parse.quote_plus(item)

    if item == '':
        continue
    elif not item:
        quit()

    country_choices = easygui.multchoicebox('Item Location/s:', TITLE, [k for k, v in country_codes.items()])

    for country in country_choices:
        print(f'Scraping {country}...')

        pool = Pool(25)
        for n in range(1, 11):
            url = f'https://www.ebay.com/sch/i.html?_ftrt=901&_sop=12&_dmd=1&LH_BIN=1&_ftrv=1&_from=R40&_sacat=0&_fosrp=1&_nkw={item}&LH_LocatedIn={country_codes[country]}&_ipg=200&rt=nc&_pgn={n}&LH_TitleDesc=1'
            pool.spawn(scrape_ebay, url)

        pool.join()

    s = sorted(data, key=lambda x: int(data[x]['sales']), reverse=True)

    doc, tag, text = Doc().tagtext()

    with tag('body', style="font-family: Roboto"):
        with tag('div', style="margin: 20px auto; width: 90%;"):
            with tag('h1', style="font-weight: bold; font-size: 32px; margin: 5px; color: #1242b9;"):
                text('eBay Scraper')
        for i in s:
            with tag('div', style="margin: 25px auto; width: 90%;"):
                with tag('a', href=data[i]['url'], style="text-decoration: none; color: black;"):
                    text(f"{i}")
                    with tag('div', style="font-size: 12px;"):
                        text(f"{data[i]['location']}")
                    with tag('div', style="font-size: 12px; font-weight: bold; color: #e81f1f"):
                        text(f"{data[i]['sales']} sold")
                    with tag('div', style="font-size: 12px;"):
                        text(f"${data[i]['price']}")
                    with tag('div'):
                        doc.stag('img', src=f"{data[i]['img']}", style='height: 100px; margin-left: 10px 0; border-radius: 7px;')

    with open('temp.html', 'w', encoding='utf-8') as f:
        f.write(doc.getvalue())

    html_path = 'file:///' + os.path.abspath('temp.html')
    webbrowser.open(html_path)
