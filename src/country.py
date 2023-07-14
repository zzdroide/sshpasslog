from ip3country import CountryLookup

lookup = CountryLookup()

def ip2country(ip: str):
    # TODO: check for TOR ips
    # (from https://check.torproject.org/torbulkexitlist)
    # and return country "XT".
    # XT code is available for custom purposes (https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2#XT)

    return lookup.lookupStr(ip) or '--'
