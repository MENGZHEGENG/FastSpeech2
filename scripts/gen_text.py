import re
import sys
import json
from unicodedata import normalize
from tqdm import tqdm
from ipatok import tokenise
from g2p import make_tokenizer

# Regular expression matching whitespace:
_whitespace_re = re.compile(r"\s+")


def lower(text):
    """
    >>> lower("MiXeD ÇÀSÉ")
    'mixed çàsé'
    """
    return text.lower()


def nfc_normalize(text):
    """
    >>> nfc_normalize("éçà")
    'éçà'
    """
    return normalize("NFC", text)


def collapse_whitespace(text):
    """
    >>> collapse_whitespace("  asdf  	   qwer   ")
    ' asdf qwer '
    """
    return re.sub(_whitespace_re, " ", text)


def clean_text(text, lang):
    """
    clean the text
    """
    if lang == "moh" or lang == "crk":
        sentence = lower(collapse_whitespace(nfc_normalize(text)))
    elif lang == "str":
        sentence = collapse_whitespace(nfc_normalize(text))

    # special consideration for moh
    if lang == "moh":
        sentence = sentence.replace("׃", "ː")
    return sentence


def transform_ipa(ipas):
    """
    transform ipa to replace " " as "#"
    """
    tokenizer = make_tokenizer(lang)
    out_ipas = "{"
    for index, token in enumerate(tokenizer.tokenize_text(ipas)):
        if token["is_word"]:
            units = tokenise(token["text"])
        elif token["text"] == " ":
            units = ["# " if index == 0 else " # "]
        else:
            units = [
                f"{token['text']} " if index == 0 else f" {token['text']} "
            ]
        out_ipas += " ".join(units)
    out_ipas = out_ipas.strip() + "}"
    return out_ipas


if __name__ == "__main__":

    in_ipa_file = sys.argv[1]
    in_text_file = sys.argv[2]
    out_file = sys.argv[3]
    lang = sys.argv[4]

    sentence_map = {}
    out_lines = []

    with open(in_text_file, "r") as f:
        for line in tqdm(f):
            json_data = json.loads(line)
            sentence = clean_text(json_data["sentence"], lang)
            sentence_id = json_data["original_sentence_id"]
            sentence_map[sentence_id] = sentence

    with open(in_ipa_file, "r") as f:
        for line in tqdm(f):
            utt_id = line.strip().split("|")[0]
            map_id = utt_id.split("-")[1]
            spk = line.strip().split("|")[2]
            ipas = clean_text(line.strip().split("|")[-1], lang)
            ipas = transform_ipa(ipas)
            sentence = sentence_map[map_id]
            out_lines.append(f"{utt_id}|{spk}|{ipas}|{sentence}")

    with open(out_file, "w") as f:
        for line in tqdm(out_lines):
            f.write(line + "\n")
