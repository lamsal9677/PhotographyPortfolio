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
from urllib.parse import urlsplit
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
        if c['kind'] == 'event':
            c['category'] = 'People & events'
        if c['kind'] == 'nature' and c.get('category') not in CATEGORIES:
            raise ValueError(f'{c["slug"]}: choose a supported nature category')
        if not isinstance(c.get('order', 0), (int, float)):
            raise ValueError(f'{c["slug"]}: order must be a number')
        if not isinstance(c.get('photos'), list) or not c['photos']:
            raise ValueError(f'{c["slug"]}: add at least one photograph')
    collections.sort(key=lambda c: (c.get('order', 0), c['title']))
    images, descriptions, sizes, source_ids = {}, {}, {}, {}
    cache = ROOT / '.cache' / 'images'
    cache.mkdir(parents=True, exist_ok=True)
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
        # Include processing settings in the cache key; process each source once.
        digest = hashlib.sha256(path.read_bytes() + b'webp-2000-800-q88-q82-v2').hexdigest()[:20]
        id = 'p-' + digest
        if id not in images:
            full_cache = cache / (id + '.webp')
            small_cache = cache / (id + '-small.webp')
            if not full_cache.exists() or not small_cache.exists():
                with Image.open(path) as original:
                    im = ImageOps.exif_transpose(original).convert('RGB')
                    im.thumbnail((2000, 2000))
                    im.save(full_cache, 'WEBP', quality=88)
                    im.thumbnail((800, 800))
                    im.save(small_cache, 'WEBP', quality=82)
            with Image.open(full_cache) as full_image:
                w, h = full_image.size
            with Image.open(small_cache) as small_image:
                sw = small_image.width
            shutil.copy2(full_cache, stage / 'photos' / full_cache.name)
            shutil.copy2(small_cache, stage / 'photos' / small_cache.name)
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
            when = when[:10]
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

    def button(id, key, title, caption, priority=False, prefix=''):
        w, h = sizes[id]
        return f'<button class="photo-item" data-open-album="{e(key)}" aria-label="Explore {e(title)}" style="flex-grow:{w/h};--ratio:{w}/{h}">'+img(id, priority, prefix)+caption+'</button>'

    slides, hero_ids = [], set()
    for kind in ['event', 'nature']:
        requested = settings.get('hero_' + kind + '_collection')
        key = requested
        if key not in albums or not albums[key]['all']:
            key = next((k for k, a in albums.items() if a['kind'] == kind and a['all']), None)
        if not key:
            continue
        a = albums[key]
        value = settings.get('hero_' + kind + '_image') if key == requested else None
        id = process(value, a.get('category', '')) if value else a.get('cover', a['all'][0])
        if id not in a['all']:
            raise ValueError(f'Hero {kind} image must belong to its selected collection')
        slides.append({'image': id, 'collection': key, 'title': a['title'], 'kind': kind})
        hero_ids.add(id)
    # Mix event and nature work without repeating a frame within the slideshow.
    event_queue = [c for c in collections if c['kind'] == 'event' and c['slug'] != settings.get('hero_event_collection')]
    nature_priority = {'Wildlife':0, 'Birds':1, 'Small worlds':2, 'Landscapes':3}
    nature_queue = sorted([c for c in collections if c['kind'] == 'nature'], key=lambda c:nature_priority.get(c.get('category'),4))
    showcase = []
    while nature_queue or event_queue:
        if nature_queue:showcase.append(nature_queue.pop(0))
        if event_queue:showcase.append(event_queue.pop(0))
    for c in showcase:
        a = albums[c['slug']]
        for id in [a['cover']] + a['featured']:
            if id not in hero_ids:
                slides.append({'image':id,'collection':c['slug'],'title':a['title'],'kind':a['kind']})
                hero_ids.add(id)
                break
        if len(slides) >= 7:
            break
    if not slides:
        raise ValueError('Publish at least one collection to feature in the portfolio')
    # Lead with a strong sense of place, then reveal people and wildlife.
    if len(slides) > 1 and slides[0]['kind'] == 'event' and slides[1]['kind'] == 'nature':
        slides[0], slides[1] = slides[1], slides[0]
    first_slide = slides[0]
    hero = ''
    for index,slide in enumerate(slides + slides):
        id = slide['image']
        w,h=sizes[id]
        clone = index >= len(slides)
        hero += '<button class="showcase-frame" data-showcase-index="'+str(index)+'" data-collection="'+e(slide['collection'])+'" aria-label="Open '+e(slide['title'])+' collection" '+('aria-hidden="true" tabindex="-1" ' if clone else '')+'style="--frame-width:'+str(w/h)+'">'+img(id,index==0)+'</button>'
    # Choose homepage highlights outside the opening sequence when alternatives exist.
    used_home = set(hero_ids)
    for cat in categories:
        group = albums[cat]
        choices = [id for id in group['featured'] + group['all'] if id not in used_home]
        if choices:
            used_home.add(choices[0])
            albums['Selected']['featured'][categories.index(cat)] = choices[0]
    events = ''.join(button(albums[k]['cover'], k, albums[k]['title'], f'<h3>{e(albums[k]["title"])}</h3><div class="image-caption"><b>{len(albums[k]["featured"])} highlights</b><span>{len(albums[k]["all"])} photographs</span></div>') for k in event_keys)
    tabs = ''.join(f'<button class="{("active" if i == 0 else "")}" aria-pressed="{str(i == 0).lower()}" data-category="{e(cat)}">{e(cat)}</button>' for i, cat in enumerate(['Selected'] + categories))
    cards = ''.join(f'<a class="story-card" href="{s["url"]}">{img(s["coverId"])}<div class="story-meta">{e(s.get("category", "Field notes"))}</div><h3>{e(s["title"])}</h3><p>{e(s.get("summary", ""))}</p></a>' for s in story_records)
    story_section = '<section id="stories"><div class="sectionhead"><h2>Stories behind the photographs</h2><a href="stories/">All stories</a></div><div class="story-grid">'+cards+'</div></section>' if cards else ''
    all_ids = list(images)
    albums['All'] = {'title':'All photographs','kind':'all','type':'The complete portfolio','description':'Browse every published photograph.','all':all_ids,'featured':all_ids}
    dataset = json.dumps({'slides': slides, 'albums': albums, 'sizes': sizes, 'descriptions': descriptions, 'images': images, 'settings': settings}, ensure_ascii=False).replace('<', chr(92)+'u003c').replace(chr(0x2028), chr(92)+'u2028').replace(chr(0x2029), chr(92)+'u2029')
    first = next(iter(images), None)
    icon_paths = {
        'instagram':'<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17.5" cy="6.5" r=".8" fill="currentColor" stroke="none"/>',
        'facebook':'<path d="M14 21v-8h3l.5-4H14V7c0-1.2.4-2 2-2h2V1.5C17.2 1.2 16.1 1 15 1c-3.2 0-5 1.9-5 5v3H7v4h3v8Z" fill="currentColor" stroke="none"/>',
        'email':'<rect x="3" y="5" width="18" height="14" rx="3"/><path d="m4 7 8 6 8-6"/>'
    }
    def icon(name):
        return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false">'+icon_paths[name]+'</svg>'
    social_icons = ''.join('<a class="social-icon" href="'+e(href)+'" aria-label="'+label+'" title="'+label+'"'+(' target="_blank" rel="noopener"' if name != 'email' else '')+'>'+icon(name)+'</a>' for name,label,href in [('instagram','Instagram',settings['instagram']),('facebook','Facebook',settings['facebook']),('email','Email '+settings['name'],'mailto:'+settings['email'])] if href)
    mail_cta = '<a class="contact-cta" href="mailto:'+e(settings['email'])+'" aria-label="Email '+e(settings['name'])+'">'+icon('email')+'<span>Let’s talk</span></a>'
    replacements = {'NAME':e(settings['name']), 'EMAIL':e(settings['email']), 'HEADLINE':'<br>'.join(e(settings['headline']).splitlines()),
                    'BIO':e(settings['bio']), 'INSTAGRAM':e(settings['instagram']), 'FACEBOOK':e(settings['facebook']),
                    'HERO':hero, 'EVENTS':events, 'TABS':tabs, 'STORIES':story_section, 'STORY_NAV':'<a href="#stories">Field notes</a>' if cards else '',
                    'OG_IMAGE':e(settings['site_url']+'/'+images[first_slide['image']]['src']) if first else '', 'YEAR':str(date.today().year), 'DATA':dataset, 'SOCIAL_ICONS':social_icons, 'MAIL_CTA':mail_cta, 'DIALOGS':(ROOT / 'templates/dialogs.html').read_text().replace('{{NAME}}',e(settings['name']))}
    template = (ROOT / 'templates/index.html').read_text()
    output = re.sub(r'\{\{([A-Z_]+)\}\}', lambda m: replacements[m[1]], template)
    (stage / 'index.html').write_text(output)
    (stage / 'assets/data.js').write_text('window.PORTFOLIO='+dataset+';')
    shutil.copytree(ROOT / 'assets', stage / 'assets', dirs_exist_ok=True)
    for f in ['.nojekyll', '_headers']:
        if (ROOT / f).exists():shutil.copy2(ROOT / f, stage / f)
    def nav(prefix=''):
        return '<header class="nav"><a class="brand" href="'+prefix+'">'+e(settings['name'])+'<span>Photography</span></a><nav class="navlinks" aria-label="Main navigation"><a href="'+prefix+'work/">All work</a><a href="'+prefix+'#people">People & events</a><a href="'+prefix+'stories/">Stories</a><a href="'+prefix+'#about">About & contact</a></nav></header>'
    def page(title, body, prefix='../', scripts='', data=False):
        return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600&display=swap" rel="stylesheet"><meta name="theme-color" content="#dfe2da"><title>'+e(title)+' — '+e(settings['name'])+'</title><meta name="description" content="Photography, events, wildlife and stories by '+e(settings['name'])+'"><link rel="stylesheet" href="'+prefix+'assets/site.css"></head><body>'+nav(prefix)+body+'<footer><span>© '+str(date.today().year)+' '+e(settings['name'])+'</span><a href="'+prefix+'#about">Get in touch</a></footer>'+('<script src="'+prefix+'assets/data.js"></script>' if data else '')+scripts+'</body></html>'
    dialogs = (ROOT / 'templates/dialogs.html').read_text().replace('{{NAME}}', e(settings['name']))
    work_dir = stage / 'work';work_dir.mkdir()
    work_filters = ''.join('<button data-work-filter="'+e(cat)+'" aria-pressed="'+str(i==0).lower()+'" class="'+('active' if i==0 else '')+'">'+e('Nature' if cat == 'nature' else cat)+'</button>' for i,cat in enumerate(['All','People & events','nature']+categories))
    all_rows = ''
    for index in range(0,len(all_ids),2):
        pair = all_ids[index:index+2]
        all_rows += '<div class="photo-row">' + ''.join(button(id,'All',descriptions[id],'<div class="image-caption"><b>'+e(images[id]['category'] or 'Photograph')+'</b></div>',prefix='../') for id in pair) + '</div>'
    work_body = '<main class="archive-page"><div class="page-heading"><span class="eyebrow">The complete portfolio</span><h1>All photographs.</h1><p>People, places, and the natural world. Every published frame, in one place.</p></div><div class="archive-tools"><div class="tabs" aria-label="Filter photographs">'+work_filters+'</div><label class="search-label">Search photographs<input id="photoSearch" type="search" placeholder="Search captions and descriptions" autocomplete="off"></label></div><div class="results-bar"><p id="workCount" role="status">'+str(len(all_ids))+' photographs</p><button id="resetFilters" class="text-button">Reset filters</button></div><div class="nature-rows" id="allPhotos">'+all_rows+'</div><p class="empty-state" id="noResults" hidden>No photographs match. Try another search or reset the filters.</p></main>'+dialogs
    (work_dir / 'index.html').write_text(page('All photographs',work_body,scripts='<script src="../assets/gallery.js" defer></script>',data=True))
    story_dir=stage/'stories';story_dir.mkdir(exist_ok=True)
    story_cards=''.join('<a class="story-card" href="'+e(s['slug'])+'/">'+img(s['coverId'], prefix='../')+'<div class="story-meta">'+e(s.get('category','Field notes'))+'</div><h2>'+e(s['title'])+'</h2><p>'+e(s.get('summary',''))+'</p></a>' for s in story_records)
    empty='<div class="empty-story"><h2>The photographs are here.<br>Their stories will follow.</h2><p>No stories have been published yet. Come back for field notes, encounters, and the moments behind the frame.</p><a class="button-link" href="../work/">Explore the photographs</a></div>'
    (story_dir/'index.html').write_text(page('Stories','<main class="archive-page"><div class="page-heading"><span class="eyebrow">Field notes & encounters</span><h1>Behind the frame.</h1><p>Stories from nature, travel, and time spent photographing people.</p></div>'+('<div class="story-grid">'+story_cards+'</div>' if story_records else empty)+'</main>'))
    for s in story_records:
        folder = story_dir / s['slug'];folder.mkdir(parents=True)
        meta = ' · '.join(e(x) for x in [s['date'], s['location']] if x)
        # The opening photograph is not repeated again in the story gallery.
        figures = ''.join('<figure>'+img(id, prefix='../../')+'<figcaption>'+e(images[id]['caption'])+'</figcaption></figure>' for id in dict.fromkeys(s['gallery']) if id != s['coverId'])
        article='<main class="story-article"><a class="backlink" href="../">All stories</a><div class="story-meta">'+e(s.get('category','Field notes'))+'</div><h1>'+e(s['title'])+'</h1><div class="story-meta">'+meta+'</div>'+img(s['coverId'],True,'../../')+'<div class="prose">'+paragraphs(s['body'])+'</div>'+figures+'<div class="story-end"><a href="../../work/">Explore all photographs</a><a href="mailto:'+e(settings['email'])+'">Work with me</a></div></main>'
        (folder/'index.html').write_text(page(s['title'],article,prefix='../../'))
    # Bust browser caches when any frontend asset or content manifest changes.
    versions = {name:hashlib.sha256((stage/'assets'/name).read_bytes()).hexdigest()[:12] for name in ['site.css','gallery.js','data.js']}
    for page_path in stage.rglob('*.html'):
        page_content=page_path.read_text()
        for name,version in versions.items():
            page_content=page_content.replace('assets/'+name+'"','assets/'+name+'?v='+version+'"')
        page_path.write_text(page_content)
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
