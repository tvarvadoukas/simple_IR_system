"""
A driver program for the `search_engine.py` API that allows for
real-time querying.

When this module is executed, then an interactive shell will appear where
one can enter queries and choose the query strategy or configure the number
of returned results.  For examples of usage of this shell, please check the
README file in the same directory.

"""
from time import time
import search_engine as SE


def print_results(docids):
    """Displays the filenames of the matched documents with id's in
    `docids`.

    Parameters
    ----------
    docids : list
        List of document id's.
    """
    print "\n".join([SE.dataset[d]["filename"] for d in docids])


def run_cmd(strategy="boolean", max_results=10):
    """A dummy interactive shell for real-time querying.  It allows for
    setting the query strategy and the number of returned results on the fly,
    so as to avoid re-building the index.  Look at the README file for
    examples of usage.
    """
    while True:
        querystring = raw_input("> ")
        args = querystring.split()
        if len(args) == 0:
            continue
        elif args[0] == "/set_strategy":
            if len(args) == 1:
                print "error: missing argument"
            else:
                if args[1] not in ("tfidf", "boolean"):
                    print "error: unrecognised strategy"
                else:
                    strategy = args[1]
        elif args[0] == "/set_max_results":
            if len(args) == 1:
                print "error: missing argument"
            else:
                try:
                    if int(args[1]) >= 1:
                        max_results = int(args[1])
                    else:
                        print "error: you should get at least 1 result!"
                except ValueError:
                    print "error: arg should be an integer"
        elif args[0] == "/show_options":
            print "strategy: %s, max_results: %d" % (strategy, max_results)
        else:  # actual querying!
            query_start_time = time()
            result = SE.query(querystring, max_results, strategy)
            print_results(result)
            print "(query took %.4f seconds)" % (time() - query_start_time)


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print "Usage: %s <path_to_dataset_dir>" % sys.argv[0]
        sys.exit()
    root_path = sys.argv[1]

    print "Building the index ..."
    start_indexing = time()
    SE.build_index(root_path)  # indexing of the dataset
    print "Finished indexing in %d seconds." % \
          (time() - start_indexing)
    print "Dataset / Inverted index size: %d / %d" % \
          (len(SE.dataset), len(SE.inverted_index))
    run_cmd()  # interactive shell
