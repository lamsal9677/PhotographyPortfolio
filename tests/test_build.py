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
        shutil.copy2(REPO / 'templates/index.html', self.root / 'templates/index.html')
        Image.new('RGB', (1200,800), 'red').save(self.root / 'media/event.jpg')
        Image.new('RGB', (900,900), 'blue').save(self.root / 'media/nature.jpg')
        self.site = {'name':'Photographer','email':'hello@example.com','headline':'People and nature','bio':'A biography','site_url':'https://example.com','instagram':'','facebook':'','hero_event_collection':'event','hero_nature_collection':'nature'}
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
        self.assertIn('width="900" height="900"',page)
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
        self.assertIn('stories/encounter/',(self.root/'_site/index.html').read_text())
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
