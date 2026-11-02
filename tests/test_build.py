import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', REPO / 'scripts/build.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)

class ContentBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.old_root = builder.ROOT
        builder.ROOT = self.root
        for folder in ['content/collections','content/stories','media','assets','templates']:
            (self.root / folder).mkdir(parents=True)
        shutil.copytree(REPO / 'templates', self.root / 'templates', dirs_exist_ok=True)
        shutil.copytree(REPO / 'assets', self.root / 'assets', dirs_exist_ok=True)
        Image.new('RGB', (1200,800), 'red').save(self.root / 'media/event.jpg')
        Image.new('RGB', (900,900), 'blue').save(self.root / 'media/nature.jpg')
        self.site = {'name':'Photographer','email':'hello@example.com','headline':'People and nature','bio':'A biography','site_url':'https://example.com','instagram':'','facebook':'','hero_event_collection':'event','hero_nature_collection':'nature','web3forms_access_key':'00000000-0000-0000-0000-000000000000'}
        self.write('content/site.json', self.site)
        for name,kind,category in [('event','event','People & events'),('nature','nature','Birds')]:
            self.write('content/collections/'+name+'.json', {'title':name,'kind':kind,'category':category,'published':True,'photos':[{'image':'/media/'+name+'.jpg','alt':'A '+name+' photograph','highlight':True}]})
    def tearDown(self):
        builder.ROOT = self.old_root
        self.tmp.cleanup()
    def write(self,path,obj):
        (self.root/path).write_text(json.dumps(obj))
    def run_build(self):
        return builder.build(self.root/'_site')
    def test_original_dimensions_and_both_sections_survive(self):
        result = self.run_build()
        self.assertEqual(result['collections'],2)
        page=(self.root/'_site/index.html').read_text()
        self.assertIn('id="people"',page)
        self.assertIn('id="nature"',page)
        self.assertIn('width="1200" height="800"',page)
        data=json.loads((self.root/'_site/assets/data.js').read_text().split('=',1)[1].rstrip(';'))
        self.assertIn([900,900],data['sizes'].values())
    def test_draft_content_and_unreferenced_uploads_are_not_published(self):
        self.write('content/stories/private-draft.json',{'title':'DO_NOT_PUBLISH','published':False,'body':'PRIVATE_DRAFT'})
        Image.new('RGB',(50,50)).save(self.root/'media/unreferenced.jpg')
        result=self.run_build()
        self.assertEqual(result['stories'],0)
        self.assertEqual(result['images'],2)
        self.assertNotIn('PRIVATE_DRAFT',(self.root/'_site/index.html').read_text())
        self.assertFalse((self.root/'_site/media').exists())
        self.assertFalse((self.root/'_site/content').exists())
    def test_published_story_is_escaped_and_linked_to_photo(self):
        self.write('content/stories/encounter.json',{'title':'An encounter','published':True,'date':'2026-11-01','cover':'/media/nature.jpg','body':'First paragraph.\n\n<script>alert(1)</script>','photos':[]})
        self.run_build()
        story=(self.root/'_site/stories/encounter/index.html').read_text()
        self.assertIn('&lt;script&gt;',story)
        self.assertNotIn('<script>alert',story)
        self.assertIn('stories/encounter/',(self.root/'_site/assets/data.js').read_text())
    def test_complete_archive_and_empty_stories_are_always_reachable(self):
        self.run_build()
        page=(self.root/'_site/index.html').read_text()
        self.assertIn('href="work/"',page)
        self.assertIn('href="stories/"',page)
        self.assertTrue((self.root/'_site/work/index.html').exists())
        stories=(self.root/'_site/stories/index.html').read_text()
        self.assertIn('No stories have been published yet',stories)
        self.assertNotIn('first-field-note',stories)

    def test_slideshow_has_unique_images_and_both_disciplines(self):
        self.run_build()
        data=json.loads((self.root/'_site/assets/data.js').read_text().split('=',1)[1].rstrip(';'))
        slides=data['slides']
        self.assertEqual({slide['kind'] for slide in slides},{'event','nature'})
        self.assertEqual(len(slides),len({slide['image'] for slide in slides}))
        self.assertEqual(len(data['albums']['All']['all']),2)

    def test_published_story_does_not_repeat_cover(self):
        self.write('content/stories/encounter.json',{'title':'Encounter','published':True,'cover':'/media/nature.jpg','body':'A field note.','photos':[{'image':'/media/nature.jpg','alt':'The same cover'}]})
        self.run_build()
        story=(self.root/'_site/stories/encounter/index.html').read_text()
        self.assertEqual(story.count('<img '),1)

    def test_image_cache_does_not_reencode_unchanged_sources(self):
        self.run_build()
        before={p.name:p.stat().st_mtime_ns for p in (self.root/'.cache/images').glob('*.webp')}
        self.run_build()
        after={p.name:p.stat().st_mtime_ns for p in (self.root/'.cache/images').glob('*.webp')}
        self.assertEqual(before,after)

    def test_built_pages_have_no_unresolved_template_tokens(self):
        self.run_build()
        for page in (self.root/'_site').rglob('*.html'):
            self.assertNotIn('{{',page.read_text())

    def test_content_is_preserved_in_external_manifest_and_assets_are_versioned(self):
        self.site['name']='A < B & C'
        self.write('content/site.json',self.site)
        self.run_build()
        data=json.loads((self.root/'_site/assets/data.js').read_text().split('=',1)[1].rstrip(';'))
        self.assertEqual(data['settings']['name'],'A < B & C')
        self.assertIn('assets/gallery.js?v=',(self.root/'_site/index.html').read_text())
        self.assertIn('../assets/site.css?v=',(self.root/'_site/work/index.html').read_text())
        self.assertIn('<img ',(self.root/'_site/work/index.html').read_text())

    def test_editorial_showcase_and_social_icons_replace_player_chrome(self):
        self.run_build()
        page=(self.root/'_site/index.html').read_text()
        self.assertIn('id="showcaseRail"',page)
        self.assertNotIn('slidePlay',page)
        self.assertIn('id="contactForm"',page)
        self.assertIn('aria-label="Email Photographer"',page)
        self.assertIn('<svg ',page)
        for built in (self.root/'_site').rglob('*.html'):
            self.assertNotIn('↗',built.read_text())

    def test_clean_archive_and_homepage_keep_stories_on_separate_page(self):
        self.write('content/stories/note.json',{'title':'A real field note','published':True,'cover':'/media/nature.jpg','body':'The owner’s story - with a normal dash.'})
        self.run_build()
        home=(self.root/'_site/index.html').read_text()
        work=(self.root/'_site/work/index.html').read_text()
        self.assertNotIn('photoSearch',work)
        self.assertNotIn('Search captions',work)
        self.assertNotIn('image-caption',work)
        self.assertNotIn('id="natureAlbum"',home)
        self.assertNotIn('id="stories"',home)
        self.assertIn('href="stories/"',home)
        self.assertNotIn('A real field note',home)
        self.assertIn('A real field note',(self.root/'_site/stories/index.html').read_text())
        data=json.loads((self.root/'_site/assets/data.js').read_text().split('=',1)[1].rstrip(';'))
        self.assertEqual(data['images'][data['albums']['All']['all'][0]]['category'],'People & events')

    def test_contact_form_and_favicons_are_built_for_project_subpaths(self):
        self.run_build()
        home=(self.root/'_site/index.html').read_text()
        self.assertIn('action="https://api.web3forms.com/submit" method="POST"',home)
        self.assertIn('name="access_key" value="00000000-0000-0000-0000-000000000000"',home)
        self.assertIn('type="email" name="email"',home)
        self.assertIn('aria-live="polite"',home)
        self.assertIn('assets/contact.js?v=',home)
        for page in (self.root/'_site').rglob('*.html'):
            self.assertIn('rel="icon"',page.read_text())
            self.assertNotIn(' — ',page.read_text())
        self.assertTrue((self.root/'_site/assets/favicon.svg').exists())

    def test_outside_media_path_is_rejected(self):
        with self.assertRaises(ValueError):builder.safe_image_path('../secret.jpg')
        with self.assertRaises(ValueError):builder.safe_image_path('/etc/passwd')
    def test_malformed_published_collection_fails_without_replacing_good_build(self):
        self.run_build()
        before=(self.root/'_site/index.html').read_bytes()
        self.write('content/collections/broken.json',{'title':'Broken','kind':'event','published':True,'photos':[]})
        with self.assertRaises(ValueError):self.run_build()
        self.assertEqual(before,(self.root/'_site/index.html').read_bytes())
    def test_source_image_metadata_is_not_exported(self):
        self.run_build()
        for path in (self.root/'_site/photos').glob('*.webp'):
            with Image.open(path) as im:self.assertFalse(im.getexif())

if __name__=='__main__':unittest.main()
