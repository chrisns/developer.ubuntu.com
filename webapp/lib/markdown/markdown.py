from __future__ import absolute_import

import frontmatter
import markdown as _markdown

from django.conf import settings
from django.template import loader
from django.template import TemplateDoesNotExist

from .extensions.vanilla_toc import VanillaTocExtension


markdown_extensions = [
    'markdown.extensions.attr_list',
    'markdown.extensions.def_list',
    'markdown.extensions.fenced_code',
    'markdown.extensions.meta',
    'markdown.extensions.tables',
    'mdx_callouts',
    'mdx_anchors_away',
    'mdx_foldouts',
    VanillaTocExtension(marker=''),
]


def parse_frontmatter(markdown_content):
    metadata = {}
    try:
        file_parts = frontmatter.loads(markdown_content)
        metadata = file_parts.metadata
    except (ScannerError, ParserError):
        """
        If there's a parsererror, it's because frontmatter had to parse
        the entire file (not finding frontmatter at the top)
        and encountered an unexpected format somewhere in it.
        This means the file has no frontmatter, so we can simply continue.
        """
        pass
    return metadata


def get_markdown_with_parser(markdown_content):
    metadata = {}
    try:
        file_parts = frontmatter.loads(markdown_content)
        metadata = file_parts.metadata
        markdown_content = file_parts.content
    except (ScannerError, ParserError):
        """
        If there's a parsererror, it's because frontmatter had to parse
        the entire file (not finding frontmatter at the top)
        and encountered an unexpected format somewhere in it.
        This means the file has no frontmatter, so we can simply continue.
        """
        pass


    markdown_parser = _markdown.Markdown(extensions=markdown_extensions)
    parsed_markdown = markdown_parser.convert(markdown_content)
    table_of_contents = markdown_parser.toc
    if table_of_contents:
        metadata['table_of_contents'] = table_of_contents
    return markdown_parser, parsed_markdown, metadata


def parse_markdown(markdown_content):
    parser, parsed_markdown, metadata = get_markdown_with_parser(
        markdown_content
    )
    return parsed_markdown, metadata


def get_page_data(pages, root_path=None):
    template_root = ''.join([
        getattr(settings, 'TEMPLATE_FINDER_PATH', ''), '/'
    ])

    page_data = []
    for path in pages:
        # If trying to lookup relative path
        if root_path and not path.startswith('/'):
            path = '/'.join([root_path, path])
        # We don't need any slashes at the ends
        path.strip('/')

        template_paths = [
            ''.join([template_root, path, '.md']),
        ]
        try:
            template = loader.select_template(template_paths)
            template_path = template.origin.name
        except TemplateDoesNotExist:
            raise Exception("Can't find template metadata for: %s" % path)

        with open(template.origin.name, 'r') as f:
            metadata = parse_frontmatter(f.read())
            metadata['path'] = path
            page_data.append(metadata)

    return page_data
