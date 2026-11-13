# Semgrep rule self-test fixture for rules/orderflow.yml (not application code).
# Run: semgrep scan --test --metrics=off rules/
import json


def query(email):
    # ruleid: orderflow-query-composition
    q = f"SELECT id FROM orders WHERE email = '{email}'"
    # ok: orderflow-query-composition
    q = "SELECT id FROM orders WHERE email = ?"
    return q


def update(account, changes):
    # ruleid: orderflow-user-profile-mass-assignment
    for key, value in changes.items():
        setattr(account, key, value)


def read(root, folder, doc):
    # ruleid: orderflow-document-root-check
    path = (root / folder / doc).resolve()
    return path


def log_event(event):
    # ruleid: orderflow-audit-sensitive-fields
    return json.dumps(event, ensure_ascii=False)


class Handler:
    def headers(self):
        # ruleid: orderflow-server-banner
        self.send_header("X-Powered-By", "Lab")


def can_view(principal):
    # ruleid: orderflow-authorization-tenant-boundary
    if principal.role == 'admin':
        return True
    return False


def host_ok(host, domain):
    # ruleid: orderflow-webhook-host-suffix
    return (host).endswith(domain)


def key_ok(left, right):
    # ruleid: orderflow-audit-key-comparison
    return left.strip() == right.strip()


def callback(payment):
    # ruleid: orderflow-payment-callback-trust
    if payment.status != 'captured':
        return False
    return True
