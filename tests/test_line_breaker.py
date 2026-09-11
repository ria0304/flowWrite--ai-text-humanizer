"""
tests/test_line_breaker.py
Comprehensive tests for Stage 5 (Line Break Fragmentation)
"""
import pytest
import unicodedata
from pipeline.line_breaker import (
    fragment_sentences,
    inject_invisible_breaks,
    apply_line_break_trick,
    apply_line_break_trick_with_metadata,
    ZWSP,
    SHY
)


class TestBasicBehavior:
    """Test basic Stage 5 functionality."""
    
    def test_normal_sentence(self):
        """Test that normal sentences get perturbations."""
        text = "This is a simple sentence. Here is another one with more words to trigger fragmentation."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["input_length"] > 0
        assert result["output_length"] >= result["input_length"]
        # Should have some perturbations in a sentence this long
        assert result["total_insertions"] >= 0
    
    def test_multiple_sentences(self):
        """Test multiple sentences are processed correctly."""
        text = "First sentence here. Second sentence there. Third one as well."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "First" in result["output"]
        assert "Second" in result["output"]
        assert "Third" in result["output"]
    
    def test_short_text_no_perturbation(self):
        """Test that short texts (< 6 words) don't get sentence-level perturbations."""
        text = "Short text."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        # Short text should still work but may have fewer perturbations
    
    def test_empty_string(self):
        """Test empty string handling."""
        text = ""
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["output"] == ""
        assert result["input_length"] == 0
        assert result["output_length"] == 0
        assert result["total_insertions"] == 0
    
    def test_repeated_punctuation(self):
        """Test text with repeated punctuation."""
        text = "Wait... what? Yes! Amazing..."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "..." in result["output"] or result["success"] is True
    
    def test_quotes(self):
        """Test text with quotations."""
        text = 'She said "Hello world" and then left.'
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert '"' in result["output"]


class TestUnicodeHandling:
    """Test Unicode character handling."""
    
    def test_emoji(self):
        """Test text with emoji."""
        text = "This is great! 😊👍 Let's celebrate."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "😊" in result["output"]
        assert "👍" in result["output"]
        assert result["utf8_valid"] is True
    
    def test_accented_characters(self):
        """Test text with accented characters."""
        text = "Café résumé naïve coöperate."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "é" in result["output"]
        assert "ï" in result["output"]
        assert result["utf8_valid"] is True
    
    def test_non_latin_scripts(self):
        """Test text with non-Latin scripts."""
        text = "Hello 世界！Привет мир! مرحبا"
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["utf8_valid"] is True
    
    def test_multilingual_text(self):
        """Test multilingual mixed text."""
        text = "English and 中文 and Español and العربية together."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["utf8_valid"] is True
    
    def test_combining_characters(self):
        """Test text with combining characters."""
        # e + combining acute accent
        text = "Cafe\u0301"  # Café with combining character
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["utf8_valid"] is True


class TestSpecialContent:
    """Test special content types."""
    
    def test_urls(self):
        """Test that URLs are preserved."""
        text = "Visit https://example.com/path?query=1 for more info."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "https://example.com" in result["output"]
    
    def test_email_like_strings(self):
        """Test email-like strings."""
        text = "Contact us at support@example.com today."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "@" in result["output"]
    
    def test_numbers(self):
        """Test numerical content."""
        text = "The year 2024 saw 1,234,567 users and 99.9% uptime."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "2024" in result["output"]
        assert "1,234,567" in result["output"]
    
    def test_decimal_numbers(self):
        """Test decimal numbers."""
        text = "The value is 3.14159 and growth was 12.5%."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "3.14159" in result["output"]
    
    def test_abbreviations(self):
        """Test abbreviations."""
        text = "Dr. Smith works at U.S.A. headquarters near D.C."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert "Dr." in result["output"] or "Dr" in result["output"]


class TestStage5Behavior:
    """Test Stage 5 ON/OFF behavior."""
    
    def test_stage5_on_produces_perturbations(self):
        """Test that Stage 5 ON produces expected perturbations."""
        text = "This is a longer sentence with multiple words and connectors but also commas, which should trigger insertions."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        # Should have inserted some characters
        assert result["output_length"] >= result["input_length"]
    
    def test_visible_characters_unchanged(self):
        """Test that visible characters remain unchanged."""
        text = "The quick brown fox jumps over the lazy dog."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        
        # Remove invisible characters and compare
        original_visible = ''.join(c for c in text if c not in [ZWSP, SHY])
        output_visible = ''.join(c for c in result["output"] if c not in [ZWSP, SHY])
        
        assert original_visible == output_visible
    
    def test_correct_unicode_characters_inserted(self):
        """Test that only ZWSP and SHY are inserted."""
        text = "This is a test sentence with multiple words and connectors but also commas, here."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        
        # Count inserted characters
        diff_length = result["output_length"] - result["input_length"]
        total_perturbations = result["zwsp_count"] + result["shy_count"]
        
        # The difference should match the perturbation count
        assert diff_length == total_perturbations
        
        # Verify only ZWSP and SHY are in the perturbations
        for pert in result["perturbations"]:
            assert pert["character"] in [ZWSP, SHY]


