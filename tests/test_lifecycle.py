"""Editorial source lifecycle identity and safeguards, including synthetic notices."""
from pathlib import Path
import json
import unittest
from xml.etree import ElementTree as ET

from muhu.lifecycle import (
 SCHEMA,PINNED_SNAPSHOT_SHA,REF_TYPES,create_snapshot,validate_snapshot,
 parse_efetch,version_components,_note_category,lookup,load,canonical,sha,
)
from muhu.provenance_graph import build_from_paths

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/"research"/"public_sources"
FILE=BASE/"pubmed-editorial-lifecycle-20261117.json"

def xml_fixture(pmids=("11111","22222"),linked_type="UpdateIn",types=None):
 types=types or ["Journal Article","Preprint"]
 records=[]
 for i,p in enumerate(pmids):
  corr=(f'<CommentsCorrectionsList><CommentsCorrections RefType="{linked_type}">'
        f'<RefSource>Fictional citation.</RefSource><PMID>{pmids[1-i]}</PMID>'
        f'</CommentsCorrections></CommentsCorrectionsList>'
        if len(pmids)==2 else "")
  pubs="".join(f"<PublicationType>{k}</PublicationType>" for k in types)
  records.append(f'<PubmedArticle><MedlineCitation Status="MEDLINE"><PMID>{p}</PMID>'
    f'<Article><ArticleTitle>Original invented paper {p}</ArticleTitle>'
    f'<PublicationTypeList>{pubs}</PublicationTypeList></Article>'
    f'{corr}</MedlineCitation>'
    '<PubmedData><PublicationStatus>epublish</PublicationStatus></PubmedData>'
    '</PubmedArticle>')
 return ("<PubmedArticleSet>"+"".join(records)+"</PubmedArticleSet>").encode()

class EditorialLifecycleTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.snapshot=load(FILE)
  cls.graph=build_from_paths(BASE/"pubmed-sources-admitted-20261117.json",
    BASE/"sara-pubmed-sources-20261117.json")

 def test_pinned_public_source_exact_bytes(self):
  self.assertEqual(sha(FILE.read_bytes()),PINNED_SNAPSHOT_SHA)
  self.assertEqual(self.snapshot["schema"],SCHEMA)
  self.assertEqual(len(self.snapshot["normalized_records"]),23)
  self.assertEqual(self.snapshot["parent_bibliographic_graph_sha256"],self.graph["graph_sha256"])
  self.assertTrue(self.snapshot["not_training_data"])

 def test_selected_editorial_state_denominators(self):
  result=validate_snapshot(self.snapshot)
  self.assertEqual(result["selected_pmids"],23)
  self.assertEqual(result["version_groups"],22)
  self.assertEqual(self.snapshot["editorial_category_counts"]["PREPRINT_WITH_VERSION_UPDATE_LINK"],3)
  self.assertEqual(self.snapshot["editorial_category_counts"]["VERSION_UPDATE_LINK_OBSERVED"],2)
  self.assertEqual(self.snapshot["editorial_category_counts"]["NO_TRACKED_EDITORIAL_LINK_OBSERVED_NOT_VERIFIED_CLEAR"],18)

 def test_three_preprints_with_update_records(self):
  for pmid in ("39185200","39257798","40661626"):
   row=lookup(self.snapshot,pmid)
   self.assertEqual(row["publication"]["editorial_index_state"],"PREPRINT_WITH_VERSION_UPDATE_LINK")
   self.assertIn("Preprint",row["publication"]["publication_types"])
   self.assertTrue(any(link["type"]=="UpdateIn" for link in row["publication"]["correction_links"]))

 def test_preprint_and_updated_paper_not_independent(self):
  group=lookup(self.snapshot,"39257798")["version_group"]
  self.assertEqual(group["selected_pmids"],["39257798","41431865"])
  self.assertTrue(self.snapshot["version_components"]["version_links_not_independent_scientific_replication"])
  self.assertIn(["39257798","41431865"],
    self.snapshot["version_components"]["explicit_in_sample_version_links"])
  self.assertEqual(lookup(self.snapshot,"41431865")["version_group"],group)

 def test_outside_index_update_not_silently_invented(self):
  refs=self.snapshot["version_components"]["unselected_linked_version_targets"]
  self.assertTrue(any(item["linked_pmid"]=="41429758" for item in refs))
  self.assertTrue(any(item["linked_pmid"]=="40979067" for item in refs))
  for item in refs:
   self.assertIs(item["linked_record_in_sample"],False)

 def test_no_index_notice_does_not_prove_clean(self):
  row=lookup(self.snapshot,"42422765")
  self.assertEqual(row["publication"]["editorial_index_state"],
   "NO_TRACKED_EDITORIAL_LINK_OBSERVED_NOT_VERIFIED_CLEAR")
  self.assertIs(row["publication"]["retraction_status_comprehensively_verified"],False)
  self.assertIs(row["editorial_notice_absence_does_not_prove_clean_status"],True)
  self.assertEqual(row["scientific_claim_validity"],"NOT_ASSESSED")

 def test_not_in_selected_source_is_unknown(self):
  out=lookup(self.snapshot,"99999999")
  self.assertEqual(out["state"],"UNAVAILABLE_NOT_IN_23_SELECTED_PMIDS")
  self.assertTrue(out["upstream_publication_absence_not_inferred"])
  with self.assertRaises(ValueError):lookup(self.snapshot,"not_numeric")

 def test_synthetic_normalized_retraction_flag(self):
  self.assertEqual(_note_category(["Journal Article","Retracted Publication"],[]),
    "RETRACTION_INDEX_FLAG_REVIEW_REQUIRED")
  self.assertEqual(_note_category(["Journal Article"],[{"type":"RetractionIn","linked_pmid":"33333"}]),
    "RETRACTION_INDEX_FLAG_REVIEW_REQUIRED")

 def test_synthetic_expression_of_concern_flag(self):
  self.assertEqual(_note_category(["Journal Article"],[{"type":"ExpressionOfConcernIn"}]),
    "EXPRESSION_OF_CONCERN_INDEX_FLAG_REVIEW_REQUIRED")

 def test_synthetic_erratum_flag(self):
  self.assertEqual(_note_category(["Journal Article"],[{"type":"ErratumIn"}]),
    "ERRATUM_INDEX_FLAG_REVIEW_REQUIRED")

 def test_synthetic_preprint_flag_with_and_without_version(self):
  self.assertEqual(_note_category(["Preprint"],[]),
    "PREPRINT_INDEXED_VERSION_REVIEW_REQUIRED")
  self.assertEqual(_note_category(["Preprint"],[{"type":"UpdateIn"}]),
    "PREPRINT_WITH_VERSION_UPDATE_LINK")

 def test_synthetic_two_article_xml(self):
  docs=parse_efetch(xml_fixture(),{"11111","22222"})
  self.assertEqual(len(docs),2)
  self.assertEqual(docs[0]["correction_links"][0]["type"],"UpdateIn")
  self.assertEqual(version_components(docs)["selected_pmid_version_group_count"],1)

 def test_bad_provider_ref_type_refuses(self):
  xml=xml_fixture(linked_type="BiologyProven").replace(b"UpdateIn",b"BiologyProven")
  with self.assertRaisesRegex(ValueError,"UNRECOGNIZED_NLM"):
   parse_efetch(xml,{"11111","22222"})

 def test_bad_source_count_or_unrecognized_id_refuses(self):
  with self.assertRaises(ValueError):parse_efetch(xml_fixture(),{"11111"})
  with self.assertRaises(ValueError):parse_efetch(xml_fixture(),{"33333","44444"})

 def test_preprinted_snapshot_source_conflict_refuses(self):
  altered=dict(self.snapshot)
  altered["clinical_or_biological_validity"]="PROVEN"
  with self.assertRaisesRegex(ValueError,"FALSE_CLINICAL"):
   validate_snapshot(altered)
  altered=dict(self.snapshot)
  altered["absence_of_notice_is_evidence_of_clean_status"]=True
  with self.assertRaisesRegex(ValueError,"FALSE_NEGATIVE"):
   validate_snapshot(altered)

 def test_no_full_text_or_patient_data_stored(self):
  for row in self.snapshot["normalized_records"]:
   self.assertEqual(row["scientific_or_clinical_quality"],"NOT_EVALUATED")
   self.assertFalse(row["retraction_status_comprehensively_verified"])
   self.assertFalse(any(k in row for k in ("abstract","full_text",
    "genomic_sequence","patient_record","private_lab_data")))
  self.assertTrue(self.snapshot["no_provider_lookup_on_user_request"])
  self.assertFalse(self.snapshot["external_signature"])

if __name__=="__main__":unittest.main()
