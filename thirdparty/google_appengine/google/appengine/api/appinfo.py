#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#




"""AppInfo tools.

Library for working with AppInfo records in memory, store and load from
configuration files.
"""









import os
import logging
import re
import string
import wsgiref.util

if os.environ.get('APPENGINE_RUNTIME') == 'python27':
  from google.appengine.api import pagespeedinfo
  from google.appengine.api import validation
  from google.appengine.api import yaml_builder
  from google.appengine.api import yaml_listener
  from google.appengine.api import yaml_object
else:

  from google.appengine.api import pagespeedinfo
  from google.appengine.api import validation
  from google.appengine.api import yaml_builder
  from google.appengine.api import yaml_listener
  from google.appengine.api import yaml_object

from google.appengine.api import appinfo_errors
from google.appengine.api import backendinfo




_URL_REGEX = r'(?!\^)/.*|\..*|(\(.).*(?!\$).'
_FILES_REGEX = r'(?!\^).*(?!\$).'
_URL_ROOT_REGEX = r'/.*'


_DELTA_REGEX = r'([0-9]+)([DdHhMm]|[sS]?)'
_EXPIRATION_REGEX = r'\s*(%s)(\s+%s)*\s*' % (_DELTA_REGEX, _DELTA_REGEX)
_START_PATH = '/_ah/start'




_ALLOWED_SERVICES = ['mail', 'mail_bounce', 'xmpp_message', 'xmpp_subscribe',
                     'xmpp_presence', 'xmpp_error', 'channel_presence', 'rest',
                     'warmup']
_SERVICE_RE_STRING = '(' + '|'.join(_ALLOWED_SERVICES) + ')'


_PAGE_NAME_REGEX = r'^.+$'


_EXPIRATION_CONVERSIONS = {
    'd': 60 * 60 * 24,
    'h': 60 * 60,
    'm': 60,
    's': 1,
}



APP_ID_MAX_LEN = 100
SERVER_ID_MAX_LEN = 63



SERVER_VERSION_ID_MAX_LEN = 63
MAX_URL_MAPS = 100


PARTITION_SEPARATOR = '~'


DOMAIN_SEPARATOR = ':'


VERSION_SEPARATOR = '.'


SERVER_SEPARATOR = ':'


DEFAULT_SERVER = 'default'



PARTITION_RE_STRING = (r'[a-z\d\-]{1,%d}\%s' %
                       (APP_ID_MAX_LEN, PARTITION_SEPARATOR))
DOMAIN_RE_STRING = (r'(?!\-)[a-z\d\-\.]{1,%d}%s' %
                    (APP_ID_MAX_LEN, DOMAIN_SEPARATOR))
DISPLAY_APP_ID_RE_STRING = r'(?!-)[a-z\d\-]{0,%d}[a-z\d]' % (APP_ID_MAX_LEN - 1)
APPLICATION_RE_STRING = (r'(?:%s)?(?:%s)?%s' %
                         (PARTITION_RE_STRING,
                          DOMAIN_RE_STRING,
                          DISPLAY_APP_ID_RE_STRING))

SERVER_ID_RE_STRING = r'^(?!-)[a-z\d\-]{0,%d}[a-z\d]$' % (SERVER_ID_MAX_LEN - 1)






SERVER_VERSION_ID_RE_STRING = (r'^(?!-)[a-z\d\-]{0,%d}[a-z\d]$' %
                               (SERVER_VERSION_ID_MAX_LEN - 1))

_IDLE_INSTANCES_REGEX = r'^([\d]+|automatic)$'
_INSTANCES_REGEX = r'^[\d]+$'
_INSTANCE_CLASS_REGEX = r'^([sS](1|2|4|8))$'




_PENDING_LATENCY_REGEX = r'^(\d+((\.\d{1,3})?s|ms)|automatic)$'

_IDLE_TIMEOUT_REGEX = r'^[\d]+(s|m)$'

ALTERNATE_HOSTNAME_SEPARATOR = '-dot-'


BUILTIN_NAME_PREFIX = 'ah-builtin'

RUNTIME_RE_STRING = r'[a-z][a-z0-9]{0,29}'

API_VERSION_RE_STRING = r'[\w.]{1,32}'

SOURCE_LANGUAGE_RE_STRING = r'[\w.\-]{1,32}'

HANDLER_STATIC_FILES = 'static_files'
HANDLER_STATIC_DIR = 'static_dir'
HANDLER_SCRIPT = 'script'
HANDLER_API_ENDPOINT = 'api_endpoint'

LOGIN_OPTIONAL = 'optional'
LOGIN_REQUIRED = 'required'
LOGIN_ADMIN = 'admin'

AUTH_FAIL_ACTION_REDIRECT = 'redirect'
AUTH_FAIL_ACTION_UNAUTHORIZED = 'unauthorized'

SECURE_HTTP = 'never'
SECURE_HTTPS = 'always'
SECURE_HTTP_OR_HTTPS = 'optional'

SECURE_DEFAULT = 'default'

REQUIRE_MATCHING_FILE = 'require_matching_file'

DEFAULT_SKIP_FILES = (r'^(.*/)?('
                      r'(#.*#)|'
                      r'(.*~)|'
                      r'(.*\.py[co])|'
                      r'(.*/RCS/.*)|'
                      r'(\..*)|'
                      r')$')

DEFAULT_NOBUILD_FILES = (r'^$')


LOGIN = 'login'
AUTH_FAIL_ACTION = 'auth_fail_action'
SECURE = 'secure'
URL = 'url'
POSITION = 'position'
POSITION_HEAD = 'head'
POSITION_TAIL = 'tail'
STATIC_FILES = 'static_files'
UPLOAD = 'upload'
STATIC_DIR = 'static_dir'
MIME_TYPE = 'mime_type'
SCRIPT = 'script'
EXPIRATION = 'expiration'
API_ENDPOINT = 'api_endpoint'
HTTP_HEADERS = 'http_headers'


APPLICATION = 'application'
SERVER = 'server'
AUTOMATIC_SCALING = 'automatic_scaling'
MANUAL_SCALING = 'manual_scaling'
BASIC_SCALING = 'basic_scaling'
VM_SETTINGS = 'vm_settings'
VERSION = 'version'
MAJOR_VERSION = 'major_version'
MINOR_VERSION = 'minor_version'
RUNTIME = 'runtime'
API_VERSION = 'api_version'
SOURCE_LANGUAGE = 'source_language'
BUILTINS = 'builtins'
INCLUDES = 'includes'
HANDLERS = 'handlers'
LIBRARIES = 'libraries'
DEFAULT_EXPIRATION = 'default_expiration'
SKIP_FILES = 'skip_files'
NOBUILD_FILES = 'nobuild_files'
SERVICES = 'inbound_services'
DERIVED_FILE_TYPE = 'derived_file_type'
JAVA_PRECOMPILED = 'java_precompiled'
PYTHON_PRECOMPILED = 'python_precompiled'
ADMIN_CONSOLE = 'admin_console'
ERROR_HANDLERS = 'error_handlers'
BACKENDS = 'backends'
THREADSAFE = 'threadsafe'
API_CONFIG = 'api_config'
CODE_LOCK = 'code_lock'
ENV_VARIABLES = 'env_variables'
PAGESPEED = 'pagespeed'