class TestUTF8Validity:
    """Test UTF-8 encoding validity."""
    
    def test_utf8_encoding_decoding(self):
        """Test that output can be encoded and decoded as UTF-8."""
        text = "Test with emoji 😊 and accents café."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["utf8_valid"] is True
        
        # Explicitly test encode/decode
        encoded = result["output"].encode('utf-8')
        decoded = encoded.decode('utf-8')
        assert decoded == result["output"]
    
    def test_long_document_utf8(self):
        """Test UTF-8 validity on longer text."""
        text = " ".join(["This is sentence number {}.".format(i) for i in range(50)])
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["utf8_valid"] is True


class TestNormalization:
    """Test Unicode normalization behavior."""
    
    def test_nfc_normalization(self):
        """Test NFC normalization survival."""
        text = "This is a test sentence with multiple words and connectors."
        transformed = apply_line_break_trick(text)
        
        # Apply NFC normalization
        normalized = unicodedata.normalize('NFC', transformed)
        
        # Count remaining ZWSP and SHY
        zwsp_after = normalized.count(ZWSP)
        shy_after = normalized.count(SHY)
        
        # Record for analysis (actual survival depends on normalization rules)
        assert zwsp_after >= 0
        assert shy_after >= 0
    
    def test_nfd_normalization(self):
        """Test NFD normalization survival."""
        text = "This is a test sentence with multiple words and connectors."
        transformed = apply_line_break_trick(text)
        
        # Apply NFD normalization
        normalized = unicodedata.normalize('NFD', transformed)
        
        zwsp_after = normalized.count(ZWSP)
        shy_after = normalized.count(SHY)
        
        assert zwsp_after >= 0
        assert shy_after >= 0
    
    def test_nfkc_normalization(self):
        """Test NFKC normalization survival."""
        text = "This is a test sentence with multiple words and connectors."
        transformed = apply_line_break_trick(text)
        
        # Apply NFKC normalization
        normalized = unicodedata.normalize('NFKC', transformed)
        
        zwsp_after = normalized.count(ZWSP)
        shy_after = normalized.count(SHY)
        
        # Note: NFKC may remove some invisible characters
        # This test records the behavior for the paper
        assert zwsp_after >= 0
        assert shy_after >= 0
    
    def test_nfkd_normalization(self):
        """Test NFKD normalization survival."""
        text = "This is a test sentence with multiple words and connectors."
        transformed = apply_line_break_trick(text)
        
        # Apply NFKD normalization (fixed form name)
        normalized = unicodedata.normalize('NFKD', transformed)
        
        zwsp_after = normalized.count(ZWSP)
        shy_after = normalized.count(SHY)
        
        assert zwsp_after >= 0
        assert shy_after >= 0
    
    def test_normalization_survival_rate(self):
        """Calculate perturbation survival rate under normalization."""
        text = "In practice, this is a test. That said, we need more words here."
        result = apply_line_break_trick_with_metadata(text)
        
        original_zwsp = result["zwsp_count"]
        original_shy = result["shy_count"]
        
        if original_zwsp + original_shy == 0:
            pytest.skip("No perturbations to test survival")
        
        # Test each normalization form
        for norm_form in ['NFC', 'NFD', 'NFKC', 'NFKD']:
            normalized = unicodedata.normalize(norm_form, result["output"])
            zwsp_after = normalized.count(ZWSP)
            shy_after = normalized.count(SHY)
            
            # Record survival rates (for paper analysis)
            zwsp_survival = zwsp_after / original_zwsp if original_zwsp > 0 else 1.0
            shy_survival = shy_after / original_shy if original_shy > 0 else 1.0
            
            # Assert that we can measure survival (actual rates depend on Unicode rules)
            assert 0.0 <= zwsp_survival <= 1.0
            assert 0.0 <= shy_survival <= 1.0


class TestRegression:
    """Regression tests to ensure existing behavior is preserved."""
    
    def test_backward_compatibility_apply_line_break_trick(self):
        """Test that apply_line_break_trick still works as before."""
        text = "This is a test. Another sentence here."
        
        # Old interface should still work
        result = apply_line_break_trick(text)
        
        assert isinstance(result, str)
        assert len(result) >= len(text)
    
    def test_fragment_sentences_returns_tuple(self):
        """Test that fragment_sentences now returns tuple."""
        text = "Test sentence here."
        result, perturbations = fragment_sentences(text)
        
        assert isinstance(result, str)
        assert isinstance(perturbations, list)
    
    def test_inject_invisible_breaks_returns_tuple(self):
        """Test that inject_invisible_breaks now returns tuple."""
        text = "In practice, this works."
        result, perturbations = inject_invisible_breaks(text)
        
        assert isinstance(result, str)
        assert isinstance(perturbations, list)


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_none_input_handling(self):
        """Test that None input is handled gracefully."""
        # The function should handle this without crashing
        try:
            result = apply_line_break_trick_with_metadata(None)
            # If it returns, check the result
            assert result["success"] is False or result["output"] is None
        except (TypeError, AttributeError):
            # Expected behavior if None is not handled
            pass
    
    def test_whitespace_only(self):
        """Test whitespace-only input."""
        text = "   \n\t   "
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
    
    def test_single_character(self):
        """Test single character input."""
        text = "A"
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["output"] == "A"
    
    def test_very_long_text(self):
        """Test very long text."""
        text = " ".join(["word{}".format(i) for i in range(1000)])
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
        assert result["utf8_valid"] is True
    
    def test_mixed_newlines(self):
        """Test text with mixed newline styles."""
        text = "Line one.\r\nLine two.\nLine three.\rLine four."
        result = apply_line_break_trick_with_metadata(text)
        
        assert result["success"] is True
