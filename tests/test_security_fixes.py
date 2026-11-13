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


def test_admin_cannot_cross_tenant_boundary():
    from orderflow.access import Principal, can_view_order, visible_orders
    admin = Principal(1, "admin", tenant_id=1)
    own_tenant = {"owner_id": 5, "tenant_id": 1}
    other_tenant = {"owner_id": 5, "tenant_id": 2}
    assert can_view_order(admin, own_tenant)
    assert not can_view_order(admin, other_tenant)
    assert visible_orders(admin, [own_tenant, other_tenant]) == [own_tenant]


def test_owner_cannot_read_record_of_other_tenant():
    from orderflow.access import Principal, can_view_order
    user = Principal(4, "user", tenant_id=1)
    assert not can_view_order(user, {"owner_id": 4, "tenant_id": 2})