INSTANCE_CLASS = 'instance_class'

MINIMUM_PENDING_LATENCY = 'min_pending_latency'
MAXIMUM_PENDING_LATENCY = 'max_pending_latency'
MINIMUM_IDLE_INSTANCES = 'min_idle_instances'
MAXIMUM_IDLE_INSTANCES = 'max_idle_instances'


INSTANCES = 'instances'


MAX_INSTANCES = 'max_instances'
IDLE_TIMEOUT = 'idle_timeout'


PAGES = 'pages'
NAME = 'name'


ERROR_CODE = 'error_code'
FILE = 'file'
_ERROR_CODE_REGEX = r'(default|over_quota|dos_api_denial|timeout)'


ON = 'on'
ON_ALIASES = ['yes', 'y', 'True', 't', '1', 'true']
OFF = 'off'
OFF_ALIASES = ['no', 'n', 'False', 'f', '0', 'false']


class _VersionedLibrary(object):
  """A versioned library supported by App Engine."""

  def __init__(self,
               name,
               url,
               description,
               supported_versions,
               default_version=None,
               deprecated_versions=None,
               experimental_versions=None):
    """Initializer for _VersionedLibrary.

    Args:
      name: The name of the library e.g. "django".
      url: The URL for the library's project page e.g.
          "http://www.djangoproject.com/".
      description: A short description of the library e.g. "A framework...".
      supported_versions: A list of supported version names ordered by release
          date e.g. ["v1", "v2", "v3"].
      default_version: The version of the library that is enabled by default
          in the Python 2.7 runtime or None if the library is not available by
          default e.g. "v1".
      deprecated_versions: A list of the versions of the library that have been
          deprecated e.g. ["v1", "v2"].
      experimental_versions: A list of the versions of the library that are
          current experimental e.g. ["v1"].
    """
    self.name = name
    self.url = url
    self.description = description
    self.supported_versions = supported_versions
    self.default_version = default_version
    self.deprecated_versions = deprecated_versions or []
    self.experimental_versions = experimental_versions or []

  @property
  def non_deprecated_versions(self):
    return [version for version in self.supported_versions
            if version not in self.deprecated_versions]


_SUPPORTED_LIBRARIES = [
    _VersionedLibrary(
        'django',
        'http://www.djangoproject.com/',
        'A full-featured web application framework for Python.',
        ['1.2', '1.3', '1.4'],
        experimental_versions=['1.4']
        ),
    _VersionedLibrary(
        'jinja2',
        'http://jinja.pocoo.org/docs/',
        'A modern and designer friendly templating language for Python.',
        ['2.6']),
    _VersionedLibrary(
        'lxml',
        'http://lxml.de/',
        'A Pythonic binding for the C libraries libxml2 and libxslt.',
        ['2.3']),
    _VersionedLibrary(
        'markupsafe',
        'http://pypi.python.org/pypi/MarkupSafe',
        'A XML/HTML/XHTML markup safe string for Python.',
        ['0.15']),
    _VersionedLibrary(
        'matplotlib',
        'http://matplotlib.sourceforge.net/',
        'A 2D plotting library which produces publication-quality figures.',
        ['1.1.1'],
        experimental_versions=['1.1.1']
        ),
    _VersionedLibrary(
        'numpy',
        'http://numpy.scipy.org/',
        'A general-purpose library for array-processing.',
        ['1.6.1']),
    _VersionedLibrary(
        'PIL',
        'http://www.pythonware.com/library/pil/handbook/',
        'A library for creating and transforming images.',
        ['1.1.7']),
    _VersionedLibrary(
        'PyAMF',
        'http://www.pyamf.org/',
        'A library that provides (AMF) Action Message Format functionality.',
        ['0.6.1']),
    _VersionedLibrary(
        'pycrypto',
        'https://www.dlitz.net/software/pycrypto/',
        'A library of cryptogoogle.appengine._internal.graphy functions such as random number generation.',
        ['2.3', '2.6'],
        ),
    _VersionedLibrary(
        'setuptools',
        'http://pypi.python.org/pypi/setuptools',
        'A library that provides package and module discovery capabilities.',
        ['0.6c11']),
    _VersionedLibrary(
        'ssl',
        'http://docs.python.org/dev/library/ssl.html',
        'The SSL socket wrapper built-in module.',
        ['2.7'],
        experimental_versions=['2.7']),
    _VersionedLibrary(
        'webapp2',
        'http://webapp-improved.appspot.com/',
        'A lightweight Python web framework.',
        ['2.3', '2.5.1', '2.5.2'],
        default_version='2.3',
        deprecated_versions=['2.3']
        ),
    _VersionedLibrary(
        'webob',
        'http://www.webob.org/',
        'A library that provides wrappers around the WSGI request environment.',
        ['1.1.1', '1.2.3'],
        default_version='1.1.1',
        experimental_versions=['1.2.3']
        ),
    _VersionedLibrary(
        'yaml',
        'http://www.yaml.org/',
        'A library for YAML serialization and deserialization.',
        ['3.10'],
        default_version='3.10'
        ),
    ]

_NAME_TO_SUPPORTED_LIBRARY = dict((library.name, library)
                                  for library in _SUPPORTED_LIBRARIES)



REQUIRED_LIBRARIES = {
    ('jinja2', '2.6'): [('markupsafe', '0.15'), ('setuptools', '0.6c11')],
    ('jinja2', 'latest'): [('markupsafe', 'latest'), ('setuptools', 'latest')],
}

_USE_VERSION_FORMAT = ('use one of: "%s" or "latest" '
                       '("latest" recommended for development only)')



_HTTP_SEPARATOR_CHARS = frozenset('()<>@,;:\\"/[]?={} \t')
_HTTP_TOKEN_CHARS = frozenset(string.printable[:-5]) - _HTTP_SEPARATOR_CHARS
_HTTP_TOKEN_RE = re.compile('[%s]+$' % re.escape(''.join(_HTTP_TOKEN_CHARS)))


_HTTP_REQUEST_HEADERS = frozenset([
    'accept',
    'accept-charset',
    'accept-encoding',
    'accept-language',
    'authorization',
    'expect',
    'from',
    'host',
    'if-match',
    'if-modified-since',
    'if-none-match',
    'if-range',
    'if-unmodified-since',
    'max-forwards',
    'proxy-authorization',
    'range',
    'referer',
    'te',
    'user-agent',
])



