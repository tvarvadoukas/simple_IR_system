"""
Simple in-memory IR system that supports boolean and TFIDF-based queries.

The boolean queries are single terms connected with the boolean operators
OR or AND (or lowercase), e.g.:

> science
> politics AND terrorism
> religion OR science AND atheism

The top matching documents are retrieved, but there is no notion of ranking.

TF-IDF queries can be more generic search phrases (no specific format) and the
documents are ranked based on their matching score (the higher the better).


Attributes
----------
dataset : list of dicts
    Represents the index of dataset's documents.

    Each entry in the list represents a document.  It contains the path to the
    document, which is relative to the top level dataset's directory path, the
    number of indexable terms in it and their counts.  These metadata are
    required for ranking algorithms based on metrics like TF-IDF.  Also, the
    implicit position in the index can be used as the document's id, which
    offers memory conveniences as it is only an integer.
    
    Below is a block representation of this attribute's internal structure:

        [
            {
                "filename": str,
                "length": int,
                "counts": {
                    str : int,
                    str : int,
                    ...
                    str : int
                }
            },
            ...
        ]
inverted_index : dict of sets of int
    Inverted index of terms to documents.
    
    It is a dictionary where each entry's key is an indexable term and its
    value the list of documents (their id's) that contain them.  In this
    implementation the list of documents is represented by sets to gain the
    speed benefits of union and intersection.        

    Below is a block representation of this attribute's internal structure:
    {
        str : set(int, int, ...),
        str : set(...),
        ...
        str : set(...)
    }
extract_words : function
    This regular expression method is used for tokenization below.  It is
    defined inline and at the module level only for speed optimization
    purposes.

"""
import os
import math
from time import time
from re import compile
from collections import defaultdict
from heapq import heappush, heapreplace


inverted_index = defaultdict(set)
dataset = []

extract_words = compile('[a-z0-9]+').findall


def build_index(root_path):
    """Indexes all the documents found under the top level directory defined
    by `root_path`.

    This function does the necessary pre-processing of any IR system; creates
    an index of the documents with some metadata and an inverted index of
    terms to the documents that contain them.  These two data structures are
    represented by the global variables `dataset` and `inverted_index`, that
    will be set after the termination of this function.

    Parameters
    ----------
    root_path : str
        Path to the top level directory containing the documents of a dataset.
        The structure of the filesystem below does not matter, but it should
        not contain irrelevant files.

    Returns
    -------
    None

    """
    global dataset
    dataset = [index_document(filename, f_id)
               for f_id, filename in enumerate(get_filenames(root_path))]


def get_filenames(root_path):
    """Yields a relative path of a file in the directory defined by
    `root_path`.

    Parameters
    ----------
    root_path : str
        Path to dataset's top level directory.
    
    Yields
    ------
    str
        The relative path of a file.
    
    """
    return (os.path.join(dirpath, f)
            for dirpath, _, files in os.walk(root_path)
            for f in files)


def index_document(filename, f_id):
    """Indexes a document.

    Indexing can be summarized by the following steps:
        1. Read a document.
        2. Tokenize it and extract indexable terms.
        3. Add the extracted terms in the inverted index.
        4. Store required metadata for each document in the index:
           filename, terms' frequencies and size.

    This function does all the above steps apart from storing the final
    document's representation.  Insteat it is being returned and the calling
    function is responsible for storage.

    Parameters
    ----------
    filename : str
        Path to the file.
    f_id : int
        Document's unique id.

    Returns
    -------
    dict
        A document's indexable representation.  Look the documentation of
        the module level variable `dataset` for a more detailed explanation.

    """
    global inverted_index
    tokens = tokenize(read_file(filename))
    counts = defaultdict(int)
    for t in tokens:
        inverted_index[t].add(f_id)
        counts[t] += 1
    return {"filename": filename,
            "counts": counts,
            "length": len(tokens)}


def read_file(filename):
    """Returns the contents of a file as a string. """
    with open(filename) as fp:
        return fp.read()


