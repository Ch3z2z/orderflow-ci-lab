from orderflow.access import safe_return_url
from orderflow.notifications import webhook_destination_allowed


def test_return_url_requires_exact_host():
    assert safe_return_url("https://shop.example/orders", "shop.example")
    assert not safe_return_url("https://evilshop.example/orders", "shop.example")
    assert not safe_return_url("https://shop.example.attacker.test/", "shop.example")
    assert not safe_return_url("//evil.test/path", "shop.example")


def test_webhook_domain_boundary():
    approved = {"partner.example"}
    assert webhook_destination_allowed("https://partner.example/hook", approved)
    assert webhook_destination_allowed("https://api.partner.example/hook", approved)
    assert not webhook_destination_allowed("https://evilpartner.example/hook", approved)
    assert not webhook_destination_allowed("http://partner.example/hook", approved)
