#!/usr/bin/env python3
"""Build a static portfolio from CMS-editable JSON and image files."""
import argparse
import hashlib
import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit, quote
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
Image.MAX_IMAGE_PIXELS = 60_000_000
CATEGORIES = ['Landscapes', 'Birds', 'Wildlife', 'Small worlds']

def text(value, label, required=False):
    if value is None and not required:
        return ''
    if not isinstance(value, str):
        raise ValueError(f'{label}: expected text')
    if required and not value.strip():
        raise ValueError(f'{label}: cannot be empty')
    return value.strip()

def load(path):
    obj = json.loads(path.read_text())
    if not isinstance(obj, dict):
        raise ValueError(f'{path}: expected a JSON object')
    return obj

def safe_image_path(value):
    value = text(value, 'Image path', True).lstrip('/')
    path = (ROOT / value).resolve()
    if not path.is_relative_to((ROOT / 'media').resolve()):
        raise ValueError(f'Image must be inside media/: {value}')
    if path.suffix.lower() not in {'.jpg', '.jpeg', '.png', '.webp'} or not path.is_file():
        raise ValueError(f'Missing or unsupported image: {value}')
    return path

def read_entries(folder, include_drafts=False):
    entries = []
    for path in sorted((ROOT / 'content' / folder).glob('*.json')):
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', path.stem):
            raise ValueError(f'Use lowercase, hyphenated filenames: {path}')
        obj = load(path)
        if not isinstance(obj.get('published', False), bool):
            raise ValueError(f'{path}: published must be true or false')
        if not obj.get('published') and not include_drafts:
            continue
        obj['slug'] = path.stem
        obj['title'] = text(obj.get('title'), f'{path}: title', True)
        entries.append(obj)
    return entries

def e(value):
    return html.escape(str(value), quote=True)

def paragraphs(value):
    # Plain-text story paragraphs deliberately never execute embedded HTML.
    return ''.join('<p>' + e(p).replace('\n', '<br>') + '</p>' for p in re.split(r'\n\s*\n', value.strip()) if p.strip())