_MAX_COOKIE_LENGTH = 4096



_MAX_URL_LENGTH = 2047


class HandlerBase(validation.Validated):
  """Base class for URLMap and ApiConfigHandler."""
  ATTRIBUTES = {

      URL: validation.Optional(_URL_REGEX),
      LOGIN: validation.Options(LOGIN_OPTIONAL,
                                LOGIN_REQUIRED,
                                LOGIN_ADMIN,
                                default=LOGIN_OPTIONAL),

      AUTH_FAIL_ACTION: validation.Options(AUTH_FAIL_ACTION_REDIRECT,
                                           AUTH_FAIL_ACTION_UNAUTHORIZED,
                                           default=AUTH_FAIL_ACTION_REDIRECT),

      SECURE: validation.Options(SECURE_HTTP,
                                 SECURE_HTTPS,
                                 SECURE_HTTP_OR_HTTPS,
                                 SECURE_DEFAULT,
                                 default=SECURE_DEFAULT),


      HANDLER_SCRIPT: validation.Optional(_FILES_REGEX)
  }


class HttpHeadersDict(validation.ValidatedDict):
  """A dict that limits keys and values what http_headers allows.

  http_headers is an static handler key i.e. it applies to handlers with
  static_dir or static_files keys. An example of how http_headers is used is

  handlers:
  - url: /static
    static_dir: static
    http_headers:
      X-Foo-Header: foo value
      X-Bar-Header: bar value
  """


  DISALLOWED_HEADERS = frozenset([




      'content-encoding',
      'content-length',
      'date',
      'server'
  ])

  MAX_HEADER_LENGTH = 500
  MAX_HEADER_VALUE_LENGTHS = {
      'set-cookie': _MAX_COOKIE_LENGTH,
      'set-cookie2': _MAX_COOKIE_LENGTH,
      'location': _MAX_URL_LENGTH}
  MAX_LEN = 500

  class KeyValidator(validation.Validator):
    """Ensures that keys in HttpHeadersDict i.e. header names are valid.

    An instance is used as HttpHeadersDict's KEY_VALIDATOR.
    """

    def Validate(self, name, unused_key=None):
      """Returns argument, or raises an exception if it is invalid.

      HTTP header names are defined by RFC 2616 section 4.2.

      Args:
        name: HTTP header field value.
        unused_key: Unused.

      Returns:
        name argument, unchanged.

      Raises:
        appinfo_errors.InvalidHttpHeaderName: argument cannot be used as an HTTP
          header name.
      """
      original_name = name


      if isinstance(name, unicode):
        try:
          name = name.encode('ascii')
        except UnicodeEncodeError:
          raise appinfo_errors.InvalidHttpHeaderName(
              'HTTP header values must not contain non-ASCII data')


      name = name.lower()

      if not _HTTP_TOKEN_RE.match(name):
        raise appinfo_errors.InvalidHttpHeaderName(
            'An HTTP header must be a non-empty RFC 2616 token.')


      if name in _HTTP_REQUEST_HEADERS:
        raise appinfo_errors.InvalidHttpHeaderName(
            '%r can only be used in HTTP requests, not responses.'
            % original_name)


      if name.startswith('x-appengine'):
        raise appinfo_errors.InvalidHttpHeaderName(
            'HTTP header names that begin with X-Appengine are reserved.')

      if wsgiref.util.is_hop_by_hop(name):
        raise appinfo_errors.InvalidHttpHeaderName(
            'Only use end-to-end headers may be used. See RFC 2616 section'
            ' 13.5.1.')

      if name in HttpHeadersDict.DISALLOWED_HEADERS:
        raise appinfo_errors.InvalidHttpHeaderName(
            '%s is a disallowed header.' % name)

      return original_name

  class ValueValidator(validation.Validator):
    """Ensures that values in HttpHeadersDict i.e. header values are valid.

    An instance is used as HttpHeadersDict's VALUE_VALIDATOR.
    """

    def Validate(self, value, key=None):
      """Returns value, or raises an exception if it is invalid.

      According to RFC 2616 section 4.2, header field values must consist "of
      either *TEXT or combinations of token, separators, and quoted-string".

      TEXT = <any OCTET except CTLs, but including LWS>

      Args:
        value: HTTP header field value.
        key: HTTP header field name.

      Returns:
        value argument.

      Raises:
        appinfo_errors.InvalidHttpHeaderValue: argument cannot be used as an
          HTTP header value.
      """

      if isinstance(value, unicode):
        try:
          value = value.encode('ascii')
        except UnicodeEncodeError:
          raise appinfo_errors.InvalidHttpHeaderValue(
              'HTTP header values must not contain non-ASCII data')


      key = key.lower()





      printable = set(string.printable[:-5])
      if not all(char in printable for char in value):
        raise appinfo_errors.InvalidHttpHeaderValue(
            'HTTP header field values must consist of printable characters.')

      HttpHeadersDict.ValueValidator.AssertHeaderNotTooLong(key, value)

      return value

    @staticmethod
    def AssertHeaderNotTooLong(name, value):
      header_length = len('%s: %s\r\n' % (name, value))



      if header_length >= HttpHeadersDict.MAX_HEADER_LENGTH:



        try:
          max_len = HttpHeadersDict.MAX_HEADER_VALUE_LENGTHS[name]
        except KeyError:
          raise appinfo_errors.InvalidHttpHeaderValue(
              'HTTP header (name + value) is too long.')



        if len(value) > max_len:
          insert = name, len(value), max_len
          raise appinfo_errors.InvalidHttpHeaderValue(
              '%r header value has length %d, which exceed the maximum allowed,'
              ' %d.' % insert)

  KEY_VALIDATOR = KeyValidator()
  VALUE_VALIDATOR = ValueValidator()

  def Get(self, header_name):
    """Gets a header value.

    Args:
      header_name: HTTP header name to look for.

    Returns:
      A header value that corresponds to header_name. If more than one such
      value is in self, one of the values is selected arbitrarily, and
      returned. The selection is not deterministic.
    """
    for name in self:
      if name.lower() == header_name.lower():
        return self[name]



  def __setitem__(self, key, value):
    is_addition = self.Get(key) is None
    if is_addition and len(self) >= self.MAX_LEN:
      raise appinfo_errors.TooManyHttpHeaders(
          'Tried to add another header when the current set of HTTP headers'
          ' already has the maximum allowed number of headers, %d.'
          % HttpHeadersDict.MAX_LEN)
    super(HttpHeadersDict, self).__setitem__(key, value)