def tokenize(document):
    """Tokenizes a string and returns a list of indexable terms.

    The following tokenization steps are applied:
        1. Lowercase
        2. Keep only letters and numbers
    
    Parameters
    ----------
    document : str
        Indexable content of a document.

    Returns
    -------
    list
        Valid terms to be indexed.

    """
    return extract_words(document.lower())


def query(querystring, max_results=10, strategy="boolean"):
    """Queries the system based on the `strategy` chosen.

    Parameters
    ----------
    querystring : str
        Query string. Look at `boolean_query()` for the appropriate format
        for boolean queries.
    max_results : int
        The number of returned results.
    strategy : str
        One of "boolean" or "tfidf".
        
    """
    if strategy == "boolean":
        return boolean_query(querystring, max_results)
    elif strategy == "tfidf":
        return tfidf_query(querystring, max_results)


def execute_chained_booleans(result, ops):
    """Executes a sequence of boolean operations stored in `ops` on the
    matching documents of each query term (left to right precendence).

    Parameters
    ----------
    result : set
        Current result set of matching documents.
    ops : list
        A list of alternating boolean operators and query terms, e.g.:
        ["or", "religion", "and", "science] , this will execute the query
        "religion AND science".  The first operator is dummy and will
        always be an "or" (neutral).

    Returns
    -------
    set
        A set of matching document id's.
    """
    if not ops:
        return result
    else:
        set_op = lambda s, x, y: (x == "and" and s.intersection_update(y)) \
                                  or (x == "or" and s.update(y))
        set_op(result, ops.pop(), inverted_index.get(ops.pop(), set()))
        return execute_chained_booleans(result, ops)


def boolean_query(querystring, max_results):
    """Executes a boolean query and returns a list of matching documents.

    Transforms the query string to a list of boolean operators and terms, for
    left to right execuion.  It returns the top `max_results` documents from the
    result set of these boolean operators.

    Parameters
    ----------
    querystring : str
        A query string. It should have the following format: 
        <word> <OP> <word> <OP> <word> , where <word> is a single term
        and <OP> is one of "AND" or "OR" (or lowercase).
    max_results : int
        The number of returned documents.
    
    Returns
    -------
    list
        A list of matched document id's.

    """
    ops = ["or"] + tokenize(querystring)
    ops.reverse()
    if len(ops) % 2 != 0:
        print "error: wrong query format? should be: word OP word OP .."
        return
    result_set = execute_chained_booleans(set(), ops)
    return list(result_set)[:max_results]


def tfidf_query(querystring, max_results):
    """Retrieves the top `max_results` documents based on their aggregated
    TF-IDF score.

    As an optimization it firstly retrieves all the documents that contain
    at least one query term.  Then it calculates the TF-IDF score of each
    document as the TF-IDF sum of the query terms that it contains.  Final
    step is to retrieve the top matching documents.

    In order to avoid a large sorting operation with O(n logn) cost, it uses
    a min-heap of size `max_results` to keep the top documents.  In the end
    the heap is sorted which in total yields a cost of O(n logk) + O(k logk),
    where k is equal to `max_results`.  For large n this would yield great
    computational and memory benefits.

    Parameters
    ----------
    querystring : str
        A query string.
    max_results : int
        The number of returned documents.
    
    Returns
    -------
    list
        A list of matching document id's.

    """
    candidates = reduce(set.union,
                        [inverted_index.get(w, set())
                         for w in tokenize(querystring)])
    result_set = []
    for c in candidates:
        score = sum(tfidf(w, c) for w in tokenize(querystring))
        if len(result_set) < max_results:
            heappush(result_set, (score, c))
        elif score > result_set[0]:
            heapreplace(resultset, (score, c))
    result_set.sort(reverse=True)
    return [r[1] for r in result_set]
    

def tfidf(word, docid):
    """Returns a term's TF-IDF score with respect to a document. """
    return tf(word, docid) * idf(word)


def tf(word, docid):
    """Returns a term's frequency with respect to a document. """
    return dataset[docid]["counts"].get(word, 0) / float(dataset[docid]["length"])


def idf(word):
    """Returns a term's inverse document frequency. """
    return math.log(len(dataset)) / (1.0 + len(inverted_index.get(word, [])))