def build(destination, include_drafts=False):
    destination = destination.resolve()
    if destination == ROOT or not destination.is_relative_to(ROOT):
        raise ValueError('Output must be a subdirectory of the repository')
    if destination.parts[len(ROOT.parts)] in {'content', 'media', 'assets', 'scripts', 'templates', '.git', '.github'}:
        raise ValueError('Output cannot overwrite source directories')
    settings = load(ROOT / 'content/site.json')
    for key in ['name', 'email', 'headline', 'bio', 'site_url']:
        settings[key] = text(settings.get(key), f'Site settings: {key}', True)
    if not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+', settings['email']):
        raise ValueError('Site email must be an email address')
    for key in ['site_url', 'instagram', 'facebook']:
        url = text(settings.get(key, ''), key, key == 'site_url')
        if url and (urlsplit(url).scheme != 'https' or not urlsplit(url).netloc):
            raise ValueError(f'{key}: use a complete https:// URL')
        settings[key] = url.rstrip('/')
    collections = read_entries('collections', include_drafts)
    stories = read_entries('stories', include_drafts)
    for c in collections:
        if c.get('kind') not in {'event', 'nature'}:
            raise ValueError(f'{c["slug"]}: choose event or nature')
        if c['kind'] == 'nature' and c.get('category') not in CATEGORIES:
            raise ValueError(f'{c["slug"]}: choose a supported nature category')
        if not isinstance(c.get('order', 0), (int, float)):
            raise ValueError(f'{c["slug"]}: order must be a number')
        if not isinstance(c.get('photos'), list) or not c['photos']:
            raise ValueError(f'{c["slug"]}: add at least one photograph')
    collections.sort(key=lambda c: (c.get('order', 0), c['title']))
    images, descriptions, sizes, source_ids = {}, {}, {}, {}
    # Build atomically: a validation failure leaves the last successful build intact.
    stage = ROOT / (destination.name + '-building')
    if stage.exists():
        shutil.rmtree(stage)
    (stage / 'photos').mkdir(parents=True)
    (stage / 'assets').mkdir()

    def process(value, category='', alt='', caption=''):
        path = safe_image_path(value)
        source = path.relative_to(ROOT).as_posix()
        if source in source_ids:
            id = source_ids[source]
            if alt:
                descriptions[id] = text(alt, 'Image description', True)
            if caption:
                images[id]['caption'] = text(caption, 'Image caption')
            return id
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:20]
        id = 'p-' + digest
        if id not in images:
            with Image.open(path) as original:
                im = ImageOps.exif_transpose(original).convert('RGB')
                im.thumbnail((2000, 2000))
                w, h = im.size
                im.save(stage / 'photos' / (id + '.webp'), 'WEBP', quality=88)
                im.thumbnail((800, 800))
                sw = im.width
                im.save(stage / 'photos' / (id + '-small.webp'), 'WEBP', quality=82)
            sizes[id] = [w, h]
            images[id] = {'src': f'photos/{id}.webp', 'small': f'photos/{id}-small.webp', 'smallWidth': sw,
                          'category': category, 'caption': text(caption, 'Caption'), 'story': ''}
            descriptions[id] = text(alt, 'Image description') or 'Photograph by ' + settings['name']
        source_ids[source] = id
        return id

    albums, event_keys = {}, []
    for c in collections:
        ids, featured = [], []
        for p in c['photos']:
            if not isinstance(p, dict):
                raise ValueError(f'{c["slug"]}: each photograph must be an object')
            alt = text(p.get('alt', ''), f'{c["slug"]}: image description', True)
            if not isinstance(p.get('highlight', False), bool):
                raise ValueError('Photo highlight must be true or false')
            id = process(p.get('image'), c.get('category', ''), alt, p.get('caption', ''))
            if id not in ids:
                ids.append(id)
            if p.get('highlight') and id not in featured:
                featured.append(id)
        cover = process(c.get('cover') or c['photos'][0]['image'], c.get('category', ''))
        if cover not in ids:
            raise ValueError(f'{c["slug"]}: cover must also be in the collection photos')
        a = {'title': c['title'], 'kind': c['kind'], 'category': c.get('category', ''),
             'type': 'People & events' if c['kind'] == 'event' else 'The natural world',
             'description': text(c.get('description', ''), 'Collection description'),
             'all': ids, 'featured': featured or ids[:3], 'cover': cover}
        albums[c['slug']] = a
        if c['kind'] == 'event':
            event_keys.append(c['slug'])
    categories = []
    for cat in CATEGORIES:
        group = [a for a in list(albums.values()) if a['kind'] == 'nature' and a.get('category') == cat]
        if not group:
            continue
        categories.append(cat)
        albums[cat] = {'title': cat, 'kind': 'nature', 'type': 'The natural world',
                       'description': '\n'.join(a['description'] for a in group if a['description']),
                       'all': list(dict.fromkeys(id for a in group for id in a['all'])),
                       'featured': list(dict.fromkeys(id for a in group for id in a['featured']))[:4]}
    all_nature = list(dict.fromkeys(id for cat in categories for id in albums[cat]['all']))
    chosen = [albums[cat]['featured'][0] for cat in categories]
    albums['Selected'] = {'title': 'The natural world', 'kind': 'nature', 'type': 'Selected photographs',
                          'description': 'Selected landscapes, wildlife, birds, and small details.',
                          'all': all_nature, 'featured': chosen}

    story_records = []
    for story in stories:
        body = text(story.get('body', ''), f'{story["slug"]}: story', True)
        cover = process(story.get('cover'), story.get('category', ''))
        location = text(story.get('location', ''), 'Story location')
        when = text(story.get('date', ''), 'Story date')
        if when:
            date.fromisoformat(when[:10])
        url = f'stories/{story["slug"]}/'
        gallery = []
        for p in (story.get('photos') or []):
            id = process(p.get('image'), story.get('category', ''), text(p.get('alt', ''), 'Story photo description', True), p.get('caption', ''))
            gallery.append(id)
            images[id]['story'] = url
        images[cover]['story'] = url
        story_records.append({**story, 'coverId': cover, 'body': body, 'url': url, 'location': location, 'date': when, 'gallery': gallery})
    story_records.sort(key=lambda s: s['date'], reverse=True)

    def img(id, priority=False, prefix=''):
        p = images[id];w, h = sizes[id]
        return f'<img src="{prefix}{p["src"]}" srcset="{prefix}{p["small"]} {p["smallWidth"]}w, {prefix}{p["src"]} {w}w" sizes="(max-width:600px) calc(100vw - 40px), 60vw" width="{w}" height="{h}" alt="{e(descriptions[id])}" '+('fetchpriority="high"' if priority else 'loading="lazy"')+' decoding="async">'

    def button(id, key, title, caption, priority=False):
        w, h = sizes[id]
        return f'<button class="photo-item" data-open-album="{e(key)}" aria-label="Explore {e(title)}" style="flex-grow:{w/h};--ratio:{w}/{h}">'+img(id, priority)+caption+'</button>'

    hero = ''
    for kind in ['event', 'nature']:
        key = settings.get('hero_' + kind + '_collection')
        if key not in albums or not albums[key]['all']:
            key = next((k for k, a in albums.items() if a['kind'] == kind and a['all']), None)
        if not key:
            continue
        a = albums[key]
        value = settings.get('hero_' + kind + '_image')
        id = process(value, a.get('category', '')) if value else a.get('cover', a['all'][0])
        if id not in a['all']:
            raise ValueError(f'Hero {kind} image must belong to its selected collection')
        hero += button(id, key, a['title'], '<div class="image-caption"><b>'+('People & events' if kind == 'event' else 'Landscapes & wildlife')+'</b><span>Explore collection ↗</span></div>', True)
    events = ''.join(button(albums[k]['cover'], k, albums[k]['title'], f'<h3>{e(albums[k]["title"])}<span>↗</span></h3><div class="image-caption"><b>{len(albums[k]["featured"])} highlights</b><span>{len(albums[k]["all"])} photographs</span></div>') for k in event_keys)
    tabs = ''.join(f'<button class="{("active" if i == 0 else "")}" aria-pressed="{str(i == 0).lower()}" data-category="{e(cat)}">{e(cat)}</button>' for i, cat in enumerate(['Selected'] + categories))
    cards = ''.join(f'<a class="story-card" href="{s["url"]}">{img(s["coverId"])}<div class="story-meta">{e(s.get("category", "Field notes"))}</div><h3>{e(s["title"])}</h3><p>{e(s.get("summary", ""))}</p></a>' for s in story_records)
    story_section = '<section id="stories"><div class="sectionhead"><h2>Field notes</h2></div><div class="story-grid">'+cards+'</div></section>' if cards else ''
    dataset = json.dumps({'albums': albums, 'sizes': sizes, 'descriptions': descriptions, 'images': images, 'settings': settings}, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    first = next(iter(images), None)
    replacements = {'NAME':e(settings['name']), 'EMAIL':e(settings['email']), 'HEADLINE':'<br>'.join(e(settings['headline']).splitlines()),
                    'BIO':e(settings['bio']), 'INSTAGRAM':e(settings['instagram']), 'FACEBOOK':e(settings['facebook']),
                    'HERO':hero, 'EVENTS':events, 'TABS':tabs, 'STORIES':story_section, 'STORY_NAV':'<a href="#stories">Field notes</a>' if cards else '',
                    'OG_IMAGE':e(settings['site_url']+'/'+images[first]['src']) if first else '', 'YEAR':str(date.today().year), 'DATA':dataset}
    template = (ROOT / 'templates/index.html').read_text()
    output = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: replacements[m[1]], template)
    (stage / 'index.html').write_text(output)
    shutil.copytree(ROOT / 'assets', stage / 'assets', dirs_exist_ok=True)
    for f in ['.nojekyll', '_headers']:
        if (ROOT / f).exists():shutil.copy2(ROOT / f, stage / f)
    for s in story_records:
        folder = stage / 'stories' / s['slug'];folder.mkdir(parents=True)
        meta = ' · '.join(e(x) for x in [s['date'], s['location']] if x)
        figures = ''.join('<figure>'+img(id, prefix='../../')+'<figcaption>'+e(images[id]['caption'])+'</figcaption></figure>' for id in s['gallery'])
        page = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>'+e(s['title'])+' — '+e(settings['name'])+'</title><meta name="description" content="'+e(s.get('summary', ''))+'"><link rel="stylesheet" href="../../assets/site.css"></head><body><header class="nav"><a class="brand" href="../../">'+e(settings['name'])+'</a><nav class="navlinks"><a href="../../#people">People & events</a><a href="../../#nature">Nature</a></nav></header><main class="story-article"><a class="backlink" href="../../#stories">← Field notes</a><h1>'+e(s['title'])+'</h1><div class="story-meta">'+meta+'</div>'+img(s['coverId'], True, '../../')+'<div class="prose">'+paragraphs(s['body'])+'</div>'+figures+'<a class="email" href="mailto:'+e(settings['email'])+'">Get in touch ↗</a></main></body></html>'
        (folder / 'index.html').write_text(page)
    if destination.exists():shutil.rmtree(destination)
    stage.rename(destination)
    return {'collections':len(collections), 'images':len(images), 'stories':len(story_records), 'output':str(destination)}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='_site')
    parser.add_argument('--include-drafts', action='store_true', help='Local preview only; never use for public publishing')
    args = parser.parse_args()
    try:
        print(json.dumps(build(ROOT / args.output, args.include_drafts), indent=2))
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as error:
        raise SystemExit('Build failed: '+str(error))
