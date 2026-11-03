import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'tools'/f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
patch, verify = module('patch'), module('verify_fork')

class ForkContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write('AndroidManifest.xml', '<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="org.smarttube.stable"><application/></manifest>')
        self.write('res/values/arrays.xml', '<resources><string-array name="update_urls"><item>https://upstream.invalid</item></string-array></resources>')
        self.write('apktool.yml', "versionCode: '3268'\n")
        self.write('smali/NetworkData.smali', '.class public Lcom/liskovsoft/smartyoutubetv2/common/prefs/NetworkData;\n.method public isConscryptEnabled()Z\n    .locals 1\n    const/4 v0, 0x0\n    return v0\n.end method\n')
        self.write('smali/MotherActivity.smali', '.class public Lcom/liskovsoft/smartyoutubetv2/common/misc/MotherActivity;\n.method private initEdgeSlide()V\n    const/16 v1, 0x15\n    invoke-static {p0}, Lcom/r0adkll/slidr/Slidr;->attach(Landroid/app/Activity;)V\n.end method\n')
        self.write('smali/SliderPanel.smali', '.class public Lcom/r0adkll/slidr/widget/SliderPanel;\n.super Landroid/widget/FrameLayout;\n.field private decorView:Landroid/view/View;\n.field private dragHelper:Lcom/r0adkll/slidr/util/ViewDragHelper;\n')
        patch.patch_get_tasks(self.root)
        patch.patch_conscrypt(self.root)
        patch.patch_update_urls(self.root, verify.UPDATE_URL)
        patch.patch_version_code(self.root, 326851)
        patch.patch_edge_slide(self.root)
        patch.patch_slider_layout(self.root)
    def write(self, path, text):
        p = self.root/path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    def test_compatibility_patches_pass_together(self):
        verify.check_decoded(self.root, verify.UPDATE_URL)
    def test_reintroduced_regulation_in_any_dex_is_rejected(self):
        for marker in verify.MARKERS:
            with self.subTest(marker=marker):
                self.write('smali_classes3/new/Helper.smali', marker)
                with self.assertRaisesRegex(ValueError, 'Regulation marker'):
                    verify.check_decoded(self.root, verify.UPDATE_URL)
    def test_regulation_permission_is_rejected(self):
        patch.add_permission(self.root, 'com.hkmc.permission.AUTOMOTIVE_REGULATION')
        with self.assertRaisesRegex(ValueError, 'Regulation marker'):
            verify.check_decoded(self.root, verify.UPDATE_URL)
    def test_wrong_feed_is_rejected(self):
        patch.patch_update_urls(self.root, 'https://github.com/KramerTech/gen5-SmartTube/releases/latest/download/smarttube-gen5w.json')
        with self.assertRaisesRegex(ValueError, 'update feed'):
            verify.check_decoded(self.root, verify.UPDATE_URL)
    def test_missing_compatibility_fix_is_rejected(self):
        p=self.root/'smali/NetworkData.smali'
        p.write_text(p.read_text().replace('const/4 v0, 0x1', 'const/4 v0, 0x0'))
        with self.assertRaisesRegex(ValueError, 'Conscrypt'):
            verify.check_decoded(self.root, verify.UPDATE_URL)
    def test_changed_upstream_layout_stops_patching(self):
        with self.assertRaises(SystemExit):
            patch.patch_edge_slide(self.root)
    def test_release_source_contract(self):
        verify.check_source(ROOT)

if __name__ == '__main__':
    unittest.main()
