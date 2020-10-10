from typing import IO, Iterator, List

from pdfreader import SimplePDFViewer, PageDoesNotExist


class PDFStringsIterator(Iterator[str]):
    """
    Given a list of strings, wraps it in a basic iterator, but
    with an additional peek() and has_next() functionality. This
    is useful in PDFs because it is unclear where boundaries of
    tables, rows, cells, etc. are -- we are able to peek at the
    next item and determine if it marks the beginning of a new
    block of content. Also, it is possible for some elements of
    a PDF to be out of order, so this enables features for
    re-ordering flagged item blocks.
    """
    def __init__(self, strings: List[str]):
        self._strings: List[str] = strings
        self._strings_offset: int = 0

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        if not self.has_next():
            raise StopIteration
        s: str = self.peek()
        self._strings_offset += 1
        return s

    def peek(self) -> str:
        return self._strings[self._strings_offset]

    def has_next(self) -> bool:
        return self._strings_offset < len(self._strings)


class PDFStrings:
    """
    Lazy loaded PDF strings for a given PDF page. The lazy load
    is because the PDF rendering can take significant time, so
    if a page should be skipped, we don't automatically trigger
    the render.
    """
    def __init__(self, pdf_viewer: SimplePDFViewer):
        self._pdf_viewer: SimplePDFViewer = pdf_viewer
        self._rendered: bool = False

    def get_page_number(self) -> int:
        return self._pdf_viewer.current_page_number

    def get_strings(self) -> List[str]:
        if not self._rendered:
            self._pdf_viewer.render()
            self._rendered = True
        return self._pdf_viewer.canvas.strings


class PDFPageIterator(Iterator[PDFStrings]):
    """
    Given an IO object, the PDFPageIterator loads it as a PDF,
    then iterates over each page of the PDF and provides the
    associated string representation of the current PDF page.
    """
    def __init__(self, f_obj: IO=None, pdf_viewer: SimplePDFViewer=None):
        self._pdf_viewer = pdf_viewer or SimplePDFViewer(f_obj)
        self._pdf_viewer.current_page_number = 0

    def __iter__(self) -> Iterator[PDFStrings]:
        return self

    def __next__(self) -> PDFStrings:
        try:
            self._pdf_viewer.next()
            return PDFStrings(self._pdf_viewer)
        except PageDoesNotExist as e:
            raise StopIteration(e)
