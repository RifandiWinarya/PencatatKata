import requests

api_key = '78a7ed44-2013-47ea-8b24-b46e270ccfab'
word = 'potato'
url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{word}?key={api_key}'

res = requests.get(url)
datas = res.json()

for data in datas:
    print(data)