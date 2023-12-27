import requests, re
from io import BytesIO
from PIL import Image, ImageChops, ImageMath
from os import environ as env

## we use newtoki.help for now because of newtoki's captchas.
url_b = 'https://newtoki.help/webtoon/453'
url_w = 'https://newtoki.help/webtoon/456'

url_webhook = env.get('WEBHOOK_URL')



# Check if newtoki changed urls recently

tme = requests.get('https://t.me/s/newtoki5')
newtoki_domain = re.search(r'https://(newtoki\d+)\.com', tme.text).group(1)
try:
    with open('newtoki_lastknown.txt', 'r') as state:
        if state.read() == newtoki_domain:
            exit()
except FileNotFoundError:
    pass

with open('newtoki_lastknown.txt', 'w') as state:
    state.write(newtoki_domain)


# Image scraping

LATESTCHAPTER_REGEX = r'<div class="toon_index">(?:.|\s)*?<li><a href="(.*?)"'
LASTIMAGE_REGEX = r'<img src="([^<]*?)"[^<]*?>\s*?<br><br>'

listing_w = requests.get(url_w)
url_latest_w = re.search(LATESTCHAPTER_REGEX, listing_w.text).group(1)
chapter_w = requests.get(url_latest_w)
url_lastImage_w = re.search(LASTIMAGE_REGEX, chapter_w.text).group(1)

listing_b = requests.get(url_b)
url_latest_b = re.search(LATESTCHAPTER_REGEX, listing_b.text).group(1)
chapter_b = requests.get(url_latest_b)
url_lastImage_b = re.search(LASTIMAGE_REGEX, chapter_b.text).group(1)

# Image loading

file_b = requests.get(url_lastImage_b)
ib = Image.open(BytesIO(file_b.content))
file_b.close()
ibc = ib.crop([ib.width - 180, ib.height - 200, ib.width - 20, ib.height - 5])
ib.close()
file_w = requests.get(url_lastImage_w)
iw = Image.open(BytesIO(file_w.content))
file_w.close()
iwc = iw.crop([iw.width - 180, iw.height - 200, iw.width - 20, iw.height - 5])
iw.close()

# Watermark extracting

ibwdiff = ImageChops.difference(iwc, ibc)
iwc.close()
ia = ImageChops.invert(ibwdiff.convert('L'))
ibwdiff.close()
iex = Image.merge('RGB', [ImageMath.eval(r"convert(255.0*float(b)/float(a), 'L')", a=ia, b=ibc.getchannel(x)) for x in 'RGB'])
iex.putalpha(ia)

## Save to in-memory BytesIO
ex_c = BytesIO()
ex_g = BytesIO()

iex.save(ex_c, format='PNG')
## generate gray watermark
iex.putalpha(ImageMath.eval(r"convert(float(a)*0.5, 'L')", a=ia))
iex.convert('LA').save(ex_g, format='PNG')
ia.close()
iex.close()

# Upload to discord
ex_c.seek(0)
ex_g.seek(0)
requests.post(url_webhook, files={
    'file1': (f'./{newtoki_domain}-color.png', ex_c),
    'file2': (f'./{newtoki_domain}-gray.png', ex_g),
})
