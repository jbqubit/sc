from __future__ import annotations

from sc.cardgen import build_cloze, generate_cards


def test_vocab_note_generates_two_cards():
    cards = generate_cards("vocab", {"hanzi": "学校", "pinyin": "xue2 xiao4", "english": "school"})
    assert [card["card_type"] for card in cards] == ["hanzi_to_meaning", "english_to_hanzi"]


def test_sentence_note_skips_cloze_without_focus_term():
    cards = generate_cards("sentence", {"sentence_cn": "我去学校", "sentence_en": "I go to school", "focus_term": ""})
    assert [card["card_type"] for card in cards] == ["sentence_to_meaning"]


def test_build_cloze_replaces_first_occurrence():
    assert build_cloze("我去学校，学校很大。", "学校") == "我去____，学校很大。"