class URLMap(HandlerBase):
  """Mapping from URLs to handlers.

  This class acts like something of a union type.  Its purpose is to
  describe a mapping between a set of URLs and their handlers.  What
  handler type a given instance has is determined by which handler-id
  attribute is used.

  Each mapping can have one and only one handler type.  Attempting to
  use more than one handler-id attribute will cause an UnknownHandlerType
  to be raised during validation.  Failure to provide any handler-id
  attributes will cause MissingHandlerType to be raised during validation.

  The regular expression used by the url field will be used to match against
  the entire URL path and query string of the request.  This means that
  partial maps will not be matched.  Specifying a url, say /admin, is the
  same as matching against the regular expression '^/admin$'.  Don't begin
  your matching url with ^ or end them with $.  These regular expressions
  won't be accepted and will raise ValueError.

  Attributes:
    login: Whether or not login is required to access URL.  Defaults to
      'optional'.
    secure: Restriction on the protocol which can be used to serve
            this URL/handler (HTTP, HTTPS or either).
    url: Regular expression used to fully match against the request URLs path.
      See Special Cases for using static_dir.
    static_files: Handler id attribute that maps URL to the appropriate
      file.  Can use back regex references to the string matched to url.
    upload: Regular expression used by the application configuration
      program to know which files are uploaded as blobs.  It's very
      difficult to determine this using just the url and static_files
      so this attribute must be included.  Required when defining a
      static_files mapping.
      A matching file name must fully match against the upload regex, similar
      to how url is matched against the request path.  Do not begin upload
      with ^ or end it with $.
    static_dir: Handler id that maps the provided url to a sub-directory
      within the application directory.  See Special Cases.
    mime_type: When used with static_files and static_dir the mime-type
      of files served from those directories are overridden with this
      value.
    script: Handler id that maps URLs to scipt handler within the application
      directory that will run using CGI.
    position: Used in AppInclude objects to specify whether a handler
      should be inserted at the beginning of the primary handler list or at the
      end.  If 'tail' is specified, the handler is inserted at the end,
      otherwise, the handler is inserted at the beginning.  This means that
      'head' is the effective default.
    expiration: When used with static files and directories, the time delta to
      use for cache expiration. Has the form '4d 5h 30m 15s', where each letter
      signifies days, hours, minutes, and seconds, respectively. The 's' for
      seconds may be omitted. Only one amount must be specified, combining
      multiple amounts is optional. Example good values: '10', '1d 6h',
      '1h 30m', '7d 7d 7d', '5m 30'.
    api_endpoint: Handler id that identifies endpoint as an API endpoint,
      calls that terminate here will be handled by the api serving framework.

  Special cases:
    When defining a static_dir handler, do not use a regular expression
    in the url attribute.  Both the url and static_dir attributes are
    automatically mapped to these equivalents:

      <url>/(.*)
      <static_dir>/\1

    For example:

      url: /images
      static_dir: images_folder

    Is the same as this static_files declaration:

      url: /images/(.*)
      static_files: images_folder/\1
      upload: images_folder/(.*)
  """
  ATTRIBUTES = {


      HANDLER_STATIC_FILES: validation.Optional(_FILES_REGEX),
      UPLOAD: validation.Optional(_FILES_REGEX),


      HANDLER_STATIC_DIR: validation.Optional(_FILES_REGEX),


      MIME_TYPE: validation.Optional(str),
      EXPIRATION: validation.Optional(_EXPIRATION_REGEX),
      REQUIRE_MATCHING_FILE: validation.Optional(bool),
      HTTP_HEADERS: validation.Optional(HttpHeadersDict),


      POSITION: validation.Optional(validation.Options(POSITION_HEAD,
                                                       POSITION_TAIL)),


      HANDLER_API_ENDPOINT: validation.Optional(validation.Options(
          (ON, ON_ALIASES),
          (OFF, OFF_ALIASES))),

  }
  ATTRIBUTES.update(HandlerBase.ATTRIBUTES)

  COMMON_FIELDS = set([URL, LOGIN, AUTH_FAIL_ACTION, SECURE])



  ALLOWED_FIELDS = {
      HANDLER_STATIC_FILES: (MIME_TYPE, UPLOAD, EXPIRATION,
                             REQUIRE_MATCHING_FILE, HTTP_HEADERS),
      HANDLER_STATIC_DIR: (MIME_TYPE, EXPIRATION, REQUIRE_MATCHING_FILE,
                           HTTP_HEADERS),
      HANDLER_SCRIPT: (POSITION),
      HANDLER_API_ENDPOINT: (POSITION, SCRIPT),
  }

  def GetHandler(self):
    """Get handler for mapping.

    Returns:
      Value of the handler (determined by handler id attribute).
    """
    return getattr(self, self.GetHandlerType())

  def GetHandlerType(self):
    """Get handler type of mapping.

    Returns:
      Handler type determined by which handler id attribute is set.

    Raises:
      UnknownHandlerType: when none of the no handler id attributes are set.

      UnexpectedHandlerAttribute: when an unexpected attribute is set for the
        discovered handler type.

      HandlerTypeMissingAttribute: when the handler is missing a
        required attribute for its handler type.
    """


    if getattr(self, HANDLER_API_ENDPOINT) is not None:

      mapping_type = HANDLER_API_ENDPOINT
    else:
      for id_field in URLMap.ALLOWED_FIELDS.iterkeys():

        if getattr(self, id_field) is not None:

          mapping_type = id_field
          break
      else:

        raise appinfo_errors.UnknownHandlerType(
            'Unknown url handler type.\n%s' % str(self))

    allowed_fields = URLMap.ALLOWED_FIELDS[mapping_type]



    for attribute in self.ATTRIBUTES.iterkeys():
      if (getattr(self, attribute) is not None and
          not (attribute in allowed_fields or
               attribute in URLMap.COMMON_FIELDS or
               attribute == mapping_type)):
        raise appinfo_errors.UnexpectedHandlerAttribute(
            'Unexpected attribute "%s" for mapping type %s.' %
            (attribute, mapping_type))




    if mapping_type == HANDLER_STATIC_FILES and not self.upload:
      raise appinfo_errors.MissingHandlerAttribute(
          'Missing "%s" attribute for URL "%s".' % (UPLOAD, self.url))

    return mapping_type

  def CheckInitialized(self):
    """Adds additional checking to make sure handler has correct fields.

    In addition to normal ValidatedCheck calls GetHandlerType
    which validates all the handler fields are configured
    properly.

    Raises:
      UnknownHandlerType: when none of the no handler id attributes are set.
      UnexpectedHandlerAttribute: when an unexpected attribute is set for the
        discovered handler type.
      HandlerTypeMissingAttribute: when the handler is missing a required
        attribute for its handler type.
      ContentTypeSpecifiedMultipleTimes: when mime_type is inconsistent with
        http_headers.
    """
    super(URLMap, self).CheckInitialized()
    if self.GetHandlerType() in (STATIC_DIR, STATIC_FILES):











      self.AssertUniqueContentType()

  def AssertUniqueContentType(self):
    """Makes sure that self.http_headers is consistent with self.mime_type.

    Assumes self is a static handler i.e. either self.static_dir or
    self.static_files is set (to not None).

    Raises:
      appinfo_errors.ContentTypeSpecifiedMultipleTimes: Raised when
        self.http_headers contains a Content-Type header, and self.mime_type is
        set. For example, the following configuration would be rejected:

          handlers:
          - url: /static
            static_dir: static
            mime_type: text/html
            http_headers:
              content-type: text/html

        As this example shows, a configuration will be rejected when
        http_headers and mime_type specify a content type, even when they
        specify the same content type.
    """
    used_both_fields = self.mime_type and self.http_headers
    if not used_both_fields:
      return

    content_type = self.http_headers.Get('Content-Type')
    if content_type is not None:
      raise appinfo_errors.ContentTypeSpecifiedMultipleTimes(
          'http_header specified a Content-Type header of %r in a handler that'
          ' also specified a mime_type of %r.' % (content_type, self.mime_type))

  def FixSecureDefaults(self):
    """Force omitted 'secure: ...' handler fields to 'secure: optional'.

    The effect is that handler.secure is never equal to the (nominal)
    default.

    See http://b/issue?id=2073962.
    """
    if self.secure == SECURE_DEFAULT:
      self.secure = SECURE_HTTP_OR_HTTPS

  def WarnReservedURLs(self):
    """Generates a warning for reserved URLs.

    See:
    https://developers.google.com/appengine/docs/python/config/appconfig#Reserved_URLs
    """
    if self.url == '/form':
      logging.warning(
          'The URL path "/form" is reserved and will not be matched.')

  def ErrorOnPositionForAppInfo(self):
    """Raises an error if position is specified outside of AppInclude objects.
    """
    if self.position:
      raise appinfo_errors.PositionUsedInAppYamlHandler(
          'The position attribute was specified for this handler, but this is '
          'an app.yaml file.  Position attribute is only valid for '
          'include.yaml files.')


