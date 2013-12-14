#-----------------------------------------------------------------------------
#  Copyright (C) 2013 The IPython Development Team
#
#  Distributed under the terms of the BSD License.  The full license is in
#  the file COPYING, distributed as part of this software.
#-----------------------------------------------------------------------------

import json
from tornado.web import StaticFileHandler
from tornado.log import access_log

def log_request(handler):
    """log a bit more information about each request than tornado's default
    
    - move static file get success to debug-level (reduces noise)
    - get proxied IP instead of proxy IP
    - log referer for redirect and failed requests
    - log user-agent for failed requests
    """
    status = handler.get_status()
    request = handler.request
    if status < 300 or status == 304 and isinstance(handler, StaticFileHandler):
        # static-file get successes (or 304 FOUND) are debug-level
        log_method = access_log.debug
    elif status < 400:
        log_method = access_log.info
    elif status < 500:
        log_method = access_log.warning
    else:
        log_method = access_log.error
    
    # If behind a proxy, get the true requester's address
    if 'X-Forwarded-For' in request.headers:
        remote_ip = request.headers['X-Forwarded-For'].split(',')[0].strip()
    else:
        remote_ip = request.remote_ip
    request_time = 1000.0 * handler.request.request_time()
    ns = dict(
        status=status,
        method=request.method,
        ip=remote_ip,
        uri=request.uri,
        request_time=request_time,
    )
    msg = "{status} {method} {uri} ({ip}) {request_time:.2f}ms"
    if status >= 300:
        # log referers on redirects
        ns['referer'] = request.headers.get('Referer', 'None')
        msg = msg + ' referer={referer}'
    if status >= 400:
        # log user agent for failed requests
        ns['agent'] = request.headers.get('User-Agent', 'Unknown')
        msg = msg + ' user-agent={agent}'
    if status >= 500 and status != 502:
        # log all headers if it caused an error
        log_method(json.dumps(request.headers, indent=2))
    log_method(msg.format(**ns))

