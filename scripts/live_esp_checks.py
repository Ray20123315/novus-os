"""Checks for boot-stage payloads unique to the live ESP image."""


def check_live_esp_payloads(fat, check):
    """Report missing or empty live-only payloads using check(condition, message)."""
    for path in ('ESP.IMG', 'TEST.NKM'):
        content = fat.read_file(path)
        check(content is not None and len(content) > 0,
              'esp.img: missing or empty %s' % path)