class AdminConsolePage(validation.Validated):
  """Class representing admin console page in AdminConsole object.
  """
  ATTRIBUTES = {
      URL: _URL_REGEX,
      NAME: _PAGE_NAME_REGEX,
  }


class AdminConsole(validation.Validated):
  """Class representing admin console directives in application info.
  """
  ATTRIBUTES = {
      PAGES: validation.Optional(validation.Repeated(AdminConsolePage)),
  }

  @classmethod
  def Merge(cls, adminconsole_one, adminconsole_two):
    """Return the result of merging two AdminConsole objects."""








    if not adminconsole_one or not adminconsole_two:
      return adminconsole_one or adminconsole_two

    if adminconsole_one.pages:
      if adminconsole_two.pages:
        adminconsole_one.pages.extend(adminconsole_two.pages)
    else:
      adminconsole_one.pages = adminconsole_two.pages

    return adminconsole_one


class ErrorHandlers(validation.Validated):
  """Class representing error handler directives in application info.
  """
  ATTRIBUTES = {
      ERROR_CODE: validation.Optional(_ERROR_CODE_REGEX),
      FILE: _FILES_REGEX,
      MIME_TYPE: validation.Optional(str),
  }


class BuiltinHandler(validation.Validated):
  """Class representing builtin handler directives in application info.

  Permits arbitrary keys but their values must be described by the
  validation.Options object returned by ATTRIBUTES.
  """






































  class DynamicAttributes(dict):
    """Provide a dictionary object that will always claim to have a key.

    This dictionary returns a fixed value for any get operation.  The fixed
    value passed in as a constructor parameter should be a
    validation.Validated object.
    """

    def __init__(self, return_value, **parameters):
      self.__return_value = return_value
      dict.__init__(self, parameters)

    def __contains__(self, _):
      return True

    def __getitem__(self, _):
      return self.__return_value

  ATTRIBUTES = DynamicAttributes(
      validation.Optional(validation.Options((ON, ON_ALIASES),
                                             (OFF, OFF_ALIASES))))

  def __init__(self, **attributes):
    """Ensure that all BuiltinHandler objects at least have attribute 'default'.
    """
    self.ATTRIBUTES.clear()
    self.builtin_name = ''
    super(BuiltinHandler, self).__init__(**attributes)

  def __setattr__(self, key, value):
    """Permit ATTRIBUTES.iteritems() to return set of items that have values.

    Whenever validate calls iteritems(), it is always called on ATTRIBUTES,
    not on __dict__, so this override is important to ensure that functions
    such as ToYAML() return the correct set of keys.
    """
    if key == 'builtin_name':
      object.__setattr__(self, key, value)
    elif not self.builtin_name:
      self.ATTRIBUTES[key] = ''
      self.builtin_name = key
      super(BuiltinHandler, self).__setattr__(key, value)
    else:




      raise appinfo_errors.MultipleBuiltinsSpecified(
          'More than one builtin defined in list element.  Each new builtin '
          'should be prefixed by "-".')

  def ToDict(self):
    """Convert BuiltinHander object to a dictionary.

    Returns:
      dictionary of the form: {builtin_handler_name: on/off}
    """
    return {self.builtin_name: getattr(self, self.builtin_name)}

  @classmethod
  def IsDefined(cls, builtins_list, builtin_name):
    """Find if a builtin is defined in a given list of builtin handler objects.

    Args:
      builtins_list: list of BuiltinHandler objects (typically yaml.builtins)
      builtin_name: name of builtin to find whether or not it is defined

    Returns:
      true if builtin_name is defined by a member of builtins_list,
      false otherwise
    """
    for b in builtins_list:
      if b.builtin_name == builtin_name:
        return True
    return False

  @classmethod
  def ListToTuples(cls, builtins_list):
    """Converts a list of BuiltinHandler objects to a list of (name, status)."""
    return [(b.builtin_name, getattr(b, b.builtin_name)) for b in builtins_list]

  @classmethod
  def Validate(cls, builtins_list, runtime=None):
    """Verify that all BuiltinHandler objects are valid and not repeated.

    Args:
      builtins_list: list of BuiltinHandler objects to validate.
      runtime: if set then warnings are generated for builtins that have been
          deprecated in the given runtime.

    Raises:
      InvalidBuiltinFormat if the name of a Builtinhandler object
          cannot be determined.
      DuplicateBuiltinSpecified if a builtin handler name is used
          more than once in the list.
    """
    seen = set()
    for b in builtins_list:
      if not b.builtin_name:
        raise appinfo_errors.InvalidBuiltinFormat(
            'Name of builtin for list object %s could not be determined.'
            % b)
      if b.builtin_name in seen:
        raise appinfo_errors.DuplicateBuiltinsSpecified(
            'Builtin %s was specified more than once in one yaml file.'
            % b.builtin_name)






      if b.builtin_name == 'datastore_admin' and runtime == 'python':
        logging.warning(
            'The datastore_admin builtin is deprecated. You can find '
            'information on how to enable it through the Administrative '
            'Console here: '
            'http://developers.google.com/appengine/docs/adminconsole/'
            'datastoreadmin.html')
      elif b.builtin_name == 'mapreduce' and runtime == 'python':
        logging.warning(
            'The mapreduce builtin is deprecated. You can find more '
            'information on how to configure and use it here: '
            'http://developers.google.com/appengine/docs/python/dataprocessing/'
            'overview.html')

      seen.add(b.builtin_name)


