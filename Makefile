.PHONY: all clean book.pdf

all: book.pdf

book.pdf:
	python3 build_ebook.py

clean:
	rm -rf build images/cache book.pdf 
