Purpose
-------
Simple in-memory IR system that supports boolean and TFIDF-based queries.

The boolean queries are single terms connected with the boolean operators
OR or AND (or lowercase). The top matching documents are retrieved, but there
is no notion of ranking.

TF-IDF queries can be more generic search phrases (no specific format) and the
documents are ranked based on their matching score (the higher the better).

The code style (on purpose) is generally Pythonic but with a few functional
elements (map, reduce, lambdas, recursion, iterators and generators). It is
an exercise of applying functional style, but Python seems to lack a lot of
features for creating "nice" functional features (e.g. high order functions
or monads). This often leads to code more complicated than imperative
progrmaming (also due to the imbalance of my experience for the two styles).
In any case, performance was not sacrificed for styling (sorry :)).


Assumptions
-----------
* Since it is an in-memory IR system, the first assumption is that it'd work
for small-scale data that fit into memory (e.g. the newsgroup dataset that
we showcase below).

Although a larger-scale approach wouldn't change much in logic, the
difference in storage might require the employment of different algorithms
for querying or storage/compression and data structures (e.g. sets vs. lists).

* Second assumption/constraint is that boolean queries would have the proper
format. The parsing code doesn't account for tricky inputs.


Files
-----
`search_engine.py`:
    API of the IR system. Contains functions for indexing and retrieval.

`main.py`:
    A driver program for the `search_engine.py` that also provides an
    interactive shell for real-time querying, so as to avoid re-indexing
    the dataset.


Ideas for future improvements
-----------------------------
#### Code
* Consistent styling. Add tests and logging.

* Add flexibility in changing tokenizers and adding other pre-processing
  steps e.g. stemming, stopwords removal. In case of OOP this would need
  better modelling.

#### Domain specific (newsgroup dataset)
* Parse the e-mails and index only the subjects and bodies. Headers and
  other fields seem to contain many important (topically) words and scew the
  scores.

* Indexes: add ability to create secondary and other indexes. For example, one
  could have a separate index for message bodies and another one for the subjects
  of e-mails. This would give different scores depending on where a word is
  contained. A difficult step afterwards is to integreate scores from different
  indexes.

* Exploit the implicit structure (hierarchy) of the dataset to create labeled
  clusters. Then one could create many ML solutions on this dataset. An example
  is the probabilistic framework where one models the probability
  `P(relevance | document)`.

#### Algorithms and data structures
* Query parsing: rewrite the boolean query using associative rules and start
  from "AND" queries. This would create smaller sets before OR'ing them, which
  overall might offer speed gains since set operations run typically in 
  O(min(|set_1|, |set_2|)).

* Query expansion (pseudo-relevance feedback): one might want to expand the
  query by adding the top terms from the top matching documents (assuming they
  are relevant) and re-run the search. This would enforce power local search,
  which generally works pretty well (better than a global - see TREC evaluations).
  A disadvantage is the so called "query drift", when the relevance assumption
  fails.

* TF-IDF score: the typical definition of TF-IDF is a bit problematic for large
  documents that contain many times specific terms. There are variants that
  penalize more the length of a document as a function of the average document
  length in the dataset. An example of this is the BM25's ranking function:

    https://en.wikipedia.org/wiki/Okapi_BM25#The_ranking_function

* For larger queries/docs: change the execution strategy from doc-at-a-time
  to term-at-a-time. The latter is faster in practice for metrics like TF-IDF
  and also due to sequential scans of the disk (disk-based inverted index).

* For larger docs: change data structures to disk-based.


Examples of usage (interactive shell + newsgroup dataset)
---------------------------------------------------------
For this example we'll use the newgroup dataset. One can find it here:

http://qwone.com/~jason/20Newsgroups/20news-19997.tar.gz

After decompressing it, we assume that the directory lies in the current
directory and is named "20Newsgroups". Now one can index it by running:

```
$ python main.py 20_newsgroups/
Building the index ...
Finished indexing in 15 seconds.
Dataset / Inverted index size: 19997 / 203943
> 
```

Now the shell waits for queries or commands. The available commands configure
the parameters `strategy` and `max_results`. List of commands:
    
- `/show_options: shows the current values of the parameters`
- `/set_strategy <strategy>: sets the strategy ("boolean" or "tfidfd")`
- `/set_max_results <number>: sets the number of returned results (default=10)`

Continuing the example:

```
> /show_options
strategy: boolean, max_results: 10
> science
20_newsgroups/rec.sport.baseball/105163
20_newsgroups/alt.atheism/51172
20_newsgroups/soc.religion.christian/21483
20_newsgroups/alt.atheism/54256
20_newsgroups/comp.sys.ibm.pc.hardware/61035
20_newsgroups/alt.atheism/51135
20_newsgroups/alt.atheism/53622
20_newsgroups/rec.motorcycles/104381
20_newsgroups/alt.atheism/54194
20_newsgroups/rec.sport.baseball/102624
(query took 0.0005 seconds)
> /set_max_results 5
> /show_options
strategy: boolean, max_results: 5
> science OR religion
20_newsgroups/soc.religion.christian/20553
20_newsgroups/soc.religion.christian/21415
20_newsgroups/alt.atheism/51172
20_newsgroups/soc.religion.christian/20917
20_newsgroups/soc.religion.christian/20634
(query took 0.0007 seconds)
> science AND religion
20_newsgroups/talk.politics.misc/178315
20_newsgroups/talk.religion.misc/83879
20_newsgroups/talk.politics.mideast/77377
20_newsgroups/soc.religion.christian/21483
20_newsgroups/alt.atheism/53615
(query took 0.0005 seconds)
```

And few TF-IDF based:

```
> /set_strategy tfidf
> /show_options
strategy: tfidf, max_results: 5
> /show_options
strategy: tfidf, max_results: 5
> terrorism cia
20_newsgroups/talk.politics.misc/178602
20_newsgroups/sci.crypt/15611
20_newsgroups/talk.politics.mideast/77377
20_newsgroups/talk.religion.misc/83945
20_newsgroups/talk.politics.mideast/76468
(query took 0.0032 seconds)
> hackers cyberwar
20_newsgroups/sci.crypt/15480
20_newsgroups/sci.crypt/15476
20_newsgroups/sci.crypt/15860
20_newsgroups/comp.graphics/39629
20_newsgroups/comp.os.ms-windows.misc/10606
(query took 0.0011 seconds)
```
