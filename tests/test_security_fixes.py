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


def test_preferences_cannot_change_role_or_status():
    import pytest
    from orderflow.accounts import Account, update_preferences
    account = Account(7, "user@example.test", "user")
    with pytest.raises(PermissionError):
        update_preferences(account, {"role": "admin", "active": True})
    assert account.role == "user"
    update_preferences(account, {"preferred_currency": "EUR"})
    assert account.preferred_currency == "EUR"


def test_api_key_comparison_is_exact():
    from orderflow.accounts import verify_api_key
    assert verify_api_key("k-123", "k-123")
    assert not verify_api_key(" k-123 ", "k-123")
    assert not verify_api_key("", "")
    assert not verify_api_key("k-124", "k-123")


def test_audit_log_redacts_sensitive_fields(caplog):
    import logging
    from orderflow.audit import record_operation
    with caplog.at_level(logging.INFO, logger="orderflow.audit"):
        event = record_operation("admin", "user.update",
                                 {"user_id": 7, "password": "p@ss", "api_token": "t-1",
                                  "contact": {"email": "a@test.local"}})
    logged = caplog.text
    assert "p@ss" not in logged and "t-1" not in logged and "a@test.local" not in logged
    assert '"user_id": 7' in logged
    assert event["attributes"]["password"] == "p@ss"


def _request(handler_cls, path):
    import io
    handler = handler_cls.__new__(handler_cls)
    handler.path = path
    handler.request_version = "HTTP/1.1"
    handler.requestline = "GET " + path + " HTTP/1.1"
    handler.command = "GET"
    handler.wfile = io.BytesIO()
    handler.log_message = lambda *args: None
    handler.do_GET()
    return handler.wfile.getvalue().decode("utf-8")


def test_response_has_no_implementation_banner():
    import json
    from orderflow.web import Handler
    raw = _request(Handler, "/health")
    headers, body = raw.split("\r\n\r\n", 1)
    assert "X-Powered-By" not in headers
    assert json.loads(body) == {"status": "ok"}