class ApiConfigHandler(HandlerBase):
  """Class representing api_config handler directives in application info."""
  ATTRIBUTES = HandlerBase.ATTRIBUTES
  ATTRIBUTES.update({

      URL: validation.Regex(_URL_REGEX),
      HANDLER_SCRIPT: validation.Regex(_FILES_REGEX)
  })


class Library(validation.Validated):
  """Class representing the configuration of a single library."""

  ATTRIBUTES = {'name': validation.Type(str),
                'version': validation.Type(str)}

  def CheckInitialized(self):
    """Raises if the library configuration is not valid."""
    super(Library, self).CheckInitialized()
    if self.name not in _NAME_TO_SUPPORTED_LIBRARY:
      raise appinfo_errors.InvalidLibraryName(
          'the library "%s" is not supported' % self.name)

    supported_library = _NAME_TO_SUPPORTED_LIBRARY[self.name]
    if self.version != 'latest':
      if self.version not in supported_library.supported_versions:
        raise appinfo_errors.InvalidLibraryVersion(
            ('%s version "%s" is not supported, ' + _USE_VERSION_FORMAT) % (
                self.name,
                self.version,
                '", "'.join(supported_library.non_deprecated_versions)))
      elif self.version in supported_library.deprecated_versions:
        logging.warning(
            ('%s version "%s" is deprecated, ' + _USE_VERSION_FORMAT) % (
                self.name,
                self.version,
                '", "'.join(supported_library.non_deprecated_versions)))


class AutomaticScaling(validation.Validated):
  """Class representing automatic scaling settings in the AppInfoExternal."""
  ATTRIBUTES = {
      MINIMUM_IDLE_INSTANCES: validation.Optional(_IDLE_INSTANCES_REGEX),
      MAXIMUM_IDLE_INSTANCES: validation.Optional(_IDLE_INSTANCES_REGEX),
      MINIMUM_PENDING_LATENCY: validation.Optional(_PENDING_LATENCY_REGEX),
      MAXIMUM_PENDING_LATENCY: validation.Optional(_PENDING_LATENCY_REGEX),
  }


class ManualScaling(validation.Validated):
  """Class representing manual scaling settings in the AppInfoExternal."""
  ATTRIBUTES = {
      INSTANCES: validation.Regex(_INSTANCES_REGEX),
  }


class BasicScaling(validation.Validated):
  """Class representing basic scaling settings in the AppInfoExternal."""
  ATTRIBUTES = {
      MAX_INSTANCES: validation.Regex(_INSTANCES_REGEX),
      IDLE_TIMEOUT: validation.Optional(_IDLE_TIMEOUT_REGEX),
  }


class VmSettings(validation.ValidatedDict):
  """Class for VM settings.

  We don't validate these further because the feature is in flux.
  """

  KEY_VALIDATOR = validation.Regex('[a-zA-Z_][a-zA-Z0-9_]*')
  VALUE_VALIDATOR = str


class EnvironmentVariables(validation.ValidatedDict):
  """Class representing a mapping of environment variable key value pairs."""

  KEY_VALIDATOR = validation.Regex('[a-zA-Z_][a-zA-Z0-9_]*')
  VALUE_VALIDATOR = str


class AppInclude(validation.Validated):
  """Class representing the contents of an included app.yaml file.

  Used for both builtins and includes directives.
  """

  ATTRIBUTES = {
      BUILTINS: validation.Optional(validation.Repeated(BuiltinHandler)),
      INCLUDES: validation.Optional(validation.Type(list)),
      HANDLERS: validation.Optional(validation.Repeated(URLMap)),
      ADMIN_CONSOLE: validation.Optional(AdminConsole),




  }

  @classmethod
  def MergeAppYamlAppInclude(cls, appyaml, appinclude):
    """This function merges an app.yaml file with referenced builtins/includes.
    """




    if not appinclude:
      return appyaml


    if appinclude.handlers:
      tail = appyaml.handlers or []
      appyaml.handlers = []

      for h in appinclude.handlers:
        if not h.position or h.position == 'head':
          appyaml.handlers.append(h)
        else:
          tail.append(h)



        h.position = None

      appyaml.handlers.extend(tail)


    appyaml.admin_console = AdminConsole.Merge(appyaml.admin_console,
                                               appinclude.admin_console)

    return appyaml

  @classmethod
  def MergeAppIncludes(cls, appinclude_one, appinclude_two):
    """This function merges the non-referential state of the provided AppInclude
    objects.  That is, builtins and includes directives are not preserved, but
    any static objects are copied into an aggregate AppInclude object that
    preserves the directives of both provided AppInclude objects.

    Args:
      appinclude_one: object one to merge
      appinclude_two: object two to merge

    Returns:
      AppInclude object that is the result of merging the static directives of
      appinclude_one and appinclude_two.
    """



    if not appinclude_one or not appinclude_two:
      return appinclude_one or appinclude_two


    if appinclude_one.handlers:
      if appinclude_two.handlers:
        appinclude_one.handlers.extend(appinclude_two.handlers)
    else:
      appinclude_one.handlers = appinclude_two.handlers


    appinclude_one.admin_console = (
        AdminConsole.Merge(appinclude_one.admin_console,
                           appinclude_two.admin_console))

    return appinclude_one


