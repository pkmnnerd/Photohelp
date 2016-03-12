from django.shortcuts import render
from django.http import HttpResponse
import requests
import json
import threading
import sets

def get_exif(id, secret, photo):
    s = sets.Set();
    ids = [
        'Make',
        'Model',
        'Exposure',
        'Aperture',
        'ISO Speed',
        'Date and Time (Original)',
        'Focal Length',
        'Focal Length (35mm format)',
        'Lens Model'
    ]

    r2 = requests.get('https://api.flickr.com/services/rest/?' +
        'method=flickr.photos.getExif&photo_id=' + id + '&secret=' + 
        secret + '&api_key=4e37767c7f7d8bc0d9399aae58a5bb3f&format=json')
    etext = json.loads(r2.text[14:-1])
    elist = []
    if 'photo' in etext:
        exif = etext['photo']['exif']
        
        for e in exif:
            edata = {};
            if 'label' in e and e['label'] in ids and e['label'] not in s:
                edata['label'] = e['label']
                s.add(e['label'])
                if 'clean' in e:
                    edata['data'] = e['clean']['_content']
                else:
                    edata['data'] = e['raw']['_content']
                elist.append(edata);    
    photo['exif'] = elist

    r2 = requests.get('https://api.flickr.com/services/rest/?' +
        'method=flickr.photos.geo.getLocation&photo_id=' + id +
        '&api_key=4e37767c7f7d8bc0d9399aae58a5bb3f&format=json')
    location = json.loads(r2.text[14:-1])
    if 'location' in location['photo']:
        photo['latitude'] = location['photo']['location']['latitude']
        photo['longitude'] = location['photo']['location']['longitude']
    else:
        photo['latitude'] = 'x'
        photo['longitude'] = 'y'

# Create your views here.
def index (request):
    term = request.GET.get('text', '')
    r = requests.get('https://api.flickr.com/services/rest/?' +
        'method=flickr.photos.search&sort=relevance&has_geo=1&per_page=25' +
        '&api_key=4e37767c7f7d8bc0d9399aae58a5bb3f&format=json&text=' + term)
    
    text = r.text[14:-1]
    info = json.loads(text)
    photos = info['photos']['photo']
    response = {}
    photolist = []
    threads = []
    for p in photos:
        photo = {};
        photo['id'] = p['id']
        photo['server'] = p['server']
        photo['user'] = p['owner']
        photo['secret'] = p['secret']
        photo['title'] = p['title']
        t = threading.Thread(target=get_exif
                             , args=(p['id'],p['secret'], photo,))
        threads.append(t)
        t.start()
        photolist.append(photo)
    for t in threads:
        t.join();
    return HttpResponse(json.dumps(photolist))
