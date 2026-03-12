from __future__ import annotations


def build_cloze(sentence: str, focus_term: str) -> str:
    if not focus_term:
        return sentence
    return sentence.replace(focus_term, "____", 1)


def generate_cards(note_type: str, payload: dict[str, str]) -> list[dict[str, str]]:
    if note_type == "vocab":
        return [
            {"card_type": "hanzi_to_meaning", "prompt_lang": "zh-Hans", "answer_lang": "en+pinyin"},
            {"card_type": "english_to_hanzi", "prompt_lang": "en", "answer_lang": "zh-Hans+pinyin"},
        ]
    if note_type == "char":
        return [
            {"card_type": "char_to_meaning", "prompt_lang": "zh-Hans", "answer_lang": "en+pinyin"},
            {"card_type": "meaning_to_char", "prompt_lang": "en", "answer_lang": "zh-Hans+pinyin"},
        ]
    cards = [
        {"card_type": "sentence_to_meaning", "prompt_lang": "zh-Hans", "answer_lang": "en+pinyin"},
    ]
    if payload.get("focus_term"):
        cards.append({"card_type": "cloze_focus_term", "prompt_lang": "zh-Hans", "answer_lang": "focus+en"})
    return cards
