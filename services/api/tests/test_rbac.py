from store_api.auth import build_capability_set, can_perform


def test_tenant_owner_has_settings_access():
    capabilities = build_capability_set(["tenant_owner"])

    assert "settings.manage" in capabilities
    assert "refund.approve" in capabilities


def test_cashier_cannot_transfer_inventory():
    assert can_perform(["cashier"], "inventory.transfer") is False


def test_platform_super_admin_bypasses_regular_scope_limits():
    assert can_perform(["platform_super_admin"], "staff.manage") is True