class AppInfoExternal(validation.Validated):
  """Class representing users application info.

  This class is passed to a yaml_object builder to provide the validation
  for the application information file format parser.

  Attributes:
    application: Unique identifier for application.
    version: Application's major version.
    runtime: Runtime used by application.
    api_version: Which version of APIs to use.
    source_language: Optional specification of the source language.
      For example we specify "php-quercus" if this is a Java app
      that was generated from PHP source using Quercus
    handlers: List of URL handlers.
    default_expiration: Default time delta to use for cache expiration for
      all static files, unless they have their own specific 'expiration' set.
      See the URLMap.expiration field's documentation for more information.
    skip_files: An re object.  Files that match this regular expression will
      not be uploaded by appcfg.py.  For example:
        skip_files: |
          .svn.*|
          #.*#
    nobuild_files: An re object.  Files that match this regular expression will
      not be built into the app.  Go only.
    api_config: URL root and script/servlet path for enhanced api serving
  """

  ATTRIBUTES = {


      APPLICATION: APPLICATION_RE_STRING,
      SERVER: validation.Optional(SERVER_ID_RE_STRING),
      VERSION: validation.Optional(SERVER_VERSION_ID_RE_STRING),
      RUNTIME: RUNTIME_RE_STRING,


      API_VERSION: API_VERSION_RE_STRING,
      INSTANCE_CLASS: validation.Optional(_INSTANCE_CLASS_REGEX),
      SOURCE_LANGUAGE: validation.Optional(
          validation.Regex(SOURCE_LANGUAGE_RE_STRING)),
      AUTOMATIC_SCALING: validation.Optional(AutomaticScaling),
      MANUAL_SCALING: validation.Optional(ManualScaling),
      BASIC_SCALING: validation.Optional(BasicScaling),
      VM_SETTINGS: validation.Optional(VmSettings),
      BUILTINS: validation.Optional(validation.Repeated(BuiltinHandler)),
      INCLUDES: validation.Optional(validation.Type(list)),
      HANDLERS: validation.Optional(validation.Repeated(URLMap)),
      LIBRARIES: validation.Optional(validation.Repeated(Library)),

      SERVICES: validation.Optional(validation.Repeated(
          validation.Regex(_SERVICE_RE_STRING))),
      DEFAULT_EXPIRATION: validation.Optional(_EXPIRATION_REGEX),
      SKIP_FILES: validation.RegexStr(default=DEFAULT_SKIP_FILES),
      NOBUILD_FILES: validation.RegexStr(default=DEFAULT_NOBUILD_FILES),
      DERIVED_FILE_TYPE: validation.Optional(validation.Repeated(
          validation.Options(JAVA_PRECOMPILED, PYTHON_PRECOMPILED))),
      ADMIN_CONSOLE: validation.Optional(AdminConsole),
      ERROR_HANDLERS: validation.Optional(validation.Repeated(ErrorHandlers)),
      BACKENDS: validation.Optional(validation.Repeated(
          backendinfo.BackendEntry)),
      THREADSAFE: validation.Optional(bool),
      API_CONFIG: validation.Optional(ApiConfigHandler),
      CODE_LOCK: validation.Optional(bool),
      ENV_VARIABLES: validation.Optional(EnvironmentVariables),
      PAGESPEED: validation.Optional(pagespeedinfo.PagespeedEntry),
  }





  _skip_runtime_checks = False

  def CheckInitialized(self):
    """Performs non-regex-based validation.

    The following are verified:
      - At least one url mapping is provided in the URL mappers.
      - Number of url mappers doesn't exceed MAX_URL_MAPS.
      - Major version does not contain the string -dot-.
      - If api_endpoints are defined, an api_config stanza must be defined.
      - If the runtime is python27 and threadsafe is set, then no CGI handlers
        can be used.
      - That the version name doesn't start with BUILTIN_NAME_PREFIX

    Raises:
      DuplicateLibrary: if the name library name is specified more than once.
      MissingURLMapping: if no URLMap object is present in the object.
      TooManyURLMappings: if there are too many URLMap entries.
      MissingApiConfig: if api_endpoints exist without an api_config.
      MissingThreadsafe: if threadsafe is not set but the runtime requires it.
      ThreadsafeWithCgiHandler: if the runtime is python27, threadsafe is set
          and CGI handlers are specified.
      TooManyScalingSettingsError: if more than one scaling settings block is
          present.
    """
    super(AppInfoExternal, self).CheckInitialized()
    if not self.handlers and not self.builtins and not self.includes:
      raise appinfo_errors.MissingURLMapping(
          'No URLMap entries found in application configuration')
    if self.handlers and len(self.handlers) > MAX_URL_MAPS:
      raise appinfo_errors.TooManyURLMappings(
          'Found more than %d URLMap entries in application configuration' %
          MAX_URL_MAPS)

    if (self.threadsafe is None and
        self.runtime == 'python27' and
        not self._skip_runtime_checks):
      raise appinfo_errors.MissingThreadsafe(
          'threadsafe must be present and set to either "yes" or "no"')

    if self.libraries:
      if self.runtime != 'python27' and not self._skip_runtime_checks:
        raise appinfo_errors.RuntimeDoesNotSupportLibraries(
            'libraries entries are only supported by the "python27" runtime')

      library_names = [library.name for library in self.libraries]
      for library_name in library_names:
        if library_names.count(library_name) > 1:
          raise appinfo_errors.DuplicateLibrary(
              'Duplicate library entry for %s' % library_name)

    if self.version and self.version.find(ALTERNATE_HOSTNAME_SEPARATOR) != -1:
      raise validation.ValidationError(
          'Version "%s" cannot contain the string "%s"' % (
              self.version, ALTERNATE_HOSTNAME_SEPARATOR))
    if self.version and self.version.startswith(BUILTIN_NAME_PREFIX):
      raise validation.ValidationError(
          ('Version "%s" cannot start with "%s" because it is a '
           'reserved version name prefix.') % (self.version,
                                               BUILTIN_NAME_PREFIX))
    if self.handlers:
      api_endpoints = [handler.url for handler in self.handlers
                       if handler.GetHandlerType() == HANDLER_API_ENDPOINT]
      if api_endpoints and not self.api_config:
        raise appinfo_errors.MissingApiConfig(
            'An api_endpoint handler was specified, but the required '
            'api_config stanza was not configured.')
      if (self.threadsafe and
          self.runtime == 'python27' and
          not self._skip_runtime_checks):
        for handler in self.handlers:
          if (handler.script and (handler.script.endswith('.py') or
                                  '/' in handler.script)):
            raise appinfo_errors.ThreadsafeWithCgiHandler(
                'threadsafe cannot be enabled with CGI handler: %s' %
                handler.script)
    if sum([bool(self.automatic_scaling),
            bool(self.manual_scaling),
            bool(self.basic_scaling)]) > 1:
      raise appinfo_errors.TooManyScalingSettingsError(
          "There may be only one of 'automatic_scaling', 'manual_scaling', "
          "or 'basic_scaling'.")


  def GetAllLibraries(self):
    """Returns a list of all Library instances active for this configuration.

    Returns:
      The list of active Library instances for this configuration. This includes
      directly-specified libraries as well as any required dependencies.
    """
    if not self.libraries:
      return []

    library_names = set(library.name for library in self.libraries)
    required_libraries = []

    for library in self.libraries:
      for required_name, required_version in REQUIRED_LIBRARIES.get(
          (library.name, library.version), []):
        if required_name not in library_names:
          required_libraries.append(Library(name=required_name,
                                            version=required_version))

    return self.libraries + required_libraries

  def GetNormalizedLibraries(self):
    """Returns a list of normalized Library instances for this configuration.

    Returns:
      The list of active Library instances for this configuration. This includes
      directly-specified libraries, their required dependencies as well as any
      libraries enabled by default. Any libraries with "latest" as their version
      will be replaced with the latest available version.
    """
    libraries = self.GetAllLibraries()
    enabled_libraries = set(library.name for library in libraries)
    for library in _SUPPORTED_LIBRARIES:
      if library.default_version and library.name not in enabled_libraries:
        libraries.append(Library(name=library.name,
                                 version=library.default_version))
    for library in libraries:
      if library.version == 'latest':
        library.version = _NAME_TO_SUPPORTED_LIBRARY[
            library.name].supported_versions[-1]
    return libraries

  def ApplyBackendSettings(self, backend_name):
    """Applies settings from the indicated backend to the AppInfoExternal.

    Backend entries may contain directives that modify other parts of the
    app.yaml, such as the 'start' directive, which adds a handler for the start
    request.  This method performs those modifications.

    Args:
      backend_name: The name of a backend defined in 'backends'.

    Raises:
      BackendNotFound: If the indicated backend was not listed in 'backends'.
    """
    if backend_name is None:
      return

    if self.backends is None:
      raise appinfo_errors.BackendNotFound

    self.version = backend_name

    match = None
    for backend in self.backends:
      if backend.name != backend_name:
        continue
      if match:
        raise appinfo_errors.DuplicateBackend
      else:
        match = backend

    if match is None:
      raise appinfo_errors.BackendNotFound

    if match.start is None:
      return

    start_handler = URLMap(url=_START_PATH, script=match.start)
    self.handlers.insert(0, start_handler)


