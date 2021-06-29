from application import nlp, model, DELIMITER, RE_HYPHENS, RE_QUOTES1, RE_QUOTES2
from nltk.tokenize.treebank import TreebankWordDetokenizer
from application.models.gector.predict import predict_for_sentences
from application.models.gector.utils.preprocess_data import align_sequences, convert_tagged_line
import re



def predict(input_text: str) -> dict:
    tokenized_sentence = tokenize_and_segment(input_text)
    corrected_sentences = predict_for_sentences(tokenized_sentence, model)
    correct_untokenized_sentences = [
        untokenize(sent) for sent in corrected_sentences]

    tagged_input, tagged_output, output = get_changes(
        sentencize(input_text), correct_untokenized_sentences)
    tagged_input = unsentencize(tagged_input)
    tagged_output = unsentencize(tagged_output)
    output = unsentencize(output)
    output = output.replace("$_$TRANSFORM", "")
    output = output.replace("$_$REPLACE", "")
    output = output.replace("$_$APPEND", "")
    output = output.replace("$_$PUNCT", "")
    return {"input": '<span style="font-size:17px">' + tagged_input+'</span>', "output": '<span style="font-size:17px">'+tagged_output+'</span>', "output_text": output}


def sentencize(text: str) -> 'list(str)':
    return [sent for sent in nlp(text).sents]


def tokenize_and_segment(input_text: str) -> 'list(str)':
    doc = nlp(input_text)
    sentences = []
    for sent in doc.sents:
        sentences.append(' '.join(token.text for token in sent))
    return sentences


def untokenize(tokens: list) -> str:
    output_text = TreebankWordDetokenizer().detokenize(tokens)
    output_text = re.sub(RE_HYPHENS, r'\1-\2', output_text)
    output_text = re.sub(RE_QUOTES1, r'\1\2', output_text)
    output_text = re.sub(RE_QUOTES2, r'\1\2', output_text)
    return output_text


def unsentencize(sentences: 'list(str)') -> str:
    output_text = ' '.join(sent for sent in sentences)
    return output_text


def get_changes(input_text: 'list(str)', output_text: 'list(str)') -> '(str,str)':
    tagged_input = list()
    tagged_output = list()
    output = list()
    for i in range(len(input_text)):
        input_sent = input_text[i].text
        output_sent = output_text[i]
        sent_with_tags = align_sequences(input_sent, output_sent)
        target_text, replaced_tok_ids, deleted_tok_ids = convert_tagged_line(
            sent_with_tags)
        tagged_input.append(highlight_changes_input(
            sent_with_tags, replaced_tok_ids, deleted_tok_ids))
        tagged_output.append(highlight_changes_output(target_text))
        output.append(target_text)
    return tagged_input, tagged_output, output


def highlight_changes_input(sent_with_tags, replaced_tok_ids, deleted_tok_ids):
    tagged_input_tokens = []
    for idx, token in enumerate(sent_with_tags.split()[1:]):
        token = token.split(DELIMITER)[0]
        if idx in deleted_tok_ids:
            token = add_css_tag(token, 'input_delete')
            deleted_tok_ids = [
                i + 1 for i in deleted_tok_ids[1:]]  # shift index
            replaced_tok_ids = [i + 1 for i in replaced_tok_ids]
        elif idx in replaced_tok_ids:
            token = add_css_tag(token, 'input_replace')
            replaced_tok_ids = replaced_tok_ids[1:]
        tagged_input_tokens.append(token)
    return ' '.join(tagged_input_tokens)


def highlight_changes_output(target_text):
    tagged_output_tokens = []
    for token in target_text.split():
        if '$_$' in token:
            modif_tag = token.split('$_$')[1]
            token = token.split('$_$')[0]
            if modif_tag == 'REPLACE' or modif_tag == 'TRANSFORM':
                token = add_css_tag(token, 'replace')
            elif modif_tag == 'APPEND':
                token = add_css_tag(token, 'append')
            elif modif_tag == 'PUNCT':
                token = add_css_tag(token, 'punctuation')
        tagged_output_tokens.append(token)
    return ' '.join(tagged_output_tokens)


def add_css_tag(token, modification):
    if modification == 'replace':
        token = '<span style="color:#00B8BA;border-bottom: 2px solid #00B8BA;">' + token + '</span>'
    elif modification == 'delete':
        token = '<span>' + token + '</span>'
    elif modification == 'append':
        token = '<span style="color:#FFFE33;border-bottom: 2px solid #FFFE33;">' + token + '</span>'
    elif modification == 'punctuation':
        token = token[:-1] + '<span style="color:#FFFE33;border-bottom: 2px solid #FFFE33;">' + \
            token[-1] + '</span>'
    elif modification == 'input_delete':
        token = '<span style="text-decoration: line-through #e54d42;">' + token + '</span>'
    elif modification == 'input_replace':
        token = '<span style="color:#e54d42;border-bottom: 2px solid #e54d42;">' + token + '</span>'
    return token
