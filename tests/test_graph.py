"""Provenance graph is a typed retrieval DAG, not a causal biomedical graph."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import json
import unittest
from xml.etree import ElementTree as ET
from muhu.provenance_graph import (
 SARA_SHA256,SNAPSHOT_SHA256,GRAPH_SCHEMA,TOPICS,
 validate_sara,new_sara_snapshot,build_from_paths,validate_graph,
 filtered_graph,source_path_for_pmid,lexical_search,canonical,digest
)
from muhu.graph_ui import svg_map,page

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/"research"/"public_sources"

class ProvenanceGraphTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.g=build_from_paths(EVIDENCE/"pubmed-sources-admitted-20261117.json",
                         EVIDENCE/"sara-pubmed-sources-20261117.json")

 def test_explicit_bounded_source_snapshots(self):
  self.assertEqual(self.g["schema"],GRAPH_SCHEMA)
  self.assertEqual(self.g["parent_snapshot_sha256"]["prior"],SNAPSHOT_SHA256)
  self.assertEqual(self.g["parent_snapshot_sha256"]["sara"],SARA_SHA256)
  self.assertEqual(len(self.g["graph_sha256"]),64)

 def test_four_sara_pubmed_author_index_strings(self):
  sara=new_sara_snapshot(EVIDENCE/"sara-pubmed-sources-20261117.json")
  self.assertEqual(sara["record_count"],4)
  self.assertEqual({i["pmid"] for i in sara["items"]},
    {"36046618","40627371","42213236","42740140"})
  self.assertEqual({r["sara_author_query_name_as_reported"] for r in sara["items"]},
    {"Behnamian S"})
  self.assertEqual(sara["scientific_quality"],"NOT_EVALUATED")

 def test_exact_source_query_count(self):
  info=validate_graph(self.g)
  self.assertEqual(info["papers"],23)
  self.assertEqual(info["nodes"],53)
  self.assertEqual(info["edges"],92)
  self.assertTrue(info["acyclic"])
  self.assertEqual(info["biological_associations"],0)

 def test_explicit_scope_cardinality(self):
  self.assertEqual({k:filtered_graph(self.g,k)["selected_publications"] for k in TOPICS},
                   {"sara":4,"vidal":7,"wwox":9,"worm_methods":3})
  self.assertEqual(filtered_graph(self.g)["selected_publications"],23)

 def test_sara_and_vidal_lineages_keep_separate(self):
  sara=source_path_for_pmid(self.g,"40627371")
  vidal=source_path_for_pmid(self.g,"41431865")
  self.assertEqual(sara["publication"]["query_scope"],["sara"])
  self.assertEqual(vidal["publication"]["query_scope"],["vidal"])
  self.assertNotEqual(sara["publication"]["snapshot_sha256"],
                      vidal["publication"]["snapshot_sha256"])
  self.assertTrue(sara["no_causal_claims"])

 def test_provenance_edges_never_biological_claims(self):
  for edge in self.g["edges"]:
   self.assertFalse(edge["supports_biological_claim"])
   self.assertFalse(edge["is_sci_or_clinical_evidence"])
   self.assertNotIn(edge["predicate"],("CAUSES","TREATS","EFFECTIVE_FOR","GENE_TO_DISEASE"))
  self.assertFalse(self.g["mechanistic_or_causal_edges_present"])
  self.assertFalse(self.g["clinical_qualification"])

 def test_stable_original_graph_hash_and_canonicality(self):
  other=build_from_paths(EVIDENCE/"pubmed-sources-admitted-20261117.json",
                         EVIDENCE/"sara-pubmed-sources-20261117.json")
  self.assertEqual(self.g["graph_sha256"],other["graph_sha256"])
  raw={k:v for k,v in self.g.items() if k!="graph_sha256"}
  self.assertEqual(digest(canonical(raw)),self.g["graph_sha256"])

 def test_invalid_forged_causal_edge_denied(self):
  g=deepcopy(self.g);g.pop("graph_sha256")
  g["edges"][0]["predicate"]="TREATS"
  with self.assertRaisesRegex(ValueError,"CAUSAL_OR_UNKNOWN"):
   validate_graph(g)

 def test_mutated_graph_node_checksum_denied(self):
  g=deepcopy(self.g)
  next(n for n in g["nodes"] if n["kind"]=="publication")["label"]="made up clinical efficacy"
  with self.assertRaisesRegex(ValueError,"GRAPH_SOURCE_CONTENT_TAMPERED"):
   validate_graph(g)

 def test_tampered_sara_record_denied(self):
  source=(EVIDENCE/"sara-pubmed-sources-20261117.json").read_bytes()
  changed=source.replace(b"AncestryGeni",b"AncestryGini")
  self.assertNotEqual(source,changed)
  with self.assertRaisesRegex(ValueError,"UNREVIEWED_SARA_SOURCE_BYTES"):
   validate_sara(changed)

 def test_unknown_topic_denied(self):
  with self.assertRaisesRegex(ValueError,"BAD_GRAPH_TOPIC"):
   filtered_graph(self.g,"gene_therapy_works")

 def test_unknown_pmid_is_unavailable_not_falsified(self):
  o=source_path_for_pmid(self.g,"99999999")
  self.assertEqual(o["state"],"UNAVAILABLE_NOT_IN_SELECTED_RESEARCH_SNAPSHOTS")
  self.assertTrue(o["publication_may_exist_elsewhere"])
  with self.assertRaises(ValueError):source_path_for_pmid(self.g,"not-a-pmid")

 def test_source_trace_has_exact_snapshot_sha(self):
  o=source_path_for_pmid(self.g,"42213236")
  provenance={r["relation"] for r in o["incoming_metadata_edges"]}
  self.assertEqual(provenance,
    {"INDEXED_IN_SELECTED_SNAPSHOT","SELECTED_FOR_BIBLIOGRAPHIC_QUERY"})
  self.assertTrue(all(e["source_snapshot_sha256"]==SARA_SHA256
                      for e in o["incoming_metadata_edges"]))

 def test_title_only_search_has_no_efficiency_claim(self):
  o=lexical_search(self.g,"AncestryGeni")
  self.assertEqual(o["state"],"BIBLIOGRAPHIC_TITLE_RETRIEVAL_ONLY")
  self.assertEqual(o["results"][0]["pmid"],"40627371")
  self.assertTrue(o["no_claims_about_relevance_beyond_title"])
  self.assertEqual(o["scientific_validity"],"NOT_EVALUATED")
  self.assertIn("title_only_score_not_probability",o["results"][0])

 def test_search_can_abstain_and_refuse_sensitive_syntax(self):
  self.assertEqual(lexical_search(self.g,"unknowntermxyz123")["state"],
                   "ABSTAIN_NO_SELECTED_TITLE_MATCH")
  for bad in ("", "a","http://evil.invalid","<script>","x"*101,"a?patient=secret"):
   with self.subTest(bad=bad):
    with self.assertRaises(ValueError):lexical_search(self.g,bad)

 def test_svg_is_valid_xml_and_has_no_scripts(self):
  svg=svg_map(filtered_graph(self.g,"sara"))
  ET.fromstring(svg)
  self.assertIn("PMID 40627371",svg)
  self.assertIn("two-dimensional",svg.lower())
  self.assertNotIn("<script",svg.lower())
  self.assertNotIn("GENE_CAUSES",svg)

 def test_full_holographic_projection_is_described_as_svg_not_3d(self):
  html=page(filtered_graph(self.g))
  self.assertIn("23",html)
  self.assertIn("not a biological causal",html.lower())
  self.assertIn("not an interactive 3D",html)
  self.assertIn("Hugging Face Space remains research-only",html)

 def test_page_escapes_and_does_not_embed_private_evaluation(self):
  html=page(filtered_graph(self.g,"wwox"))
  self.assertNotIn("private_validation.jsonl",html)
  self.assertIn("PubMed",html)
  self.assertIn("WWOX",html)

if __name__=="__main__":unittest.main()
