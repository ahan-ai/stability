.PHONY: all clean book.pdf

all: book.pdf

book.pdf:
	python build_epub.py

clean:
	rm -rf build images/cache book.epub
