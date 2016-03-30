from datetime import datetime
from email.utils import parseaddr
from six.moves import html_parser
import logging
logger = logging.getLogger(__name__)

from dateutil import parser
import pytz

class CommonChange(object):
    '''Common methods for handling material changes.'''
    def set_revision(self):
        self.revision = self.text_from_class('revision')
        logger.debug('adding change revision %s',self.revision)

    def href_from_class(self, class_name):
        '''Get first href link from a td with the named class.'''
        return(
                self.change.find(
                    'td[@class="'+class_name+'"]'
                    ).find('a').attrib['href']
                )

    def text_from_class(self, class_name):
        '''Get joined, stripped text from a td with the named class.'''
        return(
                ''.join(self.change.find(
                    'td[@class="'+class_name+'"]'
                    ).itertext()).strip()
                )

    def to_epoch(self, string):
        parsed_date = parser.parse(string)

        # strftime('%s') is not portable?
        # http://stackoverflow.com/questions/11743019/convert-python-datetime-to-epoch-with-strftime
        converted = int(
                (parsed_date - datetime(1970,1,1).replace(tzinfo = pytz.utc)).total_seconds()
                )

        logger.debug('string %s converted to epoch %d',string, converted)

        return converted

class GitChange(CommonChange):
    '''Add information about a git change from a GoCD material.'''
    def __init__(self, change):
        self.change = change

        self.set_revision()

        # Kurt Yoder <kurt@example.xyz>                                        2016-03-19T21:41:10+00:00
        modified_by_text = self.text_from_class('modified_by')
        logger.debug("change modifier text: %s",modified_by_text)
        parts = modified_by_text.split()
        assert len(parts) > 2
        self.modifier_time = self.to_epoch(parts.pop())
        modifier_info = convert_tags(' '.join(parts))
        (self.modifier_name, self.modifier_email) = parseaddr(modifier_info)

        comment = convert_tags(self.text_from_class('comment'))
        logger.debug("change comment: %s",comment)
        self.comment = comment

class PipelineChange(CommonChange):
    '''Add information about a pipeline change from a GoCD material.'''
    def __init__(self, change):
        self.change = change

        self.set_revision()

        self.revision_url = self.href_from_class('revision')

        self.label = self.text_from_class('label')
        self.label_url = self.href_from_class('label')

        self.completed = self.to_epoch( self.text_from_class('completed_at') )

def convert_tags(text):
    '''GoCD leaves errant partial tags in some of its output. Strip them out of
    the given text.'''
    # ignoring Python 3.4, because reasons
    # http://stackoverflow.com/questions/2087370/decode-html-entities-in-python-string
    return html_parser.HTMLParser().unescape(text)
