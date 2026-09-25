"""PubMed abstracts/titles with inline markup must not be truncated.

Regression: the parser read `element.text`, which stops at the first child element,
so "HbA<sub>1c</sub> was reduced by 2.0%" became "HbA" and everything after it was
silently lost — including every effect size in the trial abstracts of a drug whose
whole literature reports HbA1c (found 2026-09-25 on a tirzepatide run).
"""

from __future__ import annotations

from litreview.clients.pubmed import PubMedClient

XML = """<?xml version="1.0"?>
<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>1</PMID>
<Article>
  <Journal><Title>Test J</Title><ISSN>1234-5678</ISSN>
    <JournalIssue><PubDate><Year>2021</Year></PubDate></JournalIssue></Journal>
  <ArticleTitle>Effect on HbA<sub>1c</sub> of <i>tirzepatide</i> in T2D</ArticleTitle>
  <Abstract>
    <AbstractText Label="RESULTS">Mean HbA<sub>1c</sub> fell by 2.01% (95% CI -2.1 to -1.9) at 40 weeks, and weight fell by 7.6 kg.</AbstractText>
    <AbstractText Label="CONCLUSION">Doses were 5 mg, 10 mg and 15 mg.</AbstractText>
  </Abstract>
</Article></MedlineCitation></PubmedArticle></PubmedArticleSet>"""


def _parse():
    arts = PubMedClient._parse_articles_xml(XML)
    assert len(arts) == 1
    return arts[0]


def test_abstract_keeps_text_after_inline_subscript():
    ab = _parse()["abstract"]
    assert "HbA1c fell by 2.01%" in ab
    assert "7.6 kg" in ab  # text after the markup survived
    assert "15 mg" in ab   # second AbstractText intact


def test_title_keeps_text_around_inline_markup():
    assert _parse()["title"] == "Effect on HbA1c of tirzepatide in T2D"