def ValidateHandlers(handlers, is_include_file=False):
  """Validates a list of handler (URLMap) objects.

  Args:
    handlers: A list of a handler (URLMap) objects.
    is_include_file: If true, indicates the we are performing validation
      for handlers in an AppInclude file, which may contain special directives.
  """
  if not handlers:
    return

  for handler in handlers:
    handler.FixSecureDefaults()
    handler.WarnReservedURLs()
    if not is_include_file:
      handler.ErrorOnPositionForAppInfo()


def LoadSingleAppInfo(app_info):
  """Load a single AppInfo object where one and only one is expected.

  Args:
    app_info: A file-like object or string.  If it is a string, parse it as
    a configuration file.  If it is a file-like object, read in data and
    parse.

  Returns:
    An instance of AppInfoExternal as loaded from a YAML file.

  Raises:
    ValueError: if a specified service is not valid.
    EmptyConfigurationFile: when there are no documents in YAML file.
    MultipleConfigurationFile: when there is more than one document in YAML
    file.
  """
  builder = yaml_object.ObjectBuilder(AppInfoExternal)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(app_info)

  app_infos = handler.GetResults()
  if len(app_infos) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(app_infos) > 1:
    raise appinfo_errors.MultipleConfigurationFile()

  appyaml = app_infos[0]
  ValidateHandlers(appyaml.handlers)
  if appyaml.builtins:
    BuiltinHandler.Validate(appyaml.builtins, appyaml.runtime)

  return appyaml


class AppInfoSummary(validation.Validated):
  """This class contains only basic summary information about an app.

  It is used to pass back information about the newly created app to users
  after a new version has been created.
  """





  ATTRIBUTES = {
      APPLICATION: APPLICATION_RE_STRING,
      MAJOR_VERSION: SERVER_VERSION_ID_RE_STRING,
      MINOR_VERSION: validation.TYPE_LONG
  }


def LoadAppInclude(app_include):
  """Load a single AppInclude object where one and only one is expected.

  Args:
    app_include: A file-like object or string.  If it is a string, parse it as
    a configuration file.  If it is a file-like object, read in data and
    parse.

  Returns:
    An instance of AppInclude as loaded from a YAML file.

  Raises:
    EmptyConfigurationFile: when there are no documents in YAML file.
    MultipleConfigurationFile: when there is more than one document in YAML
    file.
  """
  builder = yaml_object.ObjectBuilder(AppInclude)
  handler = yaml_builder.BuilderHandler(builder)
  listener = yaml_listener.EventListener(handler)
  listener.Parse(app_include)

  includes = handler.GetResults()
  if len(includes) < 1:
    raise appinfo_errors.EmptyConfigurationFile()
  if len(includes) > 1:
    raise appinfo_errors.MultipleConfigurationFile()

  includeyaml = includes[0]
  if includeyaml.handlers:
    for handler in includeyaml.handlers:
      handler.FixSecureDefaults()
      handler.WarnReservedURLs()
  if includeyaml.builtins:
    BuiltinHandler.Validate(includeyaml.builtins)

  return includeyaml


def ParseExpiration(expiration):
  """Parses an expiration delta string.

  Args:
    expiration: String that matches _DELTA_REGEX.

  Returns:
    Time delta in seconds.
  """
  delta = 0
  for match in re.finditer(_DELTA_REGEX, expiration):
    amount = int(match.group(1))
    units = _EXPIRATION_CONVERSIONS.get(match.group(2).lower(), 1)
    delta += amount * units
  return delta






_file_path_positive_re = re.compile(r'^[ 0-9a-zA-Z\._\+/\$-]{1,256}$')


_file_path_negative_1_re = re.compile(r'\.\.|^\./|\.$|/\./|^-|^_ah/')


_file_path_negative_2_re = re.compile(r'//|/$')



_file_path_negative_3_re = re.compile(r'^ | $|/ | /')


def ValidFilename(filename):
  """Determines if filename is valid.

  filename must be a valid pathname.
  - It must contain only letters, numbers, _, +, /, $, ., and -.
  - It must be less than 256 chars.
  - It must not contain "/./", "/../", or "//".
  - It must not end in "/".
  - All spaces must be in the middle of a directory or file name.

  Args:
    filename: The filename to validate.

  Returns:
    An error string if the filename is invalid.  Returns '' if the filename
    is valid.
  """
  if _file_path_positive_re.match(filename) is None:
    return 'Invalid character in filename: %s' % filename
  if _file_path_negative_1_re.search(filename) is not None:
    return ('Filename cannot contain "." or ".." '
            'or start with "-" or "_ah/": %s' %
            filename)
  if _file_path_negative_2_re.search(filename) is not None:
    return 'Filename cannot have trailing / or contain //: %s' % filename
  if _file_path_negative_3_re.search(filename) is not None:
    return 'Any spaces must be in the middle of a filename: %s' % filename
  return ''
