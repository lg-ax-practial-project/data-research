import unittest
from lg_tv_crawler import extract

class ExtractionTests(unittest.TestCase):
    def test_scope_and_navigation(self):
        html='<title>[LG TV] test</title><nav>Do not collect navigation</nav><div class="view-content"><h2>TV</h2><p>'+('official guidance '*20)+'</p><dl><dt>Q. question</dt><dd>A. answer</dd></dl><script>ignore script</script></div>'
        result=extract(html,'https://www.lge.co.kr/support/solutions-1')
        self.assertNotIn('navigation',result['text'])
        self.assertNotIn('ignore script',result['text'])
        self.assertEqual(len(result['faqs']),1)
    def test_no_guessed_faq(self):
        result=extract('<title>LG TV</title><div class="view-content">'+('guide '*50)+'</div>','https://www.lge.co.kr/support/solutions-1')
        self.assertEqual(result['faqs'],[])
    def test_monitor_excluded(self):
        with self.assertRaises(ValueError): extract('<title>LG 모니터</title>','https://www.lge.co.kr/support/solutions-1')
    def test_missing_body_fails_closed(self):
        with self.assertRaises(ValueError): extract('<title>LG TV</title><div>short</div>','https://www.lge.co.kr/support/solutions-1')

    def parse(self, body, head=''):
        return extract('<title>LG TV</title>'+head+'<div class="view-content">'+('guide '*30)+body+'</div>', 'https://www.lge.co.kr/support/solutions-1')

    def test_all_pairs_in_one_dl(self):
        result=self.parse('<dl><dt>Q1</dt><dd>A1</dd><dt>Q2</dt><dd>A2</dd></dl>')
        self.assertEqual([(p['question'],p['answer']) for p in result['faqs']],[('Q1','A1'),('Q2','A2')])

    def test_unmatched_question_is_reported(self):
        self.assertTrue(self.parse('<dl><dt>Q1</dt></dl>')['extraction_issues'])

    def test_image_alt_and_blocks(self):
        result=self.parse('<h2>Step 1</h2><p>Press [<img src="/button.png" alt="Power">]</p><table><tr><td>A</td><td>B</td></tr></table>')
        self.assertIn('Power',result['text'])
        self.assertIn({'type':'tr','text':'A B','cells':['A','B']},result['content_blocks'])
        self.assertEqual(result['image_alts'][0]['url'],'https://www.lge.co.kr/button.png')

    def test_date_not_from_global_template(self):
        result=self.parse('', '<footer>2021.02.04</footer><ul class="head-infos"><li>2026.08.13</li></ul>')
        self.assertEqual(result['page_date_candidates'],['2026.08.13'])

    def test_catalog_question_answer_category(self):
        html='<title>고객 Q&A 한눈에 보기</title><section class="machine-faq__detail-content"><div class="machine-faq__item"><button class="machine-faq__title"><em class="machine-faq__category">고객지원</em><span>Q. TV repair?</span></button><div class="machine-faq__content">'+('answer '*30)+'</div></div></section>'
        result=extract(html,'https://www.lge.co.kr/story/faq/tvs-faq')
        self.assertEqual(result['faqs'][0]['question'],'Q. TV repair?')
        self.assertEqual(result['faqs'][0]['category'],'고객지원')
        self.assertEqual(result['type'],'official_tv_faq_catalog')

    def test_korean_particle_after_tv(self):
        result=extract('<title>LG TV에 소리가 안 나와요</title><div class="view-content">'+('guide '*30)+'</div>','https://www.lge.co.kr/support/solutions-1')
        self.assertIn('TV에',result['title'])

if __name__=='__main__': unittest.main()
