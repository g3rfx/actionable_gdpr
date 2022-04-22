import spacy
import csv
import string 
import pandas as pd
import re
import sys
import string
import traceback
import datetime
from collections import Counter
import yake
import spacy
import pke
import nltk
from tqdm import tqdm
from multi_rake import Rake
import textacy
from textacy.extract import keyterms
from textacy import preprocessing as textacy_preprocessing
from keybert import KeyBERT
import pandas as pd
from pandas.core.common import flatten
import spacy
from somajo import SoMaJo
from joblib import Parallel, delayed


spacy_languages = {"en": "en_core_web_trf"}
somajo_tokenizer = SoMaJo("en_PTB", split_sentences=False)


def analyse(file):

    print("Start time: ", str(datetime.datetime.now()))


    def somajo_remove_url(text):
        """
        A customized function to remove e-mails which have whitespaces
        and URLs which were apparently not cleaned from the corpus.
        """
        out = []
        text_as_list = list()
        text_as_list.append(text)
        tokenized_text = somajo_tokenizer.tokenize_text(text_as_list)
        for dummy_tokenized_text in tokenized_text:
            # return([detokenize(bla) for bla in tokenized_text][0])
            for token in dummy_tokenized_text:
                if token.token_class == "URL":
                    out.append("-URL-")
                elif token.original_spelling is not None:
                    out.append(token.original_spelling)
                else:
                    out.append(token.text)
                if token.space_after:
                    out.append(" ")
        return "".join(out)


    def text_preprocessing(text):
        text = textacy_preprocessing.normalize.hyphenated_words(text)
        text = textacy_preprocessing.normalize.whitespace(text)
        text = textacy_preprocessing.replace.emails(text, "-Email-")
        text = re.sub(r"[a-zA-Z0-9_.+-]+ @ [ a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", " -Email- ", text)
        text = textacy_preprocessing.replace.urls(text, "-URL-")
        text = somajo_remove_url(text)
        text = re.sub(" +", " ", "".join(x if x.isprintable() or x in string.whitespace else " " for x in text))
        return text


    def spacy_lemmatizer_with_whitespace(docs, language):
        lemmatized_docs = []
        nlp = spacy.load(spacy_languages[language])
        for doc in nlp.pipe(tqdm(docs, total=len(docs), unit="doc", desc="Spacy lemmatizer"), n_process=1):
            lemmatized_docs.append("".join([token.lemma_ + token.whitespace_ for token in doc]))
        return lemmatized_docs


    # def pke_textrank(text, language):
    #     extractor = pke.unsupervised.TextRank()
    #     try:
    #         extractor.load_document(input=text, language=language)
    #         extractor.candidate_selection()
    #         extractor.candidate_weighting(pos={'NOUN', 'PROPN', 'VERB'})
    #         keyphrases = extractor.get_n_best(n=20)
    #         list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
    #     except:
    #         tqdm.write(traceback.format_exc())
    #         sys.exit()
    #     return list_of_keyphrases


    # def pke_singlerank(text, language):
    #     extractor = pke.unsupervised.SingleRank()
    #     try:
    #         extractor.load_document(input=text, language=language)
    #         extractor.candidate_selection(pos={'NOUN', 'PROPN', 'VERB'})
    #         extractor.candidate_weighting(pos={'NOUN', 'PROPN', 'VERB'})
    #         keyphrases = extractor.get_n_best(n=20)
    #         list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
    #     except:
    #         tqdm.write(traceback.format_exc())
    #         sys.exit()
    #     return list_of_keyphrases


    # def pke_positionrank(text, language):
    #     extractor = pke.unsupervised.PositionRank()
    #     try:
    #         extractor.load_document(input=text, language=language)
    #         extractor.candidate_selection(grammar="NP: {<NOUN|PROPN>+}")
    #         extractor.candidate_weighting(pos={'NOUN', 'PROPN', 'VERB'})
    #         keyphrases = extractor.get_n_best(n=20)
    #         list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
    #     except:
    #         tqdm.write(traceback.format_exc())
    #         sys.exit()
    #     return list_of_keyphrases


    # def pke_topicrank(text, language):
    #     extractor = pke.unsupervised.TopicRank()
    #     try:
    #         extractor.load_document(input=text, language=language)
    #         extractor.candidate_selection()
    #         extractor.candidate_weighting()
    #         keyphrases = extractor.get_n_best(n=20)
    #         list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
    #     except:
    #         tqdm.write(traceback.format_exc())
    #         sys.exit()
    #     return list_of_keyphrases


    def pke_multipartiterank(text, language):
        extractor = pke.unsupervised.MultipartiteRank()
        try:
            extractor.load_document(input=text, language=language)
            extractor.candidate_selection(pos={'NOUN', 'PROPN', 'VERB'})
            extractor.candidate_weighting()
            keyphrases = extractor.get_n_best(n=20)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_textrank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.textrank(doc, normalize="lemma", topn=20, include_pos=pos, window_size=2, edge_weighting="binary", position_bias=False)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_singlerank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.textrank(doc, normalize="lemma", topn=20, include_pos=pos, window_size=10, edge_weighting="count", position_bias=False)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_positionrank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.textrank(doc, normalize="lemma", topn=20, include_pos=pos, window_size=10, edge_weighting="count", position_bias=True)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_yake(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.yake(doc, ngrams=1, normalize="lemma", topn=20, include_pos=pos)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            print(text)
            list_of_keyphrases = []
        return list_of_keyphrases


    def textacy_scake(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.scake(doc, normalize="lemma", topn=20, include_pos=pos)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def textacy_sgrank(text, language, pos):
        try:
            doc = textacy.make_spacy_doc(text, lang=spacy_languages[language])
            keyphrases = keyterms.sgrank(doc, ngrams=1, normalize="lemma", topn=20, include_pos=pos)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            list_of_keyphrases = []
        return list_of_keyphrases


    def keybert(text, language):
        try:
            if language == "en":
                kw_model = KeyBERT(model="paraphrase-mpnet-base-v2")
            else:
                kw_model = KeyBERT(model="paraphrase-multilingual-mpnet-base-v2")
            keyphrases = kw_model.extract_keywords(text, keyphrase_ngram_range=(1, 1), top_n=20)
            list_of_keyphrases = [keyphrase for keyphrase, score in keyphrases]
        except:
            tqdm.write(traceback.format_exc())
            sys.exit()
        return list_of_keyphrases


    def postprocessing(list_of_lists_of_keywords, name, pos=None):
        list_of_lists_of_keywords = [keyword.lower() for list_of_keywords in list_of_lists_of_keywords for keyword in list_of_keywords]
        list_of_freq_keywords = nltk.FreqDist(flatten(list_of_lists_of_keywords)).most_common()
        if pos:
            df_keywords = pd.DataFrame(list_of_freq_keywords, columns=[name + "_" + pos, name + "_" + pos + "_" + "Freq"])
        else:
            df_keywords = pd.DataFrame(list_of_freq_keywords, columns=[name, name + "_" + "Freq"])
        print(df_keywords.head())
        return df_keywords


    ### Entry point ###

    keyphrase_extractors = {
        "KeyBert": keybert,
        "TextRank": textacy_textrank,
        "SingleRank": textacy_singlerank,
        "PositionRank": textacy_positionrank,
        "MultipartiteRank": pke_multipartiterank,
        "Yake": textacy_yake,
        "sCAKE": textacy_scake,
        "SGRank": textacy_sgrank
    }

    # Depending whether the library does lemmatization or not by itself, the appropriate list is passed to the function
    groups_of_algorithms = {"misc":['MultiRake', "KeyBert"],
            "pke":['TopicRank', 'MultipartiteRank'],
            "textacy":['TextRank', 'SingleRank', 'PositionRank', "Yake", "sCAKE", "SGRank"]}

    language = "en"
    include_pos = ['NOUN', "PROPN", "VERB"]

    # load tsv file as corpus
    list_of_texts = []
    with open(file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            row2string = ''.join(str(e) for e in row)
            rowSplited = row2string.split('\t')
            parapraph = rowSplited[1]
            list_of_texts.append(parapraph)

    list_of_texts = [text_preprocessing(text) for text in list_of_texts]
    list_of_lemmatized_texts = spacy_lemmatizer_with_whitespace(list_of_texts, language)

    list_of_df_keywords = []
    for name, extractor in keyphrase_extractors.items():
        if name in groups_of_algorithms["textacy"]:
            for pos in include_pos:
                print("Extracting keyphrases using " + name + " for " + pos)
                list_of_lists_of_keywords = Parallel(n_jobs=1)(
                    delayed(extractor)(text, language, pos) for text in tqdm(list_of_texts, position=1))
                df_keywords = postprocessing(list_of_lists_of_keywords, name, pos)
                list_of_df_keywords.append(df_keywords)
        else:
            list_of_lists_of_keywords = Parallel(n_jobs=1)(
            delayed(extractor)(text, language) for text in tqdm(list_of_lemmatized_texts, position=1))
            df_keywords = postprocessing(list_of_lists_of_keywords, name, None)
            list_of_df_keywords.append(df_keywords)

    df_keywords = pd.concat(list_of_df_keywords, axis=1)
    filename = './output/'+str(file).split('/')[-1].split('.')[0]+'_single_keywords'+'.csv'
    df_keywords.to_csv(filename, sep='\t', encoding='utf-8')


file = "./input/contact_details.tsv"
analyse(file)
file = './input/user_rights_sentences.tsv'
analyse(file)
