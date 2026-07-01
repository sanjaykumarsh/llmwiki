import unittest
import tempfile
import shutil
from pathlib import Path

import agent

class TestLLMwikiOperations(unittest.TestCase):
    def setUp(self):
        # Create temp folder structures
        self.test_dir = Path(tempfile.mkdtemp())
        self.raw_dir = self.test_dir / "raw"
        self.wiki_dir = self.test_dir / "wiki"
        self.raw_dir.mkdir()
        self.wiki_dir.mkdir()

    def tearDown(self):
        # Clean up temp folder structures
        shutil.rmtree(self.test_dir)

    def test_extract_text_txt(self):
        # Test basic text extraction from .txt file
        test_file = self.raw_dir / "sample.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Hello LLMwiki, this is a test.")
        
        extracted = agent.extract_text(test_file)
        self.assertEqual(extracted, "Hello LLMwiki, this is a test.")

    def test_search_indexing_and_ranking(self):
        # Create test markdown files in wiki
        file_a = self.wiki_dir / "transformer.md"
        with open(file_a, "w", encoding="utf-8") as f:
            f.write("title: Transformer\n\nThe transformer model uses attention mechanisms to process sequences.")

        file_b = self.wiki_dir / "attention.md"
        with open(file_b, "w", encoding="utf-8") as f:
            f.write("title: Attention Mechanism\n\nAttention is a core component of neural networks and deep learning models.")

        # Test index building
        index = agent.build_search_index(self.wiki_dir)
        self.assertIn("transformer", index)
        self.assertIn("attention", index)

        # Test search ranking
        results = agent.search_wiki("attention mechanism", self.wiki_dir, top_n=2)
        # Should return both files because both contain keywords, but attention.md is highly relevant
        self.assertTrue(len(results) > 0)
        self.assertIn("attention.md", results)

    def test_programmatic_lint_checks(self):
        # Test orphan and broken link detection logic.
        # Create file_a linking to file_b, and a broken link to file_c
        file_a = self.wiki_dir / "page-a.md"
        with open(file_a, "w", encoding="utf-8") as f:
            f.write("---\ntype: concept\ntitle: Page A\n---\n\nLinks to [[page-b]] and a broken [[page-c]].")

        file_b = self.wiki_dir / "page-b.md"
        with open(file_b, "w", encoding="utf-8") as f:
            f.write("---\ntype: concept\ntitle: Page B\n---\n\nThis is page B with no links.")

        # Run local checks (extracted from run_lint programmatic part)
        wiki_files = list(self.wiki_dir.glob("*.md"))
        concept_filenames = {f.name.replace(".md", "") for f in wiki_files}
        
        broken_links = []
        orphan_candidates = set(concept_filenames)
        
        for file_path in wiki_files:
            page_name = file_path.name.replace(".md", "")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            import re
            links = re.findall(r'\[\[([^\]|#]+)(?:\|[^\]]*)?(?:#[^\]]*)?\]\]', content)
            
            links_cleaned = set()
            for l in links:
                l_clean = l.strip().lower().replace(" ", "-")
                links_cleaned.add(l_clean)
                if l_clean not in concept_filenames:
                    broken_links.append({
                        "source_file": file_path.name,
                        "broken_target": l_clean
                    })
            
            for l in links_cleaned:
                if l in orphan_candidates:
                    orphan_candidates.remove(l)

        # Assert broken link to page-c is caught
        self.assertEqual(len(broken_links), 1)
        self.assertEqual(broken_links[0]["broken_target"], "page-c")
        
        # Assert page-a is detected as an orphan (nothing links to it)
        # while page-b is NOT an orphan (page-a links to it)
        self.assertIn("page-a", orphan_candidates)
        self.assertNotIn("page-b", orphan_candidates)

if __name__ == "__main__":
    unittest.main()
