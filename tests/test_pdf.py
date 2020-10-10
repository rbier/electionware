from unittest import TestCase
from unittest.mock import call, patch

from pdfreader import PageDoesNotExist

from electionware.pdf import PDFStringsIterator, PDFStrings, PDFPageIterator


class TestPDFStringIterator(TestCase):
    def test__pdf_strings(self):
        pdf_string_iterator = PDFStringsIterator(['A', 'B', 'C', 'D'])
        self.assertTrue(pdf_string_iterator.has_next())
        self.assertEqual(pdf_string_iterator.peek(), 'A')
        self.assertEqual(next(pdf_string_iterator), 'A')
        self.assertEqual(pdf_string_iterator.peek(), 'B')
        self.assertTrue(pdf_string_iterator.has_next())
        self.assertEqual(pdf_string_iterator.peek(), 'B')
        self.assertEqual(next(pdf_string_iterator), 'B')
        self.assertEqual(pdf_string_iterator.peek(), 'C')
        self.assertTrue(pdf_string_iterator.has_next())
        self.assertEqual(pdf_string_iterator.peek(), 'C')
        self.assertEqual(next(pdf_string_iterator), 'C')
        self.assertEqual(pdf_string_iterator.peek(), 'D')
        self.assertTrue(pdf_string_iterator.has_next())
        self.assertEqual(pdf_string_iterator.peek(), 'D')
        self.assertEqual(next(pdf_string_iterator), 'D')
        with self.assertRaises(IndexError):
            pdf_string_iterator.peek()
        self.assertFalse(pdf_string_iterator.has_next())
        with self.assertRaises(StopIteration):
            next(pdf_string_iterator)

    def test__pdf_strings_iterator(self):
        pdf_string_iterator = PDFStringsIterator(['A', 'B', 'C', 'D'])
        for expected, actual in zip(['A', 'B', 'C', 'D'], pdf_string_iterator):
            self.assertEqual(expected, actual)


class TestPDFStrings(TestCase):
    def test__pdf_strings(self):
        with patch('pdfreader.SimplePDFViewer') as mock:
            mock.current_page_number = 3
            mock.canvas.strings = ['A', 'B', 'C', 'D']
            pdf_strings = PDFStrings(mock)
            self.assertEqual(pdf_strings.get_page_number(), 3)
            self.assertEqual(pdf_strings.get_strings(), ['A', 'B', 'C', 'D'])

    def test__pdf_strings_no_reload(self):
        with patch('pdfreader.SimplePDFViewer') as mock:
            pdf_strings = PDFStrings(mock)
            for i in range(5):
                pdf_strings.get_strings()
            expected_calls = [call.render()]
            self.assertEqual(mock.mock_calls, expected_calls)


class TestPDFPageIterator(TestCase):
    def test__pdf_page_iterator(self):
        with patch('pdfreader.SimplePDFViewer') as mock:
            pdf_page_iterator = PDFPageIterator(pdf_viewer=mock)
            pdf_strings = next(pdf_page_iterator)
            pdf_strings.get_strings()
            expected_calls = [call.__bool__(), call.next(), call.render()]
            self.assertEqual(mock.mock_calls, expected_calls)
            mock.next.side_effect = PageDoesNotExist
            with self.assertRaises(StopIteration):
                next(pdf_page_iterator)
            self.assertEqual(0, len([page for page in pdf_page_iterator]))
