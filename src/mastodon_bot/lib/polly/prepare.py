from bs4 import BeautifulSoup, Tag


class PollyPrepare:

    def __init__(self, html):
        self.html = html
        self.elements_to_find = [
          'a',
          'abbr',
          'b',
          'blockquote',
          'button',
          'cite',
          'code',
          'data',
          'del',
          'dfn',
          'em',
          'h1',
          'h2',
          'h3',
          'h4',
          'h5',
          'h6',
          'i',
          'ins',
          'kbd',
          'label',
          'mark',
          'output',
          'p',
          'q',
          's',
          'samp',
          'small',
          'span',
          'strong',
          'sub',
          'sup',
          'time',
          'u',
          'var',
          'ul'
          'ol'
        ]

    def parse(self):
        # Load HTML content into BeautifulSoup
        soup = BeautifulSoup(self.html, 'html.parser')
        body = soup.find("body")

        # Remove unsupported HTML tags and attributes
        unsupported_tags = ['script', 'style']
        for tag in body(unsupported_tags):
            tag.extract()

        # Convert HTML elements to SSML equivalents
        # ssml = ''.join(self.process_element(child) for child in soup.children)
        ssml = ""
        for child in body.find_all(self.elements_to_find):
            try:
                child_ssml = self.process_element(child)
                if child_ssml is not None:
                    ssml += child_ssml
            except Exception as e:
                print(type(child))
                print(e)

        return ssml

    def process_element(self, element):
        # if element.name is None:
        #     if element.string:
        #         return element.string.strip()
        # # elif element.children is None:
        # #     return element.text
        # else:
            #tag = Tag(name=element.name)
        if element.name == 'p':
            return "<p>" + element.text.strip() + "</p>"
        elif element.name == 'strong' or element.name == 'b':
            return "<emphasis level='strong'>" + element.text.strip() + "</emphasis>"
        elif element.name == 'em' or element.name == 'i':
            return "<emphasis level='moderate'>" + element.text.strip() + "</emphasis>"
        elif element.name.startswith('h'):
            return "<emphasis level='strong'>" + element.text.strip() + "</emphasis>"
        elif element.name == 'ul' or element.name == 'ol':
            list_tag = 'ul' if element.name == 'ul' else 'ol'
            list_items = ''.join(
                "<li>" + child.text.strip() + "</li>" for child in element.find_all(["li"]) if child.string)
            return f"<{list_tag}>{list_items}</{list_tag}>"
        elif element.name == "span":
            return "<p>" + element.text.strip() + "</p>"
        else:
          if element.text and not element.children:
              return element.text.strip()
            
