"""Tests for PubMed ingestion."""


from hypertrophy_rag.ingestion.pubmed import _build_query, _parse_xml

SAMPLE_XML = """<?xml version="1.0" ?>
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>12345678</PMID>
      <Article>
        <ArticleTitle>Effects of training volume on hypertrophy</ArticleTitle>
        <Abstract>
          <AbstractText>This study examined the effects of different \
training volumes on muscle hypertrophy in trained individuals.</AbstractText>
          <AbstractText Label="BACKGROUND">Resistance training volume \
is a key variable for muscle growth.</AbstractText>
        </Abstract>
        <AuthorList>
          <Author>
            <LastName>Schoenfeld</LastName>
            <ForeName>Brad J</ForeName>
          </Author>
          <Author>
            <LastName>Ogborn</LastName>
            <ForeName>Daniel</ForeName>
          </Author>
        </AuthorList>
        <Journal>
          <Title>Journal of Strength and Conditioning Research</Title>
          <JournalIssue>
            <PubDate>
              <Year>2021</Year>
            </PubDate>
          </JournalIssue>
        </Journal>
        <ELocationID EIdType="doi">10.1519/JSC.0000000000003860</ELocationID>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>99999999</PMID>
      <Article>
        <ArticleTitle>Empty abstract paper</ArticleTitle>
        <Abstract/>
        <AuthorList/>
        <Journal>
          <Title>Some Journal</Title>
          <JournalIssue>
            <PubDate>
              <Year>2020</Year>
            </PubDate>
          </JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>
"""


def test_build_query_mesh_and_text():
    config = {
        "mesh": '"Muscle Hypertrophy"[Mesh]',
        "text": '"resistance training"',
        "years": "2015:2026",
    }
    query = _build_query(config)
    assert '"Muscle Hypertrophy"[Mesh]' in query
    assert '"resistance training"' in query
    assert "2015:2026[pdat]" in query
    assert "humans[mh]" in query


def test_build_query_text_only():
    config = {
        "text": '"rest periods" AND hypertrophy',
    }
    query = _build_query(config)
    assert '"rest periods" AND hypertrophy' in query
    assert "humans[mh]" in query


def test_parse_xml_basic():
    papers = _parse_xml(SAMPLE_XML)
    assert len(papers) == 1  # Second paper has empty abstract, should be filtered
    paper = papers[0]
    assert paper.pmid == "12345678"
    assert paper.source == "pubmed"
    assert "Schoenfeld" in paper.authors
    assert paper.year == 2021
    assert paper.journal == "Journal of Strength and Conditioning Research"
    assert paper.doi == "10.1519/JSC.0000000000003860"
    assert paper.id == "PMID:12345678"


def test_parse_xml_empty_abstract_filtered():
    papers = _parse_xml(SAMPLE_XML)
    pmids = [p.pmid for p in papers]
    assert "99999999" not in pmids


def test_parse_xml_invalid():
    papers = _parse_xml("<invalid>xml</invalid>")
    assert papers == []
