import requests
from urllib.parse import unquote, urlparse, urlunparse
from flask import abort, request, current_app

from ..models import Setting


def forward_request():
    pdns_api_url = Setting().get('pdns_api_url')
    pdns_api_key = Setting().get('pdns_api_key')
    headers = {}
    data = None

    msg_str = "Sending request to powerdns API {0}"

    if request.method != 'GET' and request.method != 'DELETE':
        msg = msg_str.format(request.get_json(force=True, silent=True))
        current_app.logger.debug(msg)
        data = request.get_json(force=True, silent=True)

    verify = False

    headers = {
        'user-agent': 'powerdns-admin/api',
        'pragma': 'no-cache',
        'cache-control': 'no-cache',
        'accept': 'application/json; q=1',
        'X-API-KEY': pdns_api_key
    }

    # url = urljoin(pdns_api_url, request.full_path)

    parsed_base = urlparse(pdns_api_url)
    base_path = parsed_base.path.rstrip('/')
    request_path = request.path.lstrip('/')
    # Reject rather than resolve: requests collapses '..' after authorization
    # has been decided on the route's zone_id.
    if any(seg in ('.', '..') for seg in unquote(request_path).split('/')):
        abort(400)
    target_path = f"{base_path}/{request_path}" if request_path else (base_path or '/')
    query = request.query_string.decode('utf-8') if request.query_string else ''
    url = urlunparse((
        parsed_base.scheme,
        parsed_base.netloc,
        target_path,
        '',
        query,
        ''
    ))

    resp = requests.request(request.method,
                            url,
                            headers=headers,
                            verify=verify,
                            json=data)

    return resp
