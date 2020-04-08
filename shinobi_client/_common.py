from requests import Response


def raise_if_errors(shinobi_response: Response, raise_if_json_not_ok: bool = True):
    """
    Raises an exception if the response from Shinobi indicated there were errors.
    :param shinobi_response: the response from Shinobi
    :param raise_if_json_not_ok: raise an exception if Shinobi returns a 2XX but the JSON has `"ok": false`
    """
    shinobi_response.raise_for_status()
    json_response = shinobi_response.json()
    if raise_if_json_not_ok and not json_response["ok"]:
        # Yes, the API returns a 2XX when everything is not ok...
        raise RuntimeError(json_response["msg"])
